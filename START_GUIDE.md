# 一键启动指南 | Quick Start Guide

## 快速开始

### 1. 首次使用 - 安装依赖

双击运行：
```
install.bat
```

这会：
- ✅ 检查 Python 和 Node.js
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖
- ✅ 安装前端依赖
- ✅ 创建 .env 配置文件

### 2. 配置 API 密钥

编辑 `.env` 文件，填入你的 API 密钥：
```env
ANTHROPIC_API_KEY=your_claude_api_key_here
```

### 3. 一键启动

双击运行：
```
start.bat
```

或 PowerShell 版本（功能更强）：
```powershell
# 直接启动
.\start.ps1

# 或带参数
.\start.ps1 start    # 启动服务
.\start.ps1 stop     # 停止服务
.\start.ps1 restart  # 重启服务
.\start.ps1 status   # 查看状态
```

---

## 启动方式对比

| 方式 | 特点 | 推荐度 |
|------|------|--------|
| `start.bat` | 最简单，双击启动 | ⭐⭐⭐ |
| `start.ps1` | 支持交互菜单，功能丰富 | ⭐⭐⭐⭐⭐ |
| `docker-compose up` | 生产环境部署 | ⭐⭐⭐⭐ |

---

## 访问地址

启动成功后：
- 🌐 **前端界面**: http://localhost:5173
- 🔌 **API 接口**: http://localhost:8000

---

## 常见问题

### 端口被占用
```powershell
# 在 PowerShell 中查看占用端口的进程
Get-NetTCPConnection -LocalPort 8000
Get-NetTCPConnection -LocalPort 5173

# 使用 start.ps1 可以自动检测并处理
.\start.ps1 restart
```

### 关闭所有服务
- 关闭启动脚本打开的窗口
- 或运行：`.\start.ps1 stop`

### 更新代码后
```bash
git pull
.\start.ps1 restart
```

---

## PowerShell 交互菜单

运行 `.\start.ps1` 后可以使用交互菜单：

```
[1] 启动服务
[2] 停止服务
[3] 重启服务
[4] 刷新状态
[0] 退出
```

---

## 生产环境部署

生产环境建议使用 Docker：
```bash
docker-compose up -d
```

详见 [DEPLOY.md](DEPLOY.md) 和 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md)
