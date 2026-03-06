# Multi-Bot System 修复实施计划

**日期**: 2026-03-05  
**状态**: 方案细化完成，等待实施指示

---

## 当前问题总结

### 问题 1: mentions 为空
**现象**: 用户 @丞相 @太尉 后，`mentions` 列表为空  
**根因**: 用户使用角色 @ `<@&role_id>`，但代码只处理用户 mentions

### 问题 2: Bot 不在线
**现象**: Discord 客户端显示丞相、太尉 "不在线"  
**根因**: RoleBot 采用按需连接策略，只在收到任务时连接

### 问题 3: 跨频道任务未触发
**现象**: 用户指令未创建跨频道任务  
**根因**: 因为 mentions 为空，无法识别目标 Bot

---

## 实施方案

### 决策确认

| 决策项 | 选择 | 说明 |
|--------|------|------|
| @ 类型 | **仅支持 Bot 用户 @** | 不支持角色 @，用户需直接 @ Bot 账号 |
| 连接策略 | **启动时连接所有 Bot** | 保持持续在线状态 |
| 实施方式 | **一次性修复** | 所有问题一起修复，避免多次迭代 |

---

## 详细实施步骤

### Step 1: 更新 Token 文件说明

**文件**: `docs/DEPLOYMENT_GUIDE.md`

添加说明：
```markdown
## 使用说明

### @ 方式
- ✅ 支持：直接 @ Bot 用户（如 @丞相）
- ❌ 不支持：@ 角色（如 @丞相 角色）

### 启动流程
1. 启动时 Hub Bot 先连接
2. 然后丞相、太尉 Bot 同时连接
3. 所有 Bot 保持在线状态
```

---

### Step 2: 修改 Main 入口

**文件**: `src/ai_toolbox/multi_bot/main.py`

**变更**:
```python
async def main():
    # ... existing code ...
    
    # Initialize Hub Listener
    hub = HubListener(...)
    
    # Connect all bots at startup
    logger.info("Connecting all bots...")
    for bot_id, bot in bus.role_bots.items():
        try:
            await bot.connect()
            logger.info(f"Connected bot: {bot_id}")
            await hub.send_debug_message(
                f"🟢 Bot {bot_id} connected",
                {"status": "online"}
            )
        except Exception as e:
            logger.error(f"Failed to connect bot {bot_id}: {e}")
            await hub.send_debug_message(
                f"❌ Bot {bot_id} connection failed",
                {"error": str(e)}
            )
    
    # Start hub (this will block)
    try:
        await hub.start()
    except KeyboardInterrupt:
        # Disconnect all bots on shutdown
        for bot in bus.role_bots.values():
            await bot.disconnect()
```

**理由**: 
- 启动时连接所有 Bot
- 保持在线状态
- 优雅关闭时断开连接

---

### Step 3: 添加 Bot 在线状态检测

**文件**: `src/ai_toolbox/multi_bot/role_bot.py`

**变更**:
```python
async def connect(self):
    """Connect to Discord."""
    if self._connected:
        return
    
    if not self.token:
        raise ValueError(f"No token for bot {self.bot_id}")
    
    self._client = discord.Client(intents=discord.Intents.default())
    
    # Add on_ready event to confirm connection
    @self._client.event
    async def on_ready():
        logger.info(f"Bot {self.bot_id} logged in as {self._client.user}")
        await self._send_debug(
            f"🟢 Bot online: {self._client.user}",
            {"user_id": str(self._client.user.id)}
        )
    
    await self._client.start(self.token)  # Use start() instead of login()
    self._connected = True
```

**注意**: 需要使用 `start()` 而非 `login()` 来启动事件循环

---

### Step 4: 处理 Bot 账号 @

**文件**: `src/ai_toolbox/multi_bot/hub_listener.py`

**当前代码**:
```python
for mention in message.mentions:
    discord_id = str(mention.id)
    if discord_id in DISCORD_ID_TO_BOT_ID:
        mentions.append(DISCORD_ID_TO_BOT_ID[discord_id])
```

**需要确认**: 
- `DISCORD_ID_TO_BOT_ID` 已包含 Bot 用户 ID 映射
- 当前配置:
  ```python
  DISCORD_ID_TO_BOT_ID = {
      "1477314385713037445": "chengxiang",  # 丞相用户ID
      "1478216774171365466": "taiwei",     # 太尉用户ID
  }
  ```

**无需修改代码**，但需要在文档中明确告诉用户：
> 请直接 @ Bot 用户（丞相/太尉），不要 @ 角色

---

### Step 5: 修复 MessageBus 分发逻辑（已完成）

**状态**: ✅ 已修复  
**文件**: `src/ai_toolbox/multi_bot/message_bus.py`

**修复内容**:
```python
if message.mentions:
    # Only deliver to mentioned bots
    target_bots = set(message.mentions)
else:
    # Deliver to all channel bots
    target_bots = set(channel_bots)
```

---

## 测试方案

### 测试 1: Bot 启动连接测试

**目的**: 验证启动时所有 Bot 都连接

