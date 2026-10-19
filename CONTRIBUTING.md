# Contributing

感谢你参与本项目。为了让问题和改动更容易维护，请先阅读以下说明。

## 提交 Issue

- Bug 报告请提供操作系统、Python 版本、FFmpeg 版本、复现步骤和错误信息。
- 功能建议请说明使用场景、期望行为和可能的替代方案。
- 不要在 Issue 中提交账号、密码、Cookie、验证码、私有视频或个人路径。

## 开发流程

1. Fork 本仓库。
2. 基于 `main` 创建功能分支：

   ```bash
   git checkout -b feature/your-feature
   ```

3. 安装依赖：

   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. 修改脚本或文档。
5. 运行检查：

   ```bash
   make check
   ```

6. 提交代码并推送到你的 Fork。
7. 创建 Pull Request，并说明修改原因、测试方式和影响范围。

## 提交信息建议

建议使用简洁明确的提交信息：

- `feat: add support for custom output frame rate`
- `fix: handle missing ffprobe duration`
- `docs: update clip generation examples`
- `chore: update project metadata`

## Pull Request 检查清单

- [ ] 已说明修改目的。
- [ ] 已在本地运行 `make check`。
- [ ] 已更新必要的文档或示例。
- [ ] 未包含账号、密码、Cookie、验证码或私有素材。
- [ ] 未引入无关的大规模格式化或重命名。

## 文档与脚本风格

- 命令示例应可直接复制运行。
- 新增参数应在 README 或脚本帮助信息中说明。
- Shell 脚本优先使用安全的变量引用方式。
- 批量处理脚本应尽量支持幂等执行，已完成的输出可跳过。
