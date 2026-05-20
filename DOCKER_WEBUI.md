# NFO to VSMETA 转换器 Web UI Docker配置

## 快速启动

```bash
# 构建镜像
docker build -t nfo-converter .

# 运行容器
docker run -d \
  --name nfo-converter \
  -p 8000:8000 \
  -v /path/to/your/movies:/workspace/movies \
  nfo-converter
```

## Docker Compose

```yaml
version: '3.8'

services:
  nfo-converter:
    image: nfo-converter:latest
    container_name: nfo-converter
    ports:
      - "8000:8000"
    volumes:
      - ./movies:/workspace/movies
      - ./config:/workspace/config
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 群晖 (Synology DSM) 部署

1. **安装 Docker 套件**
   - 控制面板 → 套件中心 → 搜索 "Docker" → 安装

2. **SSH 连接并拉取镜像**
```bash
sudo docker pull python:3.11-slim
```

3. **创建数据目录**
```bash
mkdir -p /volume1/docker/nfo-converter/movies
```

4. **启动容器**
```bash
sudo docker run -d \
  --name nfo-converter \
  --hostname nfo-converter \
  -p 8000:8000 \
  -v /volume1/docker/nfo-converter/movies:/workspace/movies \
  -v /volume1/docker/nfo-converter/config:/workspace/config \
  python:3.11-slim \
  bash -c "pip install flask && cd /workspace && python web_ui.py --host 0.0.0.0 --port 8000"
```

5. **访问 Web UI**
   打开浏览器访问：`http://<群晖IP>:8000`

## QNAP / 威联通 部署

```bash
# SSH 到 NAS
ssh admin@192.168.1.100

# 创建目录
mkdir -p /share/Container/nfo-converter

# 运行容器
docker run -d \
  --name nfo-converter \
  --hostname nfo-converter \
  -p 8000:8000 \
  -v /share/Container/nfo-converter/movies:/workspace/movies \
  -v /share/Container/nfo-converter/config:/workspace/config \
  python:3.11-slim \
  bash -c "pip install flask && cd /workspace && python web_ui.py --host 0.0.0.0 --port 8000"
```

## UNRAID 部署

1. **Docker Template**
```json
{
  "name": "NFO to VSMETA Converter",
  "repository": "python:3.11-slim",
  "tag": "latest",
  "ports": [
    "8000:8000"
  ],
  "volumes": [
    {
      "container_path": "/workspace/movies",
      "host_path": "/mnt/user/movies",
      "mode": "rw"
    }
  ],
  "post_script": "pip install flask && cd /workspace && python web_ui.py --host 0.0.0.0 --port 8000"
}
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | Asia/Shanghai | 时区设置 |
| `WORKERS` | 4 | 转换线程数 |
| `LOG_LEVEL` | INFO | 日志级别 |

## 数据持久化

### 重要数据卷

- `/workspace/movies` - 电影文件目录
- `/workspace/config` - 配置文件目录
- `/workspace/.backup` - 备份文件目录

## 安全建议

### 1. 添加认证

```bash
# 使用Token认证启动
python web_ui.py --host 0.0.0.0 --port 8000 --token your-secret-token
```

### 2. Nginx 反向代理 + HTTPS

```nginx
server {
    listen 443 ssl;
    server_name converter.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Docker网络隔离

```yaml
services:
  nfo-converter:
    image: nfo-converter:latest
    networks:
      - internal
    expose:
      - "8000"

networks:
  internal:
    driver: bridge
```

## 故障排除

### 容器无法启动

```bash
# 查看日志
docker logs nfo-converter

# 重新构建
docker build --no-cache -t nfo-converter .
```

### 端口冲突

```bash
# 检查端口占用
netstat -tuln | grep 8000

# 使用其他端口
docker run -p 8001:8000 nfo-converter
```

### 权限问题

```bash
# 设置正确的权限
chmod -R 755 /path/to/movies
chown -R 1000:1000 /path/to/movies
```

## 更新升级

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker build -t nfo-converter:latest .

# 停止旧容器
docker stop nfo-converter
docker rm nfo-converter

# 启动新容器
docker run -d \
  --name nfo-converter \
  -p 8000:8000 \
  -v /path/to/movies:/workspace/movies \
  nfo-converter:latest
```

## 健康检查

Web UI 提供健康检查端点：

```bash
# 检查服务状态
curl http://localhost:8001/api/status
```

返回示例：
```json
{
  "is_running": false,
  "progress": {
    "total": 0,
    "completed": 0,
    "success": 0,
    "failed": 0
  }
}
```

## 资源限制

建议资源配置：

| 环境 | CPU | 内存 | 说明 |
|------|-----|------|------|
| 电脑 | 2核 | 2GB | 正常负载 |
| NAS | 2核 | 1GB | 低功耗环境 |
| 容器 | 1核 | 512MB | 最小配置 |

## 使用建议

1. **定期备份配置**
```bash
docker cp nfo-converter:/workspace/config.json ./backup/
```

2. **监控资源使用**
```bash
docker stats nfo-converter
```

3. **日志管理**
```bash
# 限制日志大小
docker logs --tail 100 nfo-converter > app.log
```

## 技术支持

- GitHub Issues: https://github.com/your-repo/issues
- 文档: https://docs.example.com
