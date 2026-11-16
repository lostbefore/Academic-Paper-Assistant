# 阿里云 Windows 服务器部署指南

## 方案一：Docker Desktop 部署（推荐）

### 1. 安装 Docker Desktop
```powershell
# 下载 Docker Desktop for Windows
# 访问 https://www.docker.com/products/docker-desktop 下载安装包
# 或使用 Chocolatey
choco install docker-desktop
```

安装完成后重启服务器。

### 2. 部署步骤
```powershell
# 克隆项目
git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
cd Academic-Paper-Assistant

# 创建 .env 文件
notepad .env
```

**.env 内容：**
```env
ANTHROPIC_API_KEY=your_claude_api_key
SEMANTIC_SCHOLAR_API_KEY=your_key
SERPER_API_KEY=your_key
UNSPLASH_ACCESS_KEY=your_key
CORS_ORIGINS=http://你的服务器公网IP:8000,http://localhost:8000
```

```powershell
# 启动服务
docker-compose up -d
```

### 3. 配置阿里云安全组
登录阿里云控制台 → 安全组 → 添加规则：
- 入方向：允许 8000 端口（应用访问）
- 入方向：允许 80/443 端口（HTTP/HTTPS）
- 入方向：允许 3389 端口（远程桌面，已默认）

---

## 方案二：原生部署（无 Docker）

### 1. 安装 Python
```powershell
# 下载 Python 3.11
# https://www.python.org/downloads/release/python-3117/
# 安装时勾选 "Add Python to PATH"

# 验证
python --version
```

### 2. 安装 Node.js
```powershell
# 下载 Node.js 18 LTS
# https://nodejs.org/en/download/

# 验证
node --version
npm --version
```

### 3. 部署后端
```powershell
# 克隆项目
git clone https://github.com/lostbefore/Academic-Paper-Assistant.git
cd Academic-Paper-Assistant

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（系统环境变量）
# 控制面板 → 系统 → 高级系统设置 → 环境变量
# 添加：
# ANTHROPIC_API_KEY=your_key
# CORS_ORIGINS=http://你的公网IP:8000
```

### 4. 构建前端
```powershell
cd frontend
npm install
npm run build
cd ..
```

### 5. 启动服务（使用 NSSM 作为 Windows 服务）

```powershell
# 安装 NSSM（将 Python 脚本转为 Windows 服务）
# 下载 https://nssm.cc/download

# 创建启动脚本 start.bat
@echo off
.venv\Scripts\activate
python backend/api.py
```

```powershell
# 使用 NSSM 创建服务
nssm install AcademicPaperAssistant
# 在弹出的窗口中：
# Path: C:\path\to\Academic-Paper-Assistant\.venv\Scripts\python.exe
# Startup directory: C:\path\to\Academic-Paper-Assistant
# Arguments: backend/api.py

# 启动服务
nssm start AcademicPaperAssistant
```

---

## 方案三：IIS 反向代理（生产环境）

### 1. 安装 IIS
```powershell
# 使用 PowerShell 安装 IIS 和所需模块
Install-WindowsFeature -name Web-Server -IncludeManagementTools
Install-WindowsFeature -name Web-Http-Redirect
Install-WindowsFeature -name Web-Request-Monitor
```

### 2. 安装 ARR（Application Request Routing）
```powershell
# 下载安装 Web Platform Installer
# 通过 Web PI 安装 Application Request Routing 3.0
```

### 3. 配置反向代理
```
IIS 管理器 → 服务器 → Application Request Routing Cache → 右侧"服务器代理设置"
→ 勾选 "启用代理"

然后创建网站：
- 站点名称: PaperAssistant
- 物理路径: 前端 build 目录
- 端口: 80

添加 URL 重写规则：
- 模式: ^api/(.*)
- 重写为: http://localhost:8000/api/{R:1}
```

---

## 阿里云特定配置

### 安全组配置
必须开放的端口：

| 端口 | 用途 | 授权对象 |
|------|------|---------|
| 3389 | 远程桌面 | 你的IP |
| 8000 | 应用访问 | 0.0.0.0/0 |
| 80 | HTTP | 0.0.0.0/0 |
| 443 | HTTPS | 0.0.0.0/0 |

### 绑定域名
```
1. 购买域名并备案（国内服务器必需）
2. 添加 A 记录指向服务器公网IP
3. 在服务器配置 Web 服务器（IIS/Nginx）
```

### HTTPS 证书（阿里云 SSL）
```
1. 阿里云控制台 → SSL 证书 → 购买免费证书
2. 下载 Nginx/IIS 格式证书
3. 配置到 Web 服务器
```

---

## 维护命令

### Docker 方式
```powershell
# 查看日志
docker-compose logs -f

# 重启
docker-compose restart

# 更新
git pull
docker-compose down
docker-compose up -d --build
```

### 原生方式
```powershell
# 查看服务状态
nssm status AcademicPaperAssistant

# 重启服务
nssm restart AcademicPaperAssistant

# 停止服务
nssm stop AcademicPaperAssistant
```

---

## 常见问题

### 1. 防火墙拦截
```powershell
# 开放 8000 端口
New-NetFirewallRule -DisplayName "AcademicPaper" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### 2. 无法访问公网IP
- 检查阿里云安全组规则
- 检查 Windows 防火墙
- 确认服务正在运行：
```powershell
# 查看 8000 端口是否在监听
netstat -an | findstr 8000
```

### 3. 中文乱码
```powershell
# 设置 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### 4. 内存不足
建议阿里云服务器配置：
- 最低：2核4G（测试用）
- 推荐：4核8G（生产环境）

---

## 快速检查清单

- [ ] 阿里云安全组已开放 8000 端口
- [ ] Windows 防火墙已放行
- [ ] .env 文件已配置 API 密钥
- [ ] CORS_ORIGINS 包含公网IP
- [ ] 服务已启动
- [ ] 可以通过 `http://公网IP:8000` 访问

有问题请查看 DEPLOY.md 通用部署指南。
