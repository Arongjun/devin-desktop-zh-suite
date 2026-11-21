# Devin Desktop 简体中文增强包 —— Windows 安装脚本
param(
    [string]$AssetsDir = "",
    [string]$AppDir = "",
    [switch]$NoRules
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$utf8 = New-Object System.Text.UTF8Encoding($false)
$pkg = Split-Path $PSScriptRoot -Parent

function Find-Assets {
    if ($AssetsDir -and (Test-Path $AssetsDir)) { return (Resolve-Path $AssetsDir).Path }
    if ($AppDir -and (Test-Path $AppDir)) {
        $c = Join-Path $AppDir 'resources\app\out\vs\workbench\devin-webapp-host\assets'
        if (Test-Path $c) { return (Resolve-Path $c).Path }
    }
    foreach ($c in @(
        'E:\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets',
        "$env:LOCALAPPDATA\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets",
        "$env:ProgramFiles\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets",
        'D:\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets',
        'C:\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets'
    )) { if (Test-Path $c) { return (Resolve-Path $c).Path } }

    $proc = Get-CimInstance Win32_Process -Filter "Name='Devin.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ExecutablePath -like '*\Devin.exe' } | Select-Object -First 1
    if ($proc) {
        $c = Join-Path (Split-Path $proc.ExecutablePath) 'resources\app\out\vs\workbench\devin-webapp-host\assets'
        if (Test-Path $c) { return (Resolve-Path $c).Path }
    }
    foreach ($rk in 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
                    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
                    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*') {
        foreach ($h in (Get-ItemProperty $rk -ErrorAction SilentlyContinue |
                 Where-Object { $_.DisplayName -match 'Devin' })) {
            $base = $h.InstallLocation
            if (-not $base -and $h.DisplayIcon) { $base = Split-Path ($h.DisplayIcon -replace '"','') }
            if ($base) {
                $c = Join-Path $base 'resources\app\out\vs\workbench\devin-webapp-host\assets'
                if (Test-Path $c) { return (Resolve-Path $c).Path }
            }
        }
    }
    throw '找不到 Devin assets 目录，请用 -AssetsDir 指定'
}

function Save-Text($path, $text) {
    try { [IO.File]::WriteAllText($path, $text, $utf8) }
    catch [IO.IOException] { throw "写入失败（文件被占用？请先退出 Devin）：$path" }
}

$assets = Find-Assets
$outDir = (Resolve-Path (Join-Path $assets '..\..\..\..')).Path
Write-Host "[*] assets: $assets"
Write-Host "[*] out   : $outDir"

# ---------- 1. 语言 chunk ----------
foreach ($f in 'zh-CN-translation.js', 'zh-CN-review.js') {
    Copy-Item (Join-Path $pkg "assets\$f") (Join-Path $assets $f) -Force
    Write-Host "[+] 已安装 $f"
}

# ---------- 2. NLS 内核（仅词条数一致才替换） ----------
foreach ($pair in @(@('nls.messages.json','nls.messages.zh.json'),
                    @('nls.messages.js','nls.messages.zh.js'))) {
    $dst = Join-Path $outDir $pair[0]
    $src = Join-Path $pkg "assets\$($pair[1])"
    if (-not (Test-Path $dst)) { Write-Host "[=] 跳过 $($pair[0])（不存在）"; continue }
    if ((Get-Content $dst -Raw).Contains('关闭对话框')) { Write-Host "[=] $($pair[0]) 已是中文"; continue }
    try {
        $curCount = @(Get-Content $dst -Raw | ConvertFrom-Json).Count
        $zhCount  = @(Get-Content $src -Raw | ConvertFrom-Json).Count
    } catch { Write-Host "[=] NLS 词条统计失败，跳过"; continue }
    if ($curCount -ne $zhCount) {
        Write-Host "[=] NLS 词条数不匹配（本机 $curCount / 补丁 $zhCount），跳过以避免文案错位"
        continue
    }
    if (-not (Test-Path "$dst.zhorig")) { Copy-Item $dst "$dst.zhorig" }
    Copy-Item $src $dst -Force
    Write-Host "[+] 已汉化 $($pair[0])（$curCount 条）"
}

# ---------- 3. 菜单 bundle ----------
$menu = Get-ChildItem $assets -File |
        Where-Object { $_.Name -match '(chunk-)?entry-host-editor-mode-menu-.*\.js$' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $menu) { throw '找不到 editor-mode-menu bundle' }
$s = Get-Content $menu.FullName -Raw
if ($s -match 'code:`zh`') {
    Write-Host "[=] 语言列表已含 zh，跳过菜单补丁"
} else {
    if (-not (Test-Path "$($menu.FullName).zhorig")) { Copy-Item $menu.FullName "$($menu.FullName).zhorig" }
    $mdep = [regex]::Match($s, 'm\.f=\[([^\]]*)\]')
    if (-not $mdep.Success) { throw '未找到 m.f 依赖表，版本可能已变化' }
    $depIdx = ([regex]::Matches($mdep.Groups[1].Value, '"[^"]*"')).Count
    $s = $s.Substring(0, $mdep.Index) +
         'm.f=[' + $mdep.Groups[1].Value + ',"./zh-CN-translation.js","./zh-CN-review.js"]' +
         $s.Substring($mdep.Index + $mdep.Length)

    $ment = [regex]::Match($s, ',(\{code:`[^`]+`,label:`[^`]+`,translation:[^{}]*\})\]')
    if (-not $ment.Success) { throw '未找到语言列表，版本可能已变化' }
    $entry = $ment.Groups[1].Value
    $zh = $entry -replace 'code:`[^`]+`', 'code:`zh`' -replace 'label:`[^`]+`', 'label:`中文(简体)`'
    $files = './zh-CN-translation.js', './zh-CN-review.js'
    $script:i = 0; $script:j = 0; $script:depIdx = $depIdx
    $zh = [regex]::Replace($zh, 'import\(`\./[^`]+`\)', [System.Text.RegularExpressions.MatchEvaluator]{
        param($m); $f = $files[$script:i]; $script:i++; 'import(`' + $f + '`)'
    })
    $zh = [regex]::Replace($zh, '__vite__mapDeps\(\[\d+', [System.Text.RegularExpressions.MatchEvaluator]{
        param($m); $k = $script:depIdx + $script:j; $script:j++; '__vite__mapDeps([' + $k
    })
    $at = $ment.Index + $ment.Length - 1
    $s = $s.Substring(0, $at) + ',' + $zh + $s.Substring($at)
    Save-Text $menu.FullName $s
    Write-Host "[+] 语言列表已注册 zh（依赖索引 $depIdx / $($depIdx+1)）"
}

# ---------- 4. 语言持久化 ----------
$api = Get-ChildItem $assets -File |
       Where-Object { $_.Name -match '(entry-host-index|chunk-app-initial|chunk-entry-host-index).*\.js$' } |
       ForEach-Object { if ((Get-Content $_.FullName -Raw) -match 'users/ui-language') { $_ } } |
       Select-Object -First 1
if (-not $api) { throw '找不到 ui-language API bundle，版本可能已变化' }
$s2 = Get-Content $api.FullName -Raw
if ($s2 -match 'localStorage\.getItem\(`devin-language`\)===`zh`') {
    Write-Host "[=] ui-language 本地回退已存在"
} else {
    $dirty = $false

    # 新版（斜杠路径 + body）：chunk-app-initial
    $p = 'async function (\w+)\((\w+),(\w+)\)\{return (\w+)\(\2\)\.PUT\(`/users/ui-language`,\{body:\{language:\3\}\}\)\}'
    if ($s2 -match $p) {
        $s2 = [regex]::Replace($s2, $p,
            'async function $1($2,$3){return $3===`zh`?Promise.resolve({ui_language:`zh`}):$4($2).PUT(`/users/ui-language`,{body:{language:$3}})}')
        $dirty = $true; Write-Host '[+] PUT：zh 跳过云端保存（新版结构）'
    }
    $p = 'async function (\w+)\((\w+),(\w+)\)\{return (\w+)\(\2\)\.GET\(`/users/ui-language`,\{signal:\3\}\)\}'
    if ($s2 -match $p) {
        $s2 = [regex]::Replace($s2, $p,
            'async function $1($2,$3){try{if(localStorage.getItem(`devin-language`)===`zh`)return{ui_language:`zh`}}catch{}return $4($2).GET(`/users/ui-language`,{signal:$3})}')
        $dirty = $true; Write-Host '[+] GET：zh 优先读 localStorage（新版结构）'
    }

    # 旧版（无斜杠路径 + json）：entry-host-index
    $p = '([A-Za-z_$][\w$]*)\.put\(`users/ui-language`,\{json:\{language:([A-Za-z_$][\w$]*)\}\}\)(\.json\(\))?'
    if ($s2 -match $p) {
        $s2 = [regex]::Replace($s2, $p, [System.Text.RegularExpressions.MatchEvaluator]{
            param($m)
            $c = $m.Groups[1].Value; $v = $m.Groups[2].Value; $j = $m.Groups[3].Value
            '(' + $v + '===`zh`?Promise.resolve({ui_language:' + $v + '}):' +
            $c + '.put(`users/ui-language`,{json:{language:' + $v + '}})' + $j + ')'
        })
        $dirty = $true; Write-Host '[+] PUT：zh 跳过云端保存（旧版结构）'
    }
    $p = '([A-Za-z_$][\w$]*)\.get\(`users/ui-language`,\{signal:([A-Za-z_$][\w$]*)\}\)(\.json\(\))?'
    if ($s2 -match $p) {
        $s2 = [regex]::Replace($s2, $p, [System.Text.RegularExpressions.MatchEvaluator]{
            param($m)
            $c = $m.Groups[1].Value; $v = $m.Groups[2].Value; $j = $m.Groups[3].Value
            '(()=>{try{if(localStorage.getItem(`devin-language`)===`zh`)return{ui_language:`zh`}}catch{}return ' +
            $c + '.get(`users/ui-language`,{signal:' + $v + '})' + $j + '})()'
        })
        $dirty = $true; Write-Host '[+] GET：zh 优先读 localStorage（旧版结构）'
    }
    if (-not $dirty) { throw '未识别 ui-language API 结构，版本可能已变化' }
    if (-not (Test-Path "$($api.FullName).zhorig")) { Copy-Item $api.FullName "$($api.FullName).zhorig" }
    Save-Text $api.FullName $s2
}

# ---------- 5. 中文思考规则 ----------
if (-not $NoRules) {
    $tpl = Join-Path $pkg 'rules\chinese-thinking-v2.md'
    $raw = Get-Content $tpl -Raw -Encoding UTF8
    $front = ''
    if ($raw -match '(?s)^---\s*\r?\n.*?\r?\n---\s*\r?\n') {
        $front = $matches[0]; $body = $raw.Substring($matches[0].Length)
    } else { $body = $raw }
    $block = "<!-- devin-zh-kit:rules-begin -->`r`n" + $body.Trim() + "`r`n<!-- devin-zh-kit:rules-end -->`r`n"
    $stamp = Get-Date -Format 'yyyyMMddHHmmss'
    $home = $env:USERPROFILE
    $targets = @(
        @{ Path = "$home\.devin\rules\chinese-thinking.md"; Standalone = $true },
        @{ Path = "$env:APPDATA\devin\AGENTS.md"; Standalone = $false },
        @{ Path = "$home\.codeium\windsurf\memories\global_rules.md"; Standalone = $false }
    )
    foreach ($t in $targets) {
        $p = $t.Path
        if (-not $p) { continue }
        if (Test-Path $p) {
            $old = Get-Content $p -Raw
            if ($old.Contains('<!-- devin-zh-kit:rules-begin -->')) { Write-Host "[=] 规则已存在：$p"; continue }
            Copy-Item $p "$p.bak-$stamp"
        } else { $old = '' }
        $dir = Split-Path $p
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $content = if ($t.Standalone -and -not $old.Trim()) { $front + $block } else { $old.TrimEnd() + "`r`n`r`n" + $block }
        [IO.File]::WriteAllText($p, $content, $utf8)
        Write-Host "[+] 已写入规则：$p"
    }
}

# ---------- 6. 校验 ----------
$ok = $true
if ((Get-Content $menu.FullName -Raw) -notmatch 'code:`zh`') { $ok = $false; Write-Host '[!] 校验失败：语言列表无 zh' }
if ((Get-Content $api.FullName -Raw) -notmatch 'localStorage\.getItem\(`devin-language`\)===`zh`') { $ok = $false; Write-Host '[!] 校验失败：localStorage 回退缺失' }
foreach ($f in 'zh-CN-translation.js', 'zh-CN-review.js') {
    if (-not (Test-Path (Join-Path $assets $f))) { $ok = $false; Write-Host "[!] 校验失败：缺 $f" }
}
if ($ok) {
    Write-Host ''
    Write-Host '==== 汉化完成 ===='
    Write-Host '请完全退出 Devin 后重新打开，执行 Configure Display Language，选择 中文(简体)。'
    Write-Host '中文思考规则已写入用户目录，新开会话生效。'
} else { Write-Host '==== 存在失败项 ====' }
