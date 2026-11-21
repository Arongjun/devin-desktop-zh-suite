# 来源与致谢

本项目整合了以下社区项目的成果，并针对 Windows / macOS 双平台做了适配、合并与去重。

## 上游项目

### 1. CarlCloud-dev/devin-zh-patch — 界面汉化与语言持久化
- 仓库：https://github.com/CarlCloud-dev/devin-zh-patch
- 采用内容：`assets/zh-CN-translation.js`、`assets/zh-CN-review.js`、`assets/nls.messages.zh.json`、`assets/nls.messages.zh.js`，以及语言注册 / `users/ui-language` 本地回退的补丁思路。
- 原项目说明：第三方非官方补丁，自动备份 `.zhorig`，覆盖 Webapp 与 Workbench 两层本地化。

### 2. Hezexian/devin-desktop-zh-cn — 官方语言包方案
- 仓库：https://github.com/Hezexian/devin-desktop-zh-cn
- 采用内容：通过微软官方 VS Code 简体中文语言包 `MS-CEINTL.vscode-language-pack-zh-hans` 覆盖菜单/命令面板/编辑器的方案说明。
- 该项目基于 [N1n3VASthR33H/devin-zh](https://github.com/vvvvvvvvvashhh/devin-zh) 改进，并整合 [KawaYiLab/Devin-Web-Chinese](https://github.com/KawaYiLab/Devin-Web-Chinese) 的中文词典，在此一并致谢。

### 3. lvhaotian4-max/devin-chinese-thinking — 中文思考规则
- 仓库：https://github.com/lvhaotian4-max/devin-chinese-thinking
- 采用内容：`rules/chinese-thinking-v2.md`、`rules/project-agents.md` 原文，以及 `.devin/rules` / `AGENTS.md` / 旧版全局规则路径的加载机制。
- 规则模板中的 `<!-- devin-chinese-thinking:v2 -->` 标记保留，仅额外包裹本包的托管块标记以便还原。

## 本包改动

- 将 Windows 的一键 `.bat/.ps1` 与 macOS 的 `.command/.py` 统一到同一仓库与同一套资产。
- 菜单 bundle 支持 `entry-host-*` 与 `chunk-entry-host-*` 两种命名。
- 语言 API 支持新旧两种结构（`.json()` 旧式 / `body` 新式）。
- NLS 内核替换增加词条数一致性检查，不一致时跳过以避免乱码。
- macOS 修改 app bundle 后自动 ad-hoc 重签名并保留 entitlements。
- 规则安装支持追加、备份与精确移除，不覆盖用户已有规则。

## 许可

本项目代码采用 MIT License。上游资产与规则的版权归各自作者所有，详见其仓库 LICENSE 文件。
