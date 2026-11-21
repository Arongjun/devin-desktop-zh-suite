# Devin Desktop 简体中文增强套件（Windows / macOS）

仓库地址：https://github.com/Arongjun/devin-desktop-zh-suite

把三个社区方案整合成一套**跨平台、可还原、幂等**的 Devin 汉化工具：

| 来源 | 本包吸收的能力 |
|---|---|
| [CarlCloud-dev/devin-zh-patch](https://github.com/CarlCloud-dev/devin-zh-patch) | Webapp 主界面 i18next 词典（2 万余条）、Review 词典、语言注册与本地持久化补丁、NLS 内核替换思路 |
| [Hezexian/devin-desktop-zh-cn](https://github.com/Hezexian/devin-desktop-zh-cn) | 官方 VS Code 简体中文语言包方案、菜单/编辑器中文思路、DOM 层补译理念 |
| [lvhaotian4-max/devin-chinese-thinking](https://github.com/lvhaotian4-max/devin-chinese-thinking) | `always_on` 中文思考规则 v2（可见思考、计划、工具说明、子代理、总结） |

> 非官方项目，与 Cognition / Devin 官方无关。修改安装文件前请知悉风险；所有改动都有备份。

---

## 功能

- ✅ **主界面汉化**：首页、设置、侧边栏、会话、Review 等（i18next 词典）
- ✅ **语言持久化补丁**：选择 `zh` 时跳过服务端枚举校验，重启后不会被重置为英文
- ✅ **中文思考规则**：写入用户级 `.devin/rules/`、`AGENTS.md` 与旧版全局规则路径，新开会话生效
- ✅ **Windows / macOS 双平台**：各自提供双击即可运行的入口
- ✅ **幂等 + 自动备份**：重复运行不会重复写入；原文件备份为 `*.zhorig`，规则备份为 `*.bak-<时间戳>`
- ⚠️ **NLS 内核**：仅当本机词条数与补丁词库完全一致时才替换；否则跳过，避免索引错位导致乱码

---

## 快速开始

**三步搞定，不用敲命令。** 下载本仓库并解压，然后按你的系统选一行：

| 平台 | ① 双击运行 | ② 重启 Devin | ③ 切换语言 |
|:---:|:---:|:---:|:---:|
| **Windows** | `一键汉化.bat` | 完全退出后重新打开 | 命令面板 → `Configure Display Language` → `中文(简体)` |
| **macOS** | `汉化-Mac.command` | 完全退出后重新打开 | 命令面板 → `Configure Display Language` → `中文(简体)` |

第 ③ 步完成后**新开一个会话**，中文思考规则自动生效。

> **macOS 注意**：需要 Python 3（没有会提示安装）。**不要双击 Windows 的 `.bat`** —— macOS 不会执行，只会用编辑器当文本打开，这正是很多人以为「脚本没反应」的原因。

<!-- 截图位：把汉化后的主界面截图保存为 docs/screenshots/main-ui.png，然后取消下方一行的注释即可在 README 展示效果预览：
![汉化效果预览](docs/screenshots/main-ui.png)
-->

### 自动探测失败？手动指定目录

脚本会尝试自动定位 Devin 安装目录；若失败，手动指定即可：

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\apply-zh.ps1 -AssetsDir "D:\...\devin-webapp-host\assets"
```

```bash
# macOS / Linux
python3 scripts/devin_zh.py apply --app-dir /Applications/Devin.app
```

---

## 菜单 / 命令面板仍是英文？

Devin 基于 VS Code，菜单栏、命令面板和编辑器 UI 走 **NLS 内核数组**。不同版本词条数量不同，直接替换会错位乱码。因此本包只在词条数一致时替换，其余情况推荐安装**官方简体中文语言包**：

1. 在 Devin 扩展市场安装 `MS-CEINTL.vscode-language-pack-zh-hans`（微软简体中文语言包）。
2. 执行 `Configure Display Language` → 选择 `zh-cn`。
3. 完全重启 Devin。

这与 Hezexian 方案的做法一致，是覆盖菜单/编辑器最安全的方式。

---

## 还原

| 平台 | 操作 |
|---|---|
| macOS | 双击 `还原英文-Mac.command` |
| Windows | 双击 `还原英文.bat` |

命令行方式：

```bash
python3 scripts/devin_zh.py restore --with-rules   # macOS / Linux
python3 scripts/devin_zh.py doctor                 # 只读检查当前状态
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\restore-zh.ps1 -RemoveRules
```

---

## 中文思考规则

规则文件写入以下位置（已存在则追加，不覆盖原有内容）：

| 系统 | 路径 |
|---|---|
| Windows | `%USERPROFILE%\.devin\rules\chinese-thinking.md` |
| Windows | `%APPDATA%\devin\AGENTS.md` |
| Windows（旧版） | `%USERPROFILE%\.codeium\windsurf\memories\global_rules.md` |
| macOS / Linux | `~/.devin/rules/chinese-thinking.md` |
| macOS / Linux | `~/.config/devin/AGENTS.md` |
| macOS / Linux（旧版） | `~/.codeium/windsurf/memories/global_rules.md` |

单独管理规则：

```bash
python3 scripts/devin_zh.py rules install
python3 scripts/devin_zh.py rules doctor
python3 scripts/devin_zh.py rules remove
```

只想让某个项目使用中文，可把 `rules/project-agents.md` 复制到项目根目录的 `AGENTS.md`。

**边界说明**：规则只约束模型生成的**可见文本**（思考说明、计划、工具说明、回复），无法控制不可见的内部推理，也不保证 100% 不漂移。代码、路径、API、SQL、日志原文按规则保持原样。

---

## 目录结构

```
devin-desktop-zh-suite/
├── 一键汉化.bat              # Windows 入口
├── 还原英文.bat              # Windows 还原
├── 汉化-Mac.command          # macOS 入口
├── 还原英文-Mac.command      # macOS 还原
├── scripts/
│   ├── apply-zh.ps1          # Windows 安装逻辑
│   ├── restore-zh.ps1        # Windows 还原逻辑
│   └── devin_zh.py           # macOS / Linux 跨平台逻辑（Windows 亦可用）
├── assets/                   # 主界面词典 + NLS 词库
├── rules/                    # 中文思考规则模板
└── docs/                     # 平台说明、来源与致谢
```

---

## 常见问题

**Q：Devin 更新后汉化失效？**
重新运行一次安装脚本即可（幂等）。若 bundle 结构变化导致脚本报错，请先看 `doctor` 输出并更新脚本。

**Q：macOS 提示「应用已损坏」？**
脚本会在修改后对 app 重新 ad-hoc 签名。若仍被 Gatekeeper 拦截，可运行 `xattr -d com.apple.quarantine /Applications/Devin.app`，或重装 Devin 后再试。

**Q：为什么要跳过 NLS 替换？**
本机 Devin 3.14.30833 的 `nls.messages.json` 有 27,547 条，上游补丁只有 21,210 条；索引错位会造成大面积文案错乱。宁可保留英文，也不制造乱码。

**Q：服务端返回的内容（会话标题、模型名、报错）能汉化吗？**
不能，这部分来自服务端，不在本地补丁范围内。

---

## 致谢与许可

详见 [docs/SOURCES.md](docs/SOURCES.md)。本项目采用 MIT 许可，并保留上游作者的版权声明。
