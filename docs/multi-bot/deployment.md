# Cyber Dynasty Multi-Bot System - Deployment Guide

## 系统要求

- Linux (Ubuntu 20.04+ 推荐)
- Python 3.12+
- 2GB+ RAM
- 稳定的网络连接

---

## 安装步骤

### 1. 克隆代码

```bash
cd /root/.openclaw/workspace
git clone https://github.com/unlimblue/ai-toolbox.git
cd ai-toolbox
```

### 2. 创建虚拟环境

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. 配置 Token

创建 Token 文件：

```bash
mkdir -p ~/.openclaw/secrets
cat > ~/.openclaw/secrets/cyber_dynasty_tokens.env << 'EOF'
# Discord Bot Tokens
HUB_BOT_TOKEN=MTQ3ODIyMjg0OTgwOTU4NDI0OQ.xxxxx.xxxxxxxxxxxxx
CHENGXIANG_BOT_TOKEN=MTQ3NzMxNDM4NTcxMzAzNzQ0NQ.xxxxx.xxxxxxxxxxxxx
TAIWEI_BOT_TOKEN=MTQ3ODIxNjc3NDE3MTM2NTQ2Ng.xxxxx.xxxxxxxxxxxxx

# AI API Key
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
EOF
```

**重要**：设置正确的权限：

```bash
chmod 600 ~/.openclaw/secrets/cyber_dynasty_tokens.env
```

### 4. 运行测试

```bash
./scripts/multi_bot.sh test
```

---

## 启动方式

### 方式一：使用脚本（推荐开发/测试）

```bash
# 启动
./scripts/multi_bot.sh start

# 查看状态
./scripts/multi_bot.sh status

# 查看日志
./scripts/multi_bot.sh logs

# 停止
./scripts/multi_bot.sh stop

# 重启
./scripts/multi_bot.sh restart
```

### 方式二：使用 systemd（推荐生产环境）

```bash
# 复制服务文件
sudo cp scripts/cyber-dynasty.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用开机启动
sudo systemctl enable cyber-dynasty

# 启动服务
sudo systemctl start cyber-dynasty

# 查看状态
sudo systemctl status cyber-dynasty

# 查看日志
sudo journalctl -u cyber-dynasty -f

# 停止服务
sudo systemctl stop cyber-dynasty
```

### 方式三：直接运行（调试）

```bash
# 加载环境变量
export $(cat ~/.openclaw/secrets/cyber_dynasty_tokens.env | xargs)

# 启动
source .venv/bin/activate
python -m ai_toolbox.multi_bot.main
```

---

## 配置说明

### 频道配置

编辑 `src/ai_toolbox/multi_bot/config.py`：

```python
CHANNEL_CONFIGS = {
    "金銮殿": ChannelConfig(
        channel_id="1478759781425745940",
        name="金銮殿",
        description="皇帝召见群臣，商议国事",
        allowed_bots=["chengxiang", "taiwei"]
    ),
    "内阁": ChannelConfig(
        channel_id="1477312823817277681",
        name="内阁",
        description="内阁议事，商讨政策",
        allowed_bots=["chengxiang", "taiwei"]
    ),
    "兵部": ChannelConfig(
        channel_id="1477273291528867860",
        name="兵部",
        description="军事防务，安全事务",
        allowed_bots=["taiwei"]
    )
}
```

### Bot 配置

```python
DYNASTY_CONFIG.bots["chengxiang"] = BotConfig(
    bot_id="chengxiang",
    name="丞相",
    token_env="CHENGXIANG_BOT_TOKEN",
    model_provider="kimi",
    model_name="kimi-k2-5",
    api_key_env="KIMI_API_KEY",
    channels=["金銮殿", "内阁"],
    persona=BotPersona(...)
)
```

---

## 测试流程

### 1. 单元测试

```bash
pytest tests/unit/multi_bot/test_multi_bot.py -v
```

### 2. 集成测试

```bash
pytest tests/integration/test_cross_channel.py -v
```

### 3. 全部测试

```bash
./scripts/multi_bot.sh test
```

### 4. 端到端测试（需要真实环境）

