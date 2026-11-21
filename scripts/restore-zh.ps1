# Devin Desktop 简体中文增强包 —— Windows 还原脚本
param([string]$AssetsDir = "", [switch]$RemoveRules)
$ErrorActionPreference = 'Stop'
$pkg = Split-Path $PSScriptRoot -Parent

if ($AssetsDir -and (Test-Path $AssetsDir)) {
    $assets = (Resolve-Path $AssetsDir).Path
} else {
    $guess = "$env:LOCALAPPDATA\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets"
    if (Test-Path $guess) { $assets = $guess } else {
        $proc = Get-CimInstance Win32_Process -Filter "Name='Devin.exe'" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($proc -and $proc.ExecutablePath) {
            $assets = Join-Path (Split-Path $proc.ExecutablePath) 'resources\app\out\vs\workbench\devin-webapp-host\assets'
        } else { throw '找不到 assets 目录，请用 -AssetsDir 指定' }
    }
}
$outDir = (Resolve-Path (Join-Path $assets '..\..\..\..')).Path
Write-Host "[*] assets: $assets"

$count = 0
foreach ($dir in @($assets, $outDir)) {
    Get-ChildItem $dir -File | ForEach-Object {
        $bak = "$($_.FullName).zhorig"
        if (Test-Path $bak) {
            Copy-Item $bak $_.FullName -Force
            Remove-Item $bak
            Write-Host "[+] 已还原 $($_.Name)"
            $script:count++
        }
    }
}
foreach ($f in 'zh-CN-translation.js', 'zh-CN-review.js') {
    $p = Join-Path $assets $f
    if (Test-Path $p) { Remove-Item $p; Write-Host "[+] 已删除 $f"; $count++ }
}
Write-Host "[=] 共还原 $count 项"

if ($RemoveRules) {
    foreach ($p in @("$env:USERPROFILE\.devin\rules\chinese-thinking.md",
                     "$env:APPDATA\devin\AGENTS.md",
                     "$env:USERPROFILE\.codeium\windsurf\memories\global_rules.md")) {
        if (-not (Test-Path $p)) { continue }
        $s = Get-Content $p -Raw
        $begin = '<!-- devin-zh-kit:rules-begin -->'
        $end = '<!-- devin-zh-kit:rules-end -->'
        if (-not ($s.Contains($begin) -and $s.Contains($end))) { continue }
        $i = $s.IndexOf($begin); $j = $s.IndexOf($end) + $end.Length
        $new = ($s.Substring(0, $i) + $s.Substring($j)).Trim() + "`r`n"
        Copy-Item $p "$p.bak-remove"
        [IO.File]::WriteAllText($p, $new, (New-Object System.Text.UTF8Encoding($false)))
        Write-Host "[+] 已移除规则块 $p"
    }
}
Write-Host "`n还原完成。请完全退出 Devin 后重新打开。"
