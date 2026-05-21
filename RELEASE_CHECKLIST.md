# NFO to VSMETA 发布检查清单

## 发布前检查

### 1. 代码检查
- [ ] 所有代码已提交到Git
- [ ] 提交信息符合规范
- [ ] 没有未解决的TODO或FIXME注释
- [ ] 代码已通过lint检查
- [ ] 代码已通过类型检查

### 2. 测试检查
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 测试覆盖率达标（>80%）
- [ ] 手动测试关键功能

### 3. 文档检查
- [ ] README.md已更新
- [ ] CHANGELOG.md已更新
- [ ] 文档示例已测试
- [ ] API文档完整（如有API变更）

### 4. 配置检查
- [ ] 版本号已更新
- [ ] pyproject.toml配置正确
- [ ] requirements.txt同步更新
- [ ] Docker配置检查

### 5. 依赖检查
- [ ] 所有依赖已测试
- [ ] 新增依赖已评估
- [ ] 安全漏洞扫描通过

### 6. 发布准备
- [ ] GitHub Secrets已配置（PYPI_API_TOKEN）
- [ ] Docker Hub访问正常（如需发布）
- [ ] 发布版本标签已确认

## 发布步骤

### 自动发布（推荐）
```bash
# 1. 预览发布
python scripts/auto_release.py --type patch --dry-run

# 2. 执行发布
python scripts/auto_release.py --type patch
```

### 手动发布
```bash
# 1. 更新版本号
python scripts/bump_version.py patch

# 2. 更新变更日志
# 编辑 CHANGELOG.md

# 3. 提交更改
git add .
git commit -m "chore: 准备发布 v2.0.0"
git push

# 4. 创建标签
git tag -a v2.0.0 -m "发布版本 v2.0.0"
git push origin v2.0.0

# 5. GitHub Actions 将自动：
#    - 运行测试
#    - 构建包
#    - 创建Release
#    - 发布到PyPI
```

## 发布后检查

- [ ] GitHub Release已创建
- [ ] PyPI包可正常安装
- [ ] Docker镜像已构建（如适用）
- [ ] 下载链接有效
- [ ] 变更日志显示正确

## 回滚计划

如需回滚：
```bash
# 1. 删除GitHub上的Release
# 2. 删除本地和远程标签
git tag -d v2.0.0
git push origin :refs/tags/v2.0.0

# 3. 撤销版本号更改
git revert HEAD

# 4. 推送撤销
git push
```

## 紧急联系

- 维护者：NFO to VSMETA Team
- 问题反馈：https://github.com/1525745393/TRAE--AI-NFO-to-VSMETA/issues

## 版本规范

采用语义化版本 (SemVer)：
- MAJOR.MINOR.PATCH
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修复
