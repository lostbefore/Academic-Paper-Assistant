# 部署指南 | Deployment Guide

[English](#english-deployment-guide) | [中文](#中文部署指南)

---

## English Deployment Guide

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed
- Domain name (optional, for HTTPS)
- API keys ready (Anthropic, etc.)

### Quick Deploy with Docker

1. **Clone repository on server**
   ```bash
   git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
   cd Academic-Paper-Assistant
   ```

2. **Create environment file**
   ```bash
   nano .env
   ```

   Add your configuration:
   ```env
   ANTHROPIC_API_KEY=your_key_here
   SEMANTIC_SCHOLAR_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   UNSPLASH_ACCESS_KEY=your_key_here
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:8000/api/status
   ```

The application will be available at `http://your-server-ip:8000`

### Production Deployment with Nginx

1. **Create nginx.conf**
   ```nginx
   events {
       worker_connections 1024;
   }

   http {
       server {
           listen 80;
           server_name yourdomain.com;

           location / {
               proxy_pass http://app:8000;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection 'upgrade';
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               proxy_cache_bypass $http_upgrade;
           }
       }
   }
   ```

2. **Deploy with Nginx**
   ```bash
   docker-compose --profile with-nginx up -d
   ```

### HTTPS with Let's Encrypt

1. **Install certbot**
   ```bash
   sudo apt install certbot
   ```

2. **Get certificate**
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. **Copy certificates**
   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
   ```

4. **Update nginx.conf for HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       server_name yourdomain.com;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;

       location / {
           proxy_pass http://app:8000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   ```

### Cloud Platform Deployment

#### Deploy to Railway

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and deploy:
   ```bash
   railway login
   railway init
   railway up
   ```

#### Deploy to Render

1. Create `render.yaml`:
   ```yaml
   services:
     - type: web
       name: academic-paper-assistant
       env: docker
       dockerfilePath: ./Dockerfile
       envVars:
         - key: ANTHROPIC_API_KEY
           sync: false
         - key: CORS_ORIGINS
           value: https://yourdomain.com
   ```

2. Push to GitHub and connect Render

#### Deploy to VPS (DigitalOcean, Linode, etc.)

1. Create a droplet with Docker pre-installed
2. SSH into server
3. Follow "Quick Deploy with Docker" steps above
4. Set up UFW firewall:
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

### Monitoring & Maintenance

**View logs:**
```bash
docker-compose logs -f app
```

**Update application:**
```bash
git pull
docker-compose down
docker-compose up -d --build
```

**Backup data:**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz output/
```

---

## 中文部署指南

### 环境要求

- Linux 服务器（推荐 Ubuntu 20.04+）
- 安装 Docker & Docker Compose
- 域名（可选，用于 HTTPS）
- 准备好的 API 密钥

### 使用 Docker 快速部署

1. **在服务器上克隆仓库**
   ```bash
   git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
   cd Academic-Paper-Assistant
   ```

2. **创建环境配置文件**
   ```bash
   nano .env
   ```

   添加你的配置：
   ```env
   ANTHROPIC_API_KEY=your_key_here
   SEMANTIC_SCHOLAR_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   UNSPLASH_ACCESS_KEY=your_key_here
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

3. **使用 Docker Compose 部署**
   ```bash
   docker-compose up -d
   ```

4. **验证部署**
   ```bash
   curl http://localhost:8000/api/status
   ```

应用将可通过 `http://服务器IP:8000` 访问

### 使用 Nginx 生产环境部署

1. **创建 nginx.conf**
   ```nginx
   events {
       worker_connections 1024;
   }

   http {
       server {
           listen 80;
           server_name yourdomain.com;

           location / {
               proxy_pass http://app:8000;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection 'upgrade';
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               proxy_cache_bypass $http_upgrade;
           }
       }
   }
   ```

2. **使用 Nginx 部署**
   ```bash
   docker-compose --profile with-nginx up -d
   ```

### 使用 Let's Encrypt 配置 HTTPS

1. **安装 certbot**
   ```bash
   sudo apt install certbot
   ```

2. **获取证书**
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. **复制证书**
   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
   ```

4. **更新 nginx.conf 支持 HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       server_name yourdomain.com;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;

       location / {
           proxy_pass http://app:8000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   ```

### 云平台部署

#### 部署到 Railway

1. 安装 Railway CLI：
   ```bash
   npm install -g @railway/cli
   ```

2. 登录并部署：
   ```bash
   railway login
   railway init
   railway up
   ```

#### 部署到 Render

1. 创建 `render.yaml`：
   ```yaml
   services:
     - type: web
       name: academic-paper-assistant
       env: docker
       dockerfilePath: ./Dockerfile
       envVars:
         - key: ANTHROPIC_API_KEY
           sync: false
         - key: CORS_ORIGINS
           value: https://yourdomain.com
   ```

2. 推送到 GitHub 并连接 Render

#### 部署到 VPS（阿里云、腾讯云等）

1. 购买服务器并安装 Docker
2. SSH 登录服务器
3. 按照上面的 "使用 Docker 快速部署" 步骤操作
4. 配置防火墙（安全组）：
   - 开放 22 端口（SSH）
   - 开放 80 端口（HTTP）
   - 开放 443 端口（HTTPS）
   - 开放 8000 端口（应用，可选）

### 监控与维护

**查看日志：**
```bash
docker-compose logs -f app
```

**更新应用：**
```bash
git pull
docker-compose down
docker-compose up -d --build
```

**备份数据：**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz output/
```

**查看资源使用：**
```bash
docker stats
```

---

## Environment Variables | 环境变量

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API 密钥 |
| `SEMANTIC_SCHOLAR_API_KEY` | No | - | Semantic Scholar API |
| `SERPER_API_KEY` | No | - | Serper 图片搜索 |
| `UNSPLASH_ACCESS_KEY` | No | - | Unsplash 图片 |
| `CORS_ORIGINS` | No | `*` | 允许的跨域来源 |
| `ENABLE_IMAGES` | No | `true` | 启用图片功能 |
| `MAX_IMAGES_PER_PAPER` | No | `3` | 每篇论文最大图片数 |

---

## Troubleshooting | 故障排除

### 端口被占用
```bash
# 查看占用 8000 端口的进程
sudo lsof -i :8000
# 终止进程
sudo kill -9 <PID>
```

### 权限问题
```bash
# 修复 output 目录权限
sudo chown -R 1000:1000 output/
```

### 内存不足
```bash
# 添加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```
