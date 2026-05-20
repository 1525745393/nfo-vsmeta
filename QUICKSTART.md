# 🚀 NFO to VSMETA Web UI 快速入门

## 一行命令启动

### 方式1：直接运行（推荐）

```bash
# 安装Flask（如果还没安装）
pip install flask

# 启动Web UI
python web_ui.py

# 访问 http://localhost:8000
```

### 方式2：使用快速启动脚本

```bash
# 添加执行权限（首次运行需要）
chmod +x start_webui.sh

# 启动
./start_webui.sh

# 查看状态
./start_webui.sh status

# 停止
./start_webui.sh stop

# 使用指定端口
./start_webui.sh start -p 8080

# Docker启动
./start_webui.sh docker
```

## 🎯 3分钟上手

### 第1步：打开界面
在浏览器中访问：`http://localhost:8000`

### 第2步：配置目录
在"转换"页面设置电影目录：
```
/path/to/your/movies
```

### 第3步：开始转换
点击"🚀 开始转换"按钮

### 第4步：查看进度
在仪表盘查看实时进度

## 📱 多平台使用

### Windows
```bash
# CMD 或 PowerShell
python web_ui.py

# 浏览器打开
http://localhost:8000
```

### Mac / Linux
```bash
# 终端
python3 web_ui.py

# 浏览器打开
http://localhost:8000
```

### NAS（群晖）
```bash
# SSH连接到群晖
ssh admin@192.168.1.100

# 安装Docker（如果还没安装）
# 套件中心 → 搜索 "Docker" → 安装

# 运行容器
docker run -d \
  --name nfo-converter \
  -p 8000:8000 \
  -v /volume1/movies:/workspace/movies \
  python:3.11-slim \
  bash -c "pip install flask -q && cd /workspace && python web_ui.py --host 0.0.0.0 --port 8000"

# 浏览器访问（替换为你的NAS IP）
http://192.168.1.100:8000
```

### Docker 容器
```bash
# 构建镜像
docker build -t nfo-converter .

# 运行容器
docker run -d \
  --name nfo-converter \
  -p 8000:8000 \
  -v $(pwd)/movies:/workspace/movies \
  nfo-converter

# 浏览器访问
http://localhost:8000
```

## 🔧 常用配置

### 启用Token认证
```bash
python web_ui.py --token my-secret-token
```

### 修改端口
```bash
python web_ui.py --port 8080
```

### 局域网访问
```bash
python web_ui.py --host 0.0.0.0 --port 8000
```

## 🎨 功能概览

### 仪表盘
- ✅ 统计信息（总文件、已处理、成功、失败）
- ✅ 实时进度条
- ✅ 快捷操作

### 转换控制
- ✅ 目录配置
- ✅ 线程数设置
- ✅ 备份开关
- ✅ 预演模式
- ✅ 扫描结果表格

### 配置管理
- ✅ 图片压缩
- ✅ 安全写入
- ✅ 文件过滤
- ✅ 编码修复

### 日志查看
- ✅ 实时日志流
- ✅ 自动滚动
- ✅ 日志清空

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存配置 |
| `Ctrl + Enter` | 开始转换 |
| `T` | 切换主题 |
| `1-4` | 切换页面 |

## 🐛 常见问题

### 1. 端口被占用
```bash
# 查看占用端口的进程
netstat -tuln | grep 8000

# 使用其他端口
python web_ui.py --port 8080
```

### 2. 权限错误
```bash
# 修复目录权限
chmod -R 755 /path/to/movies
```

### 3. Docker权限问题
```bash
# Linux 添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录
exit
ssh user@host
```

## 📚 详细文档

- [完整使用指南](WEBUI_README.md)
- [Docker部署详解](DOCKER_WEBUI.md)
- [API接口文档](WEBUI_README.md#api-接口)

## 🎉 小技巧

### 1. 快速测试配置
先启用"预演模式"测试配置

### 2. 查看实时日志
在"日志"页面查看详细处理过程

### 3. 使用键盘快捷键
提高操作效率

### 4. 定期备份
重要数据记得备份

## 💡 提示

- 🌙 支持深色/浅色主题切换
- 📱 完全响应式，移动端也能用
- 🔒 支持Token认证保护
- 🐳 一键Docker部署
- ⚡ 实时进度监控

## 📞 获取帮助

- 查看日志：`./start_webui.sh logs`
- 查看状态：`./start_webui.sh status`
- 停止服务：`./start_webui.sh stop`
- 查看帮助：`./start_webui.sh help`

## 🎊 享受使用！

如果觉得好用，请：
- ⭐ Star 项目
- 🐛 提交Bug
- 📝 贡献代码
- 📢 分享给朋友

---

**版本**: v5.0.0  
**更新**: 2024  
**兼容**: Windows · macOS · Linux · NAS · Docker
