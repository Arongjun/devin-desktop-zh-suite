#!/usr/bin/env python3
"""Devin Desktop 简体中文增强包 —— 跨平台核心脚本。

支持 Windows / macOS / Linux。子命令：
    apply    应用界面汉化 + 中文思考规则（默认）
    restore  还原原文件（可选同时移除规则）
    rules    单独管理中文思考规则
    doctor   只读检查当前状态

所有修改均先备份为 *.zhorig（界面文件）或 *.bak-<时间戳>（规则文件）。
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"
RULES_DIR = ROOT / "rules"
RULES_TEMPLATE = RULES_DIR / "chinese-thinking-v2.md"

RULES_BEGIN = "<!-- devin-zh-kit:rules-begin -->"
RULES_END = "<!-- devin-zh-kit:rules-end -->"

M_F_RE = re.compile(r"m\.f=\[([^\]]*)\]")
LANG_RE = re.compile(r",(\{code:`[^`]+`,label:`[^`]+`,translation:[^{}]*\})\]")
IMPORT_RE = re.compile(r"import\(`\./[^`]+`\)")
MAP_RE = re.compile(r"__vite__mapDeps\(\[\d+")

PUT_WIN = re.compile(
    r"([A-Za-z_$][\w$]*)\.put\(`users/ui-language`,\{json:\{language:([A-Za-z_$][\w$]*)\}\}\)(\.json\(\))?"
)
GET_WIN = re.compile(
    r"([A-Za-z_$][\w$]*)\.get\(`users/ui-language`,\{signal:([A-Za-z_$][\w$]*)\}\)(\.json\(\))?"
)
PUT_NEW = re.compile(
    r"async function (\w+)\((\w+),(\w+)\)\{return (\w+)\(\2\)\.PUT\(`/users/ui-language`,\{body:\{language:\3\}\}\)\}"
)
GET_NEW = re.compile(
    r"async function (\w+)\((\w+),(\w+)\)\{return (\w+)\(\2\)\.GET\(`/users/ui-language`,\{signal:\3\}\)\}"
)


def say(tag: str, msg: str) -> None:
    print(f"[{tag}] {msg}")


def is_win() -> bool:
    return platform.system().lower() == "windows"


def is_mac() -> bool:
    return platform.system().lower() == "darwin"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_backup(path: Path, text: str) -> None:
    bak = Path(str(path) + ".zhorig")
    if not bak.exists():
        shutil.copy2(path, bak)
        say("备份", str(bak))
    path.write_text(text, encoding="utf-8")


def exactly_one(pattern: re.Pattern, text: str, label: str) -> re.Match:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{label}: 期望 1 处匹配，实际 {len(matches)} 处（版本可能已变化）")
    return matches[0]


# ---------------------------------------------------------------- 定位

def find_app(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_dir():
            raise SystemExit(f"指定的 Devin 目录不存在: {p}")
        return p

    if is_mac():
        candidates = [Path("/Applications/Devin.app"), Path.home() / "Applications/Devin.app"]
    elif is_win():
        candidates = []
        for env in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            if os.environ.get(env):
                candidates.append(Path(os.environ[env]) / "Programs" / "Devin")
                candidates.append(Path(os.environ[env]) / "Devin")
        candidates += [Path(p) for p in ("C:\\Devin", "D:\\Devin", "E:\\Devin")]
        # 从运行中的进程反推
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter \"Name='Devin.exe'\").ExecutablePath"],
                stderr=subprocess.DEVNULL, text=True, timeout=10,
            )
            for line in out.splitlines():
                if line.strip().lower().endswith("devin.exe"):
                    candidates.insert(0, Path(line.strip()).parent)
        except Exception:
            pass
    else:
        candidates = [Path.home() / "Devin", Path("/opt/Devin")]

    for c in candidates:
        if c.is_dir():
            return c
    raise SystemExit("找不到 Devin 安装目录，请用 --app-dir 指定")


def find_assets(app: Path) -> Path:
    for rel in ("resources/app/out/vs/workbench/devin-webapp-host/assets",
                "Contents/Resources/app/out/vs/workbench/devin-webapp-host/assets"):
        p = app / rel
        if p.is_dir():
            return p
    hits = list(app.glob("**/devin-webapp-host/assets"))
    if len(hits) == 1:
        return hits[0]
    raise SystemExit("找不到 devin-webapp-host/assets 目录，请用 --assets-dir 指定")


def find_out(assets: Path) -> Path:
    return assets.parent.parent.parent.parent


def find_menu(assets: Path) -> Path:
    files = sorted(assets.glob("*entry-host-editor-mode-menu-*.js"))
    if not files:
        raise SystemExit("找不到 editor-mode-menu bundle")
    return max(files, key=lambda p: p.stat().st_mtime)


def find_api_files(assets: Path) -> list[Path]:
    names = ["*entry-host-index-*.js", "*app-initial-*.js"]
    files: list[Path] = []
    for n in names:
        files += list(assets.glob(n))
    hits = [p for p in files if "users/ui-language" in read(p)]
    if not hits:
        hits = [p for p in assets.glob("*.js") if "users/ui-language" in read(p)]
    return hits


# ---------------------------------------------------------------- 界面补丁

def apply_chunks(assets: Path) -> None:
    for name in ("zh-CN-translation.js", "zh-CN-review.js"):
        src = ASSET_DIR / name
        if not src.is_file():
            raise SystemExit(f"补丁包缺少 {name}")
        shutil.copy2(src, assets / name)
        say("已安装", name)


def patch_menu(assets: Path) -> None:
    path = find_menu(assets)
    s = read(path)
    if "code:`zh`" in s:
        say("跳过", f"{path.name} 已含 zh")
        return

    mdep = exactly_one(M_F_RE, s, "m.f 依赖表")
    dep_idx = len(re.findall(r'"[^"]*"', mdep.group(1)))
    ment = exactly_one(LANG_RE, s, "语言列表末项")
    entry = ment.group(1)

    zh = re.sub(r"code:`[^`]+`", "code:`zh`", entry, count=1)
    zh = re.sub(r"label:`[^`]+`", "label:`中文(简体)`", zh, count=1)

    files = iter(["./zh-CN-translation.js", "./zh-CN-review.js"])
    zh, n_imp = IMPORT_RE.subn(lambda m: "import(`" + next(files) + "`)", zh)
    if n_imp != 2:
        raise RuntimeError(f"zh 语言项 import 数量异常: {n_imp}")

    counter = [0]
    def dep_repl(m: re.Match) -> str:
        k = dep_idx + counter[0]
        counter[0] += 1
        return "__vite__mapDeps([" + str(k)
    zh, n_dep = MAP_RE.subn(dep_repl, zh)
    if n_dep != 2:
        raise RuntimeError(f"zh 语言项 mapDeps 数量异常: {n_dep}")

    s = s[:mdep.start()] + "m.f=[" + mdep.group(1) + \
        ',"./zh-CN-translation.js","./zh-CN-review.js"]' + s[mdep.end():]
    ment = exactly_one(LANG_RE, s, "语言列表末项(二次)")
    at = ment.end() - 1
    s = s[:at] + "," + zh + s[at:]
    write_backup(path, s)
    say("已修改", f"{path.name} 注册 中文(简体)（依赖索引 {dep_idx}/{dep_idx+1}）")


def patch_language_api(assets: Path) -> None:
    files = find_api_files(assets)
    if len(files) != 1:
        raise SystemExit(f"期望 1 个包含 ui-language API 的 bundle，实际 {len(files)} 个: {files}")
    path = files[0]
    s = read(path)
    if "localStorage.getItem(`devin-language`)===`zh`" in s:
        say("跳过", f"{path.name} 已含 zh 本地回退")
        return

    changed = False

    def put_win(m: re.Match) -> str:
        nonlocal changed
        changed = True
        c, v, j = m.group(1), m.group(2), m.group(3) or ""
        return (f"({v}===`zh`?Promise.resolve({{ui_language:{v}}}):"
                f"{c}.put(`users/ui-language`,{{json:{{language:{v}}}}}){j})")

    def get_win(m: re.Match) -> str:
        nonlocal changed
        changed = True
        c, v, j = m.group(1), m.group(2), m.group(3) or ""
        return ("(()=>{try{if(localStorage.getItem(`devin-language`)===`zh`)"
                f"return{{ui_language:`zh`}}}}catch{{}}return {c}.get(`users/ui-language`,"
                f"{{signal:{v}}}{j})()")

    s2 = PUT_WIN.sub(put_win, s)
    s2 = GET_WIN.sub(get_win, s2)

    def put_new(m: re.Match) -> str:
        nonlocal changed
        changed = True
        fn, a, b, cli = m.groups()
        return (f"async function {fn}({a},{b}){{return {b}===`zh`?"
                f"Promise.resolve({{ui_language:`zh`}}):"
                f"{cli}({a}).PUT(`/users/ui-language`,{{body:{{language:{b}}}}})}}")

    def get_new(m: re.Match) -> str:
        nonlocal changed
        changed = True
        fn, a, b, cli = m.groups()
        return (f"async function {fn}({a},{b}){{try{{if(localStorage.getItem(`devin-language`)===`zh`)"
                f"return{{ui_language:`zh`}}}}catch{{}}return {cli}({a}).GET(`/users/ui-language`,"
                f"{{signal:{b}}})}}")

    s2 = PUT_NEW.sub(put_new, s2)
    s2 = GET_NEW.sub(get_new, s2)

    if not changed:
        raise RuntimeError(f"{path.name} 未识别 ui-language API 结构，版本可能已变化")
    write_backup(path, s2)
    say("已修改", f"{path.name} zh 语言走 localStorage")


def patch_nls(out: Path) -> None:
    dst_json = out / "nls.messages.json"
    dst_js = out / "nls.messages.js"
    if not dst_json.is_file():
        say("跳过", "未找到 nls.messages.json")
        return
    try:
        current = len(json.loads(read(dst_json)))
        supplied = len(json.loads(read(ASSET_DIR / "nls.messages.zh.json")))
    except Exception as e:
        say("跳过", f"NLS 词条统计失败: {e}")
        return
    if current != supplied:
        say("跳过", f"NLS 词条数不匹配（本机 {current} / 补丁 {supplied}），强行替换会导致文案错位")
        say("建议", "通过官方 VS Code 简体中文语言包获得菜单/命令面板中文，见 README")
        return
    if "关闭对话框" in read(dst_json):
        say("跳过", "nls.messages.json 已是中文")
        return
    for name in ("nls.messages.json", "nls.messages.js"):
        src = ASSET_DIR / ("nls.messages.zh." + name.split(".")[-1])
        dst = out / name
        if dst.is_file() and src.is_file():
            write_backup(dst, read(src))
            say("已汉化", name)


def sign_mac(app: Path) -> None:
    if not is_mac():
        return
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
        ent = Path(f.name)
    try:
        with ent.open("wb") as f:
            subprocess.run(["codesign", "-d", "--entitlements", ":-", str(app)],
                           check=True, stdout=f, stderr=subprocess.DEVNULL)
        subprocess.run(["codesign", "-f", "-s", "-", "--entitlements", str(ent), str(app)],
                       check=True, stdout=subprocess.DEVNULL)
        say("已签名", f"{app} (ad-hoc)")
    finally:
        ent.unlink(missing_ok=True)


# ---------------------------------------------------------------- 规则

def rule_targets() -> list[tuple[Path, bool]]:
    """返回 (目标文件, 是否为独立规则文件)。"""
    if is_win():
        home = Path(os.environ.get("USERPROFILE", str(Path.home())))
        appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        return [
            (home / ".devin" / "rules" / "chinese-thinking.md", True),
            (appdata / "devin" / "AGENTS.md", False),
            (home / ".codeium" / "windsurf" / "memories" / "global_rules.md", False),
        ]
    return [
        (Path.home() / ".devin" / "rules" / "chinese-thinking.md", True),
        (Path.home() / ".config" / "devin" / "AGENTS.md", False),
        (Path.home() / ".codeium" / "windsurf" / "memories" / "global_rules.md", False),
    ]


def rule_parts() -> tuple[str, str]:
    text = read(RULES_TEMPLATE)
    front = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            front = text[:end + 4].strip() + "\n\n"
            text = text[end + 4:].lstrip("\n")
    return front, text.strip()


def install_rules() -> None:
    front, body = rule_parts()
    block = f"{RULES_BEGIN}\n{body}\n{RULES_END}\n"
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    for path, standalone in rule_targets():
        if path.is_file() and RULES_BEGIN in read(path):
            say("跳过", f"规则已存在: {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        old = read(path) if path.is_file() else ""
        if old.strip():
            shutil.copy2(path, Path(str(path) + f".bak-{stamp}"))
            say("备份", f"{path}.bak-{stamp}")
        content = (front + block) if (standalone and not old.strip()) else (old.rstrip() + "\n\n" + block)
        path.write_text(content, encoding="utf-8")
        say("已写入", str(path))


def remove_rules() -> None:
    for path, _ in rule_targets():
        if not path.is_file():
            continue
        s = read(path)
        if RULES_BEGIN not in s or RULES_END not in s:
            continue
        start, end = s.find(RULES_BEGIN), s.find(RULES_END) + len(RULES_END)
        s = (s[:start] + s[end:]).strip() + "\n"
        shutil.copy2(path, Path(str(path) + ".bak-remove"))
        path.write_text(s, encoding="utf-8")
        say("已移除规则块", str(path))


def doctor_rules() -> None:
    for path, _ in rule_targets():
        state = "已安装" if path.is_file() and RULES_BEGIN in read(path) else \
                ("存在但未托管" if path.is_file() else "未安装")
        say(state, str(path))


# ---------------------------------------------------------------- 还原

def restore_ui(app: Path, assets: Path) -> None:
    targets = [assets, find_out(assets)]
    count = 0
    for base in targets:
        for path in list(base.glob("*.js")) + list(base.glob("*.json")):
            bak = Path(str(path) + ".zhorig")
            if bak.is_file():
                shutil.copy2(bak, path)
                bak.unlink()
                say("已还原", str(path))
                count += 1
    for name in ("zh-CN-translation.js", "zh-CN-review.js"):
        p = assets / name
        if p.is_file():
            p.unlink()
            say("已删除", str(p))
            count += 1
    say("完成", f"还原 {count} 项")
    sign_mac(app)


def doctor(app: Path, assets: Path, out: Path) -> None:
    say("平台", platform.platform())
    say("Devin 目录", str(app))
    say("assets", str(assets))
    menu = find_menu(assets)
    say("菜单 bundle", f"{menu.name}: {'已汉化' if 'code:`zh`' in read(menu) else '未汉化'}")
    api = find_api_files(assets)
    say("语言 API", ", ".join(p.name for p in api) or "未找到")
    if api:
        s = read(api[0])
        say("语言回退", "已启用" if "localStorage.getItem(`devin-language`)===`zh`" in s else "未启用")
    dj = out / "nls.messages.json"
    if dj.is_file():
        try:
            say("NLS 词条", f"{len(json.loads(read(dj)))} 条")
        except Exception:
            say("NLS 词条", "无法解析")
    doctor_rules()


# ---------------------------------------------------------------- CLI

def main() -> None:
    parser = argparse.ArgumentParser(description="Devin Desktop 简体中文增强包")
    parser.add_argument("cmd", nargs="?", default="apply", choices=["apply", "restore", "rules", "doctor"])
    parser.add_argument("rule_action_pos", nargs="?", choices=["install", "remove", "doctor"])
    parser.add_argument("--app-dir", help="手动指定 Devin 安装目录")
    parser.add_argument("--assets-dir", help="手动指定 devin-webapp-host/assets 目录")
    parser.add_argument("--no-rules", action="store_true", help="apply 时不安装中文思考规则")
    parser.add_argument("--with-rules", action="store_true", help="restore 时同时移除中文思考规则")
    parser.add_argument("--rule-action", choices=["install", "remove", "doctor"], default="install")
    parser.add_argument("--dry-run", action="store_true", help="只检查，不写入")
    args = parser.parse_args()

    if args.cmd == "rules":
        action = args.rule_action_pos or args.rule_action
        {"install": install_rules, "remove": remove_rules, "doctor": doctor_rules}[action]()
        return
    if args.dry_run:
        say("提示", "--dry-run 仅用于检查定位；本版本不会写入任何文件")
    app = find_app(args.app_dir)
    assets = Path(args.assets_dir).expanduser().resolve() if args.assets_dir else find_assets(app)
    out = find_out(assets)
    if args.cmd == "doctor":
        doctor(app, assets, out)
        return
    if args.cmd == "restore":
        restore_ui(app, assets)
        if args.with_rules:
            remove_rules()
        print("\n请完全退出 Devin 后重新打开。")
        return

    say("应用", f"Devin: {app}")
    say("应用", f"assets: {assets}")
    if args.dry_run:
        say("模式", "预演，不写入")
        doctor(app, assets, out)
        return
    apply_chunks(assets)
    patch_menu(assets)
    patch_language_api(assets)
    patch_nls(out)
    sign_mac(app)
    if not args.no_rules:
        install_rules()
    print("\n==== 完成 ====")
    print("请完全退出 Devin 后重新打开，执行 Configure Display Language，选择 中文(简体)。")
    print("中文思考规则已写入用户目录，新开会话即可生效。")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