```bash
# 启动服务
./scripts/multi_bot.sh start

# 在 Discord 中测试：
# 1. 在金銮殿 @丞相 @太尉，去内阁商议测试方案
# 2. 在内阁观察 Bot 对话
# 3. 等待结论汇报到金銮殿
```

---

## 监控与日志

### 日志位置

- 脚本方式：`logs/multi_bot_YYYYMMDD_HHMMSS.log`
- systemd方式：`journalctl -u cyber-dynasty`

### 关键日志检查

```bash
# 查看启动日志
tail -f logs/multi_bot_*.log | grep -E "(Starting|logged in|error|Error)"

# 查看消息处理
tail -f logs/multi_bot_*.log | grep -E "(Received|handling|sent)"

# 查看状态转换
tail -f logs/multi_bot_*.log | grep -E "(state|DISCUSSING|REPORTING|IDLE)"
```

### 健康检查

```bash
# 检查进程
ps aux | grep multi_bot

# 检查网络连接
netstat -tlnp | grep python

# 检查日志错误
grep -i error logs/multi_bot_*.log
```

---

## 故障排除

### 问题：Bot 无法连接

**症状**：日志显示 "Failed to start Hub Listener"

**解决**：
1. 检查 Token 是否正确
2. 检查网络连接
3. 验证 Token 权限：
```bash
curl -H "Authorization: Bot $HUB_BOT_TOKEN" \
  https://discord.com/api/v10/users/@me
```

### 问题：Token 泄露警告

**症状**：GitHub 阻止推送

**解决**：
1. 立即在 Discord Developer Portal 重置 Token
2. 更新环境变量文件
3. 重启服务

### 问题：消息不转发

**症状**：Hub 收到消息但 Bot 不响应

**检查**：
1. 检查频道 ID 配置
2. 检查 allowed_bots 列表
3. 查看 MessageBus 日志

### 问题：上下文不累积

**症状**：Bot 每次回复都像第一次对话

**检查**：
1. 检查 ContextFilter 是否正常工作
2. 检查 max_context 设置
3. 查看相关性评分日志

---

## 性能调优

### 上下文大小

```python
# 调整上下文窗口大小
context_filter = ContextFilter(bot_id=self.bot_id, max_context=20)  # 默认15
```

### 消息历史限制

```python
# 调整消息总线历史限制
self.max_history = 2000  # 默认1000
```

### 日志级别

```python
# 生产环境使用 WARNING
logging.basicConfig(level=logging.WARNING)

# 调试使用 DEBUG
logging.basicConfig(level=logging.DEBUG)
```

---

## 备份与恢复

### 备份配置

```bash
# 备份 Token 文件
cp ~/.openclaw/secrets/cyber_dynasty_tokens.env \
   ~/.openclaw/secrets/cyber_dynasty_tokens.env.backup

# 备份代码
git add -A
git commit -m "Backup before modification"
git push
```

### 恢复

```bash
# 从备份恢复 Token
cp ~/.openclaw/secrets/cyber_dynasty_tokens.env.backup \
   ~/.openclaw/secrets/cyber_dynasty_tokens.env

# 从 Git 恢复代码
git reset --hard HEAD
git pull
```

---

## 扩展指南

### 添加新 Bot

1. 在 Discord Developer Portal 创建新 Bot
2. 添加 Token 到环境变量文件
3. 在 `config.py` 中添加 BotConfig
4. 更新频道配置中的 allowed_bots
5. 重启服务

### 添加新频道

1. 在 Discord 创建频道
2. 获取频道 ID
3. 在 `config.py` 中添加 ChannelConfig
4. 更新相关 Bot 的 channels 列表
5. 重启服务

---

## 安全最佳实践

1. **绝不提交 Token 到 Git**
   ```bash
   # 确保 .gitignore 包含
   *.env
   .env
   secrets/
   ```

2. **定期更换 Token**
   - 建议每 3 个月更换一次

3. **限制 Bot 权限**
   - 只给予必要的频道权限
   - 不要给予管理员权限

4. **监控异常行为**
   - 定期检查日志
   - 设置告警机制

---

## 联系与支持

- **GitHub**: https://github.com/unlimblue/ai-toolbox
- **文档**: `docs/IMPLEMENTATION_COMPLETE.md`
- **测试**: `./scripts/multi_bot.sh test`