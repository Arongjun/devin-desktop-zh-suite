# Changelog

## 1.0.0 (2026-11-21)

- 整合 `CarlCloud-dev/devin-zh-patch` 的界面词典、语言注册与本地持久化补丁。
- 整合 `Hezexian/devin-desktop-zh-cn` 的官方简体中文语言包方案（用于菜单/命令面板/编辑器）。
- 整合 `lvhaotian4-max/devin-chinese-thinking` 的中文思考规则 v2 与项目级模板。
- 新增 Windows 一键脚本与还原脚本（PowerShell，无需额外依赖）。
- 新增 macOS 一键脚本与还原脚本（Python 3，自动 ad-hoc 重签名）。
- 新增 NLS 词条数一致性检查：不一致时跳过内核替换，避免文案错位。
- 新增 `doctor` 只读检查、规则独立安装/移除、完整备份与幂等保护。
