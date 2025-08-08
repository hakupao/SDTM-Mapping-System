# 贡献指南

感谢您对 SDTM 数据迁移工具的关注！欢迎通过 Issue/PR 改进本项目。

## 工作流（Workflow）

1. Fork 仓库并克隆到本地：
```bash
git clone https://github.com/your-username/SDTM-Mapping-System.git
cd SDTM-Mapping-System
```
2. 创建开发分支：
```bash
git checkout -b feature/your-feature-name
```
分支命名建议：
- `feat/xxx`：新功能
- `fix/xxx`：缺陷修复
- `docs/xxx`：文档变更
- `refactor/xxx`：重构

3. 开发与测试：
- 遵循 PEP8（Python）与本仓库代码风格
- 较复杂函数需添加 docstring（PEP257）
- 新功能/修复应包含必要的单元测试（pytest）
- 文档更新：`docs/` 与 `README.md`

4. 提交（Commit）：
- 推荐使用 Conventional Commits：
  - `feat: 模块/功能 简述`
  - `fix: 问题 简述`
  - `docs: 文档变更 简述`
  - `refactor: 重构 简述`
  - `test: 测试 简述`
  - `chore: 杂项 简述`
```bash
git add .
git commit -m "feat: format 阶段输出检查型 F-<name>[chk].csv"
```

5. 推送与 PR：
```bash
git push origin feature/your-feature-name
```
在 GitHub 创建 Pull Request 至 `main`。

## 代码与文档风格

- Python：
  - PEP8/PEP257
  - 强类型倾向、具名变量、避免深层嵌套
  - 重要逻辑添加中文注释与简明 docstring
- 文档：
  - Markdown，中文标点
  - 引用文件/函数请使用反引号包裹，如 `VC_OP05_mapping.py`

## 安全与合规

- 禁止提交明文凭据（密码、Token）；请使用环境变量或 `.env`（未入库）
- 不要提交大体量数据/受保护数据集
- 版权遵循各数据及依赖许可

## Issue 报告模版建议

- 问题简述、复现步骤、期望与实际、环境信息（OS、Python、MySQL）、日志与截图

感谢您的贡献！ 