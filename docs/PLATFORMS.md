# 平台与版本兼容说明

## 已验证环境

| 平台 | Devin 版本 | 验证内容 |
|---|---|---|
| macOS 14+ (arm64) | 3.14.30833 | 主界面注册 zh、语言 API 本地回退、规则安装、ad-hoc 重签名、幂等与还原 |
| Windows x64 | 3.12.59 / 3.14.x（依据上游方案适配） | 主界面补丁、语言 API 新旧结构、NLS 条件替换、规则安装与还原 |

> Windows 分支沿用上游脚本的探测逻辑（常见安装目录、运行进程、注册表），并扩展了 `chunk-*` bundle 命名支持；是在上游已验证方案基础上的整合适配，未在本机实机运行。

## 文件布局差异

| 项目 | Windows | macOS |
|---|---|---|
| 应用根目录 | `...\Devin\` | `/Applications/Devin.app/` |
| assets | `resources\app\out\vs\workbench\devin-webapp-host\assets` | `Contents/Resources/app/out/vs/workbench/devin-webapp-host/assets` |
| 菜单 bundle | `entry-host-editor-mode-menu-*.js` | `chunk-entry-host-editor-mode-menu-*.js` |
| 语言 API bundle | `entry-host-index-*.js` | `chunk-app-initial-*.js` |
| 签名 | 不需要 | 修改后需 ad-hoc 重签名 |

## NLS 内核补丁的判定

脚本会对比本机 `nls.messages.json` 与补丁词库的条目数：

- **一致**：整体替换为中文数组（含 `.zhorig` 备份），菜单栏/命令面板/编辑器一并中文。
- **不一致**：跳过，并建议使用官方 VS Code 简体中文语言包。强行替换会造成按索引取值的文案错位。

本机 macOS 3.14.30833 词条数为 27,547，上游补丁为 21,210，属于**跳过**情形。

## 更新后的处理

Devin 升级会覆盖安装目录文件，导致汉化失效。直接重跑安装脚本即可（幂等）。若脚本报「未找到 xxx / 结构已变化」，说明 bundle 结构变动，请查看 `doctor` 输出并更新脚本中的正则。
