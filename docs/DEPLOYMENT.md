# 部署指南

**版本**: 2.0  
**日期**: 2026-03-06

---

## 系统要求

| 项目 | 要求 |
|------|------|
| Python | 3.12+ |
| 内存 | 2GB+ |
| 磁盘 | 10GB+ |
| 网络 | 稳定的互联网连接 |

---

## 快速部署

### 1. 克隆仓库

```bash
git clone https://github.com/unlimblue/ai-toolbox.git
cd ai-toolbox
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -e .
```

### 4. 配置环境变量

```bash
mkdir -p ~/.openclaw/secrets
cat > ~/.openclaw/secrets/cyber_dynasty_tokens.env << 'EOF'
# Discord Bot Tokens (从 Discord Developer Portal 获取)
HUB_BOT_TOKEN=your_hub_bot_token
CHENGXIANG_BOT_TOKEN=your_chengxiang_bot_token
TAIWEI_BOT_TOKEN=your_taiwei_bot_token

# AI Provider API Key
KIMI_API_KEY=your_kimi_api_key
EOF
```

### 5. 启动服务

```bash
./scripts/multi_bot.sh start
```

### 6. 检查状态

```bash
./scripts/multi_bot.sh status
```

---

## Discord Bot 配置

### 1. 创建 Discord 应用

1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application"
3. 命名你的应用（如 "赛博王朝"）

### 2. 创建 Bot

1. 进入 "Bot" 标签
2. 点击 "Add Bot"
3. 复制 Token（保存好，只显示一次）

### 3. 邀请 Bot 到服务器

1. 进入 "OAuth2" → "URL Generator"
2. 选择 Scopes: `bot`
3. 选择 Bot Permissions:
   - Send Messages
   - Read Message History
   - Mention Everyone
   - View Channels
4. 复制生成的 URL，在浏览器中打开
5. 选择你的服务器，授权

### 4. 获取频道 ID

1. 在 Discord 中开启开发者模式（设置 → 高级）
2. 右键点击频道 → "复制频道 ID"
3. 更新 `config/multi_bot.yaml` 中的频道配置

---

## 服务管理

### 启动服务

```bash
./scripts/multi_bot.sh start
```

### 停止服务

```bash
./scripts/multi_bot.sh stop
```

### 重启服务

```bash
./scripts/multi_bot.sh restart
```

### 查看状态

```bash
./scripts/multi_bot.sh status
```

### 查看日志

```bash
./scripts/multi_bot.sh logs
# 或
./scripts/multi_bot.sh logs -f  # 实时跟踪
```

---

## Systemd 部署（生产环境）

### 1. 复制服务文件

```bash
sudo cp scripts/cyber-dynasty.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. 启动服务

```bash
sudo systemctl start cyber-dynasty
sudo systemctl enable cyber-dynasty  # 开机自启
```

### 3. 查看状态

```bash
sudo systemctl status cyber-dynasty
```

---

## 故障排查

### Bot 无法连接

**症状**: 日志显示连接失败

**排查**:
1. 检查 Token 是否正确
2. 检查网络连接
3. 检查 Discord API 状态

```bash
# 测试 Token
curl -H "Authorization: Bot YOUR_TOKEN" \
  https://discord.com/api/v10/users/@me
```

### AI 无响应

**症状**: Bot 在线但不回复

**排查**:
1. 检查 Kimi API Key
2. 检查日志中的错误信息
3. 确认 Bot 被 @ 或频道配置正确

```bash
# 检查 API Key
echo $KIMI_API_KEY
```

### 上下文不连贯

**症状**: Bot 忘记之前的对话

**排查**:
1. 检查 ContextGraph 是否正确存储
2. 检查可见性计算是否正确
3. 查看 debug 日志

---

## 更新部署

### 更新代码

```bash
git pull origin main
./scripts/multi_bot.sh restart
```

### 更新依赖

```bash
pip install -e . --upgrade
./scripts/multi_bot.sh restart
```

---

## 备份与恢复

### 备份配置

```bash
cp config/multi_bot.yaml config/multi_bot.yaml.backup
cp ~/.openclaw/secrets/cyber_dynasty_tokens.env ~/secrets.backup
```

### 恢复配置

```bash
cp config/multi_bot.yaml.backup config/multi_bot.yaml
cp ~/secrets.backup ~/.openclaw/secrets/cyber_dynasty_tokens.env
./scripts/multi_bot.sh restart
```

---

*文档版本: 2.0 | 最后更新: 2026-03-06*