**测试代码**:
```python
@pytest.mark.asyncio
async def test_bots_connect_at_startup():
    """Test that all bots connect at startup."""
    bus = MessageBus()
    
    # Create mock bots
    mock_chengxiang = Mock()
    mock_chengxiang.config.bot_id = "chengxiang"
    mock_chengxiang.connect = AsyncMock()
    
    mock_taiwei = Mock()
    mock_taiwei.config.bot_id = "taiwei"
    mock_taiwei.connect = AsyncMock()
    
    bus.register_bot(mock_chengxiang)
    bus.register_bot(mock_taiwei)
    
    # Simulate startup connection
    for bot in bus.role_bots.values():
        await bot.connect()
    
    # Verify all bots connected
    mock_chengxiang.connect.assert_called_once()
    mock_taiwei.connect.assert_called_once()
```

---

### 测试 2: Bot 在线状态检测

**目的**: 验证 Bot 连接后显示在线

**测试代码**:
```python
@pytest.mark.asyncio
async def test_bot_online_status():
    """Test that bot reports online status after connection."""
    bot = RoleBot(config)
    
    with patch.object(bot, '_client') as mock_client:
        mock_client.user = Mock()
        mock_client.user.id = "1477314385713037445"
        mock_client.user.name = "丞相"
        
        # Mock the event trigger
        await bot._on_ready()  # Simulate on_ready event
        
        # Verify debug message sent
        bot.debug_sender.assert_called_with(
            "🟢 Bot online: 丞相",
            {"user_id": "1477314385713037445"}
        )
```

---

### 测试 3: 用户 @ Bot 识别

**目的**: 验证直接 @ Bot 用户能正确识别

**测试代码**:
```python
def test_user_mention_recognition():
    """Test that user mentions are correctly converted to bot_ids."""
    # Create mock Discord message with user mention
    mock_message = Mock()
    mock_message.mentions = [Mock(id=1477314385713037445)]  # 丞相用户ID
    mock_message.role_mentions = []  # No role mentions
    
    unified = discord_message_to_unified(mock_message)
    
    assert "chengxiang" in unified.mentions
```

---

### 测试 4: 角色 @ 不识别（验证决策）

**目的**: 验证角色 @ 不会被识别

**测试代码**:
```python
def test_role_mention_not_recognized():
    """Test that role mentions are NOT converted to bot_ids."""
    mock_message = Mock()
    mock_message.mentions = []  # No user mentions
    mock_message.role_mentions = [Mock(id=1477314769764614239)]  # 丞相角色ID
    
    unified = discord_message_to_unified(mock_message)
    
    assert "chengxiang" not in unified.mentions  # Should NOT be recognized
    assert len(unified.mentions) == 0
```

---

### 测试 5: 端到端流程测试

**目的**: 验证完整流程

**手动测试步骤**:

1. **启动服务**
   ```bash
   ./scripts/multi_bot.sh start
   ```

2. **验证所有 Bot 在线**
   - Discord 中查看丞相、太尉是否显示在线
   - 金銮殿应显示调试消息：
     ```
     🔍 [DEBUG] [xx:xx:xx.xxx] 🟢 Bot chengxiang connected
     🔍 [DEBUG] [xx:xx:xx.xxx] 🟢 Bot taiwei connected
     ```

3. **测试 @ Bot 用户**
   - 在金銮殿发送：`@丞相 你好`
   - 预期：
     - 丞相收到消息
     - 太尉不收到
     - 丞相回复

4. **测试 @ Bot 用户（多个）**
   - 在金銮殿发送：`@丞相 @太尉 去内阁商议`
   - 预期：
     - 两人都收到
     - 两人都回复确认
     - 创建跨频道任务

5. **测试 @ 角色（应无效）**
   - 在金銮殿发送：`@丞相（角色） 你好`
   - 预期：
     - 没有人收到（因为只支持用户 @）
     - 调试信息显示 `mentions: []`

---

## 实施顺序

| 顺序 | 步骤 | 文件 | 预计时间 |
|------|------|------|----------|
| 1 | 修改 main.py | `main.py` | 30分钟 |
| 2 | 修改 role_bot.py | `role_bot.py` | 30分钟 |
| 3 | 更新文档 | `DEPLOYMENT_GUIDE.md` | 20分钟 |
| 4 | 编写测试 | `test_multi_bot.py` | 40分钟 |
| 5 | 运行测试 | - | 10分钟 |
| 6 | 重启服务 | - | 5分钟 |
| **总计** | | | **约2.5小时** |

---

## 风险与回滚

### 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Bot 连接失败 | 低 | 高 | 添加重试机制，调试日志 |
| Token 错误 | 低 | 高 | 启动前验证 |
| 并发问题 | 中 | 中 | 使用 asyncio 锁 |

### 回滚方案

```bash
# 如果出现问题，快速回滚到上一版本
git reset --hard a36acbb  # 回滚到修复前版本
./scripts/multi_bot.sh restart
```

---

## 验证清单

实施完成后检查：

- [ ] 所有 45+ 个测试通过
- [ ] Discord 显示丞相、太尉在线
- [ ] 金銮殿显示所有 Bot 连接调试信息
- [ ] @丞相 只有丞相响应
- [ ] @丞相 @太尉 两人都响应
- [ ] @角色 无人响应（符合预期）
- [ ] 跨频道指令正常工作

---

*方案已细化，等待陛下指示实施。*