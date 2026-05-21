# 自动化脚本

本目录包含项目使用的各种自动化脚本。

## 脚本列表

### 1. auto_release.py - 自动化发布脚本
完整的自动化发布解决方案，支持版本管理、变更日志生成、构建、发布等。

**功能：**
- 自动版本号管理（支持 major/minor/patch）
- 自动生成变更日志
- 构建分发包
- 创建Git标签
- 发布到PyPI
- 创建GitHub Release

**使用方法：**
```bash
# 预览发布（不执行实际操作）
python scripts/auto_release.py --type patch --dry-run

# 执行发布（patch版本）
python scripts/auto_release.py --type patch

# 执行发布（minor版本）
python scripts/auto_release.py --type minor

# 执行发布（major版本）
python scripts/auto_release.py --type major

# 跳过测试
python scripts/auto_release.py --type patch --skip-tests

# 单独发布到PyPI
python scripts/auto_release.py --pypi
```

### 2. bump_version.py - 版本号管理
用于更新项目版本号的脚本。

**使用方法：**
```bash
# 更新版本号（预览）
python scripts/bump_version.py patch --dry-run

# 更新版本号（实际执行）
python scripts/bump_version.py patch
```

### 3. release.sh - Shell发布脚本
简单的Shell脚本，用于快速发布流程。

**使用方法：**
```bash
# 执行发布
bash scripts/release.sh patch

# 仅预览版本更新
bash scripts/release.sh patch --dry-run
```

## GitHub Actions 工作流

### CI 测试 (.github/workflows/ci.yml)
- 在 push 和 pull request 时自动运行
- 测试多个Python版本（3.8 - 3.12）
- 代码格式检查（Black, isort）
- Lint检查（flake8, mypy）
- 测试覆盖率报告

### Release 发布 (.github/workflows/release.yml)
- 在推送版本标签时自动触发
- 运行测试
- 构建包
- 创建GitHub Release
- 发布到PyPI

### Docker 构建 (.github/workflows/docker.yml)
- 在推送标签时自动构建Docker镜像
- 推送到GitHub Container Registry
- 生成SBOM
- 安全漏洞扫描

## 使用建议

1. **日常开发**：使用 `auto_release.py --dry-run` 预览发布效果
2. **正式发布**：使用 `auto_release.py --type <type>` 执行完整发布
3. **紧急修复**：直接使用 `bump_version.py patch` 快速更新版本
4. **持续集成**：GitHub Actions 会自动处理测试和发布流程

## 配置要求

### GitHub Secrets（需要手动配置）
- `PYPI_API_TOKEN`: PyPI API令牌（用于发布到PyPI）

### 本地开发环境
```bash
# 安装开发依赖
pip install -e ".[dev,test]"

# 安装发布工具
pip install build twine
```
