# NFO to VSMETA 转换器 Web UI 使用指南

## 🌟 简介

这是一个现代化的 Web UI 界面，支持在电脑、NAS 和容器环境中运行。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 启动 Web UI

```bash
python web_ui.py
```

访问：`http://localhost:8000`

### 3. 指定端口

```bash
python web_ui.py --port 8080
```

### 4. 启用 Token 认证

```bash
python web_ui.py --token your-secret-token
```

## 📱 界面功能

### 仪表盘
- 查看转换统计信息
- 实时进度显示
- 快捷操作入口
- 键盘快捷键提示

### 转换控制
- 配置处理目录
- 设置线程数和处理模式
- 启用/禁用备份
- 预演模式测试
- 实时扫描结果

### 配置管理
- 图片压缩设置
- 安全写入模式
- 文件过滤规则
- 编码修复选项

### 日志查看
- 实时日志流
- 日志级别过滤
- 自动滚动
- 导出日志

## ⌨️ 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存配置 |
| `Ctrl + Enter` | 开始转换 |
| `T` | 切换深色/浅色主题 |
| `1` | 切换到仪表盘 |
| `2` | 切换到转换 |
| `3` | 切换到配置 |
| `4` | 切换到日志 |

## 🐳 容器部署

### Docker 快速启动

```bash
# 运行容器
docker run -d \
  --name nfo-converter \
  -p 8000:8000 \
  -v $(pwd)/movies:/workspace/movies \
  python:3.11-slim \
  bash -c "pip install flask && cd /workspace && python web_ui.py --host 0.0.0.0 --port 8000"
```

### Docker Compose

```yaml
version: '3.8'
services:
  nfo-converter:
    image: python:3.11-slim
    container_name: nfo-converter
    ports:
      - "8000:8000"
    volumes:
      - ./movies:/workspace/movies
    command: bash -c "pip install flask && python web_ui.py --host 0.0.0.0 --port 8000"
    restart: unless-stopped
```

## 💻 NAS 部署

### 群晖 (Synology)

1. 安装 Docker 套件
2. 通过 SSH 连接
3. 运行容器命令

### QNAP / 威联通

1. 安装 Container Station
2. 创建新容器
3. 配置端口映射和数据卷

详细说明请查看 [DOCKER_WEBUI.md](DOCKER_WEBUI.md)

## 🎨 界面预览

### 深色主题
```
┌────────────────────────────────────────┐
│  🚀 NFO → VSMETA   [就绪] [🌙]        │
├────────────────────────────────────────┤
│  📊 仪表盘 │ 🚀 转换 │ ⚙️ 配置 │ 📋 日志 │
├────────────────────────────────────────┤
│                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │总文件│ │已处理│ │ 成功 │ │ 失败 │ │
│  │  0   │ │  0   │ │  0   │ │  0   │ │
│  └──────┘ └──────┘ └──────┘ └──────┘ │
│                                        │
│  ════════════════ 0% ════════════════ │
│            等待开始...                  │
│                                        │
└────────────────────────────────────────┘
```

### 浅色主题
界面会自动根据系统主题切换，保持一致的视觉体验。

## 🔒 安全建议

### 1. 网络访问控制

```bash
# 只允许本地访问
python web_ui.py --host 127.0.0.1 --port 8000

# 局域网访问（建议配合防火墙）
python web_ui.py --host 0.0.0.0 --port 8000 --token your-secret-token
```

### 2. Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name converter.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 3. 定期备份

```bash
# 备份配置
cp config.json config.json.backup

# 备份数据
tar -czf backup.tar.gz movies/ .backup/
```

## 🐛 故障排除

### 问题 1: 端口被占用

```bash
# 检查端口占用
netstat -tuln | grep 8000

# 使用其他端口
python web_ui.py --port 8080
```

### 问题 2: 权限错误

```bash
# 设置目录权限
chmod -R 755 movies/
chown -R $USER:$USER movies/
```

### 问题 3: 容器无法访问文件

```bash
# 检查 Docker 权限
docker run --rm -v $(pwd)/movies:/workspace/movies python:3.11-slim ls -la /workspace/movies
```

## 📊 API 接口

### 获取状态
```bash
curl http://localhost:8000/api/status
```

### 获取配置
```bash
curl http://localhost:8000/api/config
```

### 保存配置
```bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"directory": "/workspace/movies", "max_workers": 8}'
```

### 开始转换
```bash
curl -X POST http://localhost:8000/api/convert/start \
  -H "Content-Type: application/json" \
  -d '{"directory": "/workspace/movies", "max_workers": 4}'
```

### 停止转换
```bash
curl -X POST http://localhost:8000/api/convert/stop
```

### 获取日志
```bash
curl http://localhost:8000/api/logs
```

## 🎯 最佳实践

### 1. 性能优化

- 使用 SSD 存储
- 合理设置线程数（CPU 核心数的 2-4 倍）
- 启用图片缓存

### 2. 资源管理

- 定期清理备份文件
- 监控磁盘空间
- 使用增量备份

### 3. 安全加固

- 启用 Token 认证
- 配置防火墙规则
- 定期更新依赖

## 📝 版本历史

### v5.0.0 (2024-当前)
- ✅ 现代化 UI 设计
- ✅ 响应式布局
- ✅ 深色/浅色主题切换
- ✅ 实时进度监控
- ✅ Docker 容器支持
- ✅ NAS 兼容部署

### v4.0.0 (历史版本)
- 基础 Web UI 功能
- 文件扫描和转换
- 配置管理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

- GitHub: https://github.com/your-repo
- 邮箱: support@example.com
- 文档: https://docs.example.com
