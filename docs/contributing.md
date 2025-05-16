# 贡献指南

感谢您对SDTM数据迁移工具的关注！我们欢迎来自社区的贡献，帮助改进和完善这个工具。

## 贡献流程

### 1. Fork仓库

首先，在GitHub上fork本仓库到您自己的账户。

### 2. 克隆仓库

```bash
git clone https://github.com/your-username/SDTM.git
cd SDTM
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx`: 新功能开发
- `bugfix/xxx`: 错误修复
- `docs/xxx`: 文档改进
- `refactor/xxx`: 代码重构

### 4. 开发与测试

- 确保代码遵循项目的编码规范
- 添加必要的注释和文档
- 编写测试用例验证功能正确性

### 5. 提交更改

```bash
git add .
git commit -m "描述你的更改"
```

提交信息格式建议：
```
类型: 简短描述

详细描述（如有必要）
```

类型包括：
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档变更
- `style`: 格式调整（不影响代码功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 6. 推送到远程仓库

```bash
git push origin feature/your-feature-name
```

### 7. 创建Pull Request

在GitHub上从您的分支创建Pull Request到主仓库的main分支。

## 编码规范

### Python代码规范

- 遵循PEP 8编码风格
- 使用有意义的变量名和函数名
- 添加适当的注释
- 函数和类应有docstring说明用途和参数

### 文档规范

- 使用Markdown格式编写文档
- 保持文档结构清晰
- 中文文档使用中文标点符号

## 版本控制

项目使用语义化版本控制 (Semantic Versioning)：

- 主版本号：不兼容的API变更
- 次版本号：向后兼容的功能性新增
- 修订号：向后兼容的问题修正

## 问题报告

如果您发现了问题但没有时间或能力修复，请创建Issue。

创建Issue时请包含：
- 问题的简要描述
- 重现步骤
- 期望行为
- 实际行为
- 环境信息（操作系统、Python版本等）
- 相关的日志或屏幕截图

## 行为准则

- 尊重所有贡献者
- 保持专业和友好的交流
- 接受建设性批评
- 聚焦在项目改进而非个人
- 欢迎新人参与 