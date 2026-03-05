# Cyber Dynasty Multi-Bot System - Debug Mode Implementation Plan

## 实施日期
2026-03-05

## 目标
为 Multi-Bot 系统实现 Debug 模式，在金銮殿频道实时回显系统日志，便于排查问题。

---

## 方案概述 (Option B: 虚拟作者ID)

### 核心设计
使用虚拟作者ID标识调试消息，让下游 Bot 识别并忽略，避免影响正常对话上下文。

---

## 详细实现

### 1. 配置新增

**文件**: `src/ai_toolbox/multi_bot/config.py`

```python
# Debug Mode Configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEBUG_CHANNEL_ID = os.getenv("DEBUG_CHANNEL_ID", "1478759781425745940")  # 金銮殿
DEBUG_AUTHOR_ID = "__DEBUG_BOT__"  # 虚拟作者ID，Bot 会忽略此ID的消息
DEBUG_PREFIX = "🔍 [DEBUG]"
```

**环境变量配置** (`~/.openclaw/secrets/cyber_dynasty_tokens.env`):

```bash
# Debug Mode
DEBUG_MODE=true
DEBUG_CHANNEL_ID=1478759781425745940
```

---

### 2. Hub Listener 增强

**文件**: `src/ai_toolbox/multi_bot/hub_listener.py`

#### 2.1 初始化时获取调试频道

```python
class HubListener:
    def __init__(self, token: str, on_message: Callable, on_error: Optional[Callable] = None):
        # ... existing code ...
        
        # Debug mode setup
        self.debug_mode = DEBUG_MODE
        self.debug_channel_id = DEBUG_CHANNEL_ID
        self._debug_channel: Optional[discord.TextChannel] = None
        
    async def _get_debug_channel(self) -> Optional[discord.TextChannel]:
        """Get debug channel for logging."""
        if not self.debug_mode or not self.debug_channel_id:
            return None
        
        if self._debug_channel is None:
            self._debug_channel = self.client.get_channel(int(self.debug_channel_id))
        
        return self._debug_channel
    
    async def send_debug_message(self, content: str, extra_data: dict = None):
        """
        Send debug message to debug channel.
        
        Args:
            content: Debug message content
            extra_data: Additional data to include (msg_id, mentions, etc.)
        """
        if not self.debug_mode:
            return
        
        channel = await self._get_debug_channel()
        if not channel:
            return
        
        # Format debug message
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        debug_msg = f"{DEBUG_PREFIX} [{timestamp}] {content}"
        
        # Add extra data if provided
        if extra_data:
            debug_msg += f"\n  📋 Data: {extra_data}"
        
        try:
            await channel.send(debug_msg)
        except Exception as e:
            logger.error(f"Failed to send debug message: {e}")
```

#### 2.2 消息处理时发送调试信息

```python
@self.client.event
async def on_message(message: discord.Message):
    """Called when a message is received."""
    # Ignore own messages and debug messages
    if message.author.id == self.client.user.id:
        return
    
    # Ignore debug messages (prevent loop)
    if str(message.author.id) == DEBUG_AUTHOR_ID:
        return
    
    try:
        # Debug: Log received message
        if self.debug_mode:
            mentions_list = [f"@{m.name}" for m in message.mentions]
            await self.send_debug_message(
                f"📨 Message Received",
                {
                    "id": str(message.id),
                    "author": message.author.name,
                    "content": message.content[:100],
                    "channel": message.channel.name,
                    "mentions": mentions_list,
                    "is_bot": message.author.bot
                }
            )
        
        # Process message
        await self.on_message_callback(message)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        if self.debug_mode:
            await self.send_debug_message(
                f"❌ Error processing message: {str(e)}",
                {"error_type": type(e).__name__}
            )
```

---

### 3. Message Bus 增强

**文件**: `src/ai_toolbox/multi_bot/message_bus.py`

```python
class MessageBus:
    def __init__(self, config=None, debug_sender: Optional[Callable] = None):
        # ... existing code ...
        self.debug_sender = debug_sender  # Callback to send debug messages
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message if debug sender is available."""
        if self.debug_sender:
            await self.debug_sender(content, data)
    
    async def publish(self, message: UnifiedMessage):
        """Publish a message to the bus."""
        # Debug: Log publishing
        await self._send_debug(
            f"📤 Publishing Message",
            {
                "id": message.id,
                "author": message.author_name,
                "content": message.content[:100],
                "channel": message.channel_id,
                "mentions": message.mentions
            }
        )
        
        # ... rest of existing code ...
        
        # Check for cross-channel task
        task = self._parse_cross_channel_task(message)
        if task:
            self.active_tasks[task.task_id] = task
            await self._send_debug(
                f"🎯 Cross-Channel Task Created",
                {
                    "task_id": task.task_id,
                    "source": task.source_channel,
                    "target": task.target_channel,
                    "target_bots": task.target_bots,
                    "instruction": task.instruction[:100]
                }
            )
            
            # Notify target bots
            for bot_id in task.target_bots:
                if bot_id in self.role_bots:
                    try:
                        await self._send_debug(
                            f"📋 Notifying Bot: {bot_id}",
                            {"task_id": task.task_id}
                        )
                        await self.role_bots[bot_id].handle_task(task)
                    except Exception as e:
                        await self._send_debug(
                            f"❌ Failed to notify bot {bot_id}",
                            {"error": str(e)}
                        )
        
        # Distribute to relevant bots
        await self._distribute_message(message)
    
    async def _distribute_message(self, message: UnifiedMessage):
        """Distribute message to relevant bots."""
        channel_bots = self.channel_map.get(message.channel_id, [])
        target_bots = set(channel_bots + message.mentions)
        
        await self._send_debug(
            f"📨 Distributing to {len(target_bots)} bots",
            {"bots": list(target_bots)}
        )
        
        for bot_id in target_bots:
            if bot_id not in self.role_bots:
                continue
            
            if self._should_deliver(bot_id, message):
                try:
                    await self._send_debug(
                        f"➡️ Delivering to {bot_id}",
                        {"message_id": message.id}
                    )
                    await self.role_bots[bot_id].handle_message(message)
                except Exception as e:
                    await self._send_debug(
                        f"❌ Failed to deliver to {bot_id}",
                        {"error": str(e)}
                    )
```

---

### 4. Role Bot 增强

**文件**: `src/ai_toolbox/multi_bot/role_bot.py`

```python
class RoleBot:
    def __init__(self, config: BotConfig, debug_sender: Optional[Callable] = None):
        # ... existing code ...
        self.debug_sender = debug_sender
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message."""
        if self.debug_sender:
            await self.debug_sender(f"[{self.bot_id}] {content}", data)
    
    async def handle_task(self, task: CrossChannelTask):
        """Handle cross-channel task."""
        await self._send_debug(
            f"🤖 Handling Task",
            {"task_id": task.task_id, "state": self.state.value}
        )
        
        # ... existing code ...
        
        # Ensure connected
        if not self._connected:
            await self._send_debug("🔌 Connecting to Discord...")
            await self.connect()
        
        # Send confirmation
        await self._send_debug(
            f"📤 Sending confirmation to source channel",
            {"channel": task.source_channel}
        )
        await self.send_message(task.source_channel, "领旨，即刻去内阁商议。")
        
        # Send start message
        await self._send_debug(
            f"📤 Sending start message to target channel",
            {"channel": task.target_channel}
        )
        await self.send_message(task.target_channel, f"奉陛下旨意，来此商议：{task.instruction}")
    
    async def send_message(self, channel_id: str, content: str):
        """Send message to channel."""
        # ... existing code ...
        
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.send(content)
                await self._send_debug(
                    f"✅ Message sent",
                    {"channel": channel_id, "content": content[:50]}
                )
            else:
                await self._send_debug(
                    f"❌ Channel not found",
                    {"channel": channel_id}
                )
        except Exception as e:
            await self._send_debug(
                f"❌ Failed to send message",
                {"channel": channel_id, "error": str(e)}
            )
```

---

### 5. Context Filter 增强

**文件**: `src/ai_toolbox/multi_bot/context_filter.py`

```python
class ContextFilter:
    def _is_relevant(self, message: UnifiedMessage) -> bool:
        """Check if message is relevant to this bot."""
        # Ignore debug messages (identified by author_id or content prefix)
        if message.author_id == DEBUG_AUTHOR_ID:
            return False
        
        if message.content.startswith(DEBUG_PREFIX):
            return False
        
        # ... existing logic ...
```

---

### 6. Main 入口更新

**文件**: `src/ai_toolbox/multi_bot/main.py`

```python
async def main():
    # ... existing code ...
    
    # Initialize Hub Listener
    hub = HubListener(
        token=os.getenv("HUB_BOT_TOKEN"),
        on_message=on_discord_message
    )
    
    # Connect debug sender
    bus.debug_sender = hub.send_debug_message
    for bot in bus.role_bots.values():
        bot.debug_sender = hub.send_debug_message
    
    # ... rest of existing code ...
```

---

## 调试输出示例

### 用户发送跨频道指令

```
🔍 [DEBUG] [04:30:15.123] 📨 Message Received
  📋 Data: {'id': '1478956646876053536', 'author': '皇帝', 'content': '@丞相 @太尉，去内阁商议...', 'channel': '金銮殿', 'mentions': ['@丞相', '@太尉'], 'is_bot': False}

🔍 [DEBUG] [04:30:15.145] 📤 Publishing Message
  📋 Data: {'id': '1478956646876053536', 'author': '皇帝', 'content': '@丞相 @太尉，去内阁商议...', 'channel': '1478759781425745940', 'mentions': ['chengxiang', 'taiwei']}

🔍 [DEBUG] [04:30:15.167] 🎯 Cross-Channel Task Created
  📋 Data: {'task_id': 'xxx', 'source': '1478759781425745940', 'target': '1477312823817277681', 'target_bots': ['chengxiang', 'taiwei'], 'instruction': '@丞相 @太尉，去内阁商议...'}

🔍 [DEBUG] [04:30:15.189] 📋 Notifying Bot: chengxiang
  📋 Data: {'task_id': 'xxx'}

🔍 [DEBUG] [04:30:15.201] [chengxiang] 🤖 Handling Task
  📋 Data: {'task_id': 'xxx', 'state': 'idle'}

🔍 [DEBUG] [04:30:15.223] [chengxiang] 🔌 Connecting to Discord...

🔍 [DEBUG] [04:30:16.145] [chengxiang] 📤 Sending confirmation to source channel
  📋 Data: {'channel': '1478759781425745940'}

🔍 [DEBUG] [04:30:16.167] [chengxiang] ✅ Message sent
  📋 Data: {'channel': '1478759781425745940', 'content': '领旨，即刻去内阁商议。'}
```

---

## 删除 discord_bot 模块

### 删除文件列表

```
src/ai_toolbox/discord_bot/
├── README.md              ❌ DELETE
├── __init__.py            ❌ DELETE
├── bot.py                 ❌ DELETE
└── commands/
    ├── __init__.py        ❌ DELETE
    └── ai_commands.py     ❌ DELETE

tests/unit/discord_bot/    ❌ DELETE (if exists)
```

### 更新引用

- `pyproject.toml` - 移除 discord_bot entry point
- `README.md` - 更新文档，指向 multi_bot
- `AGENTS.md` - 更新说明

---

## 文件变更汇总

| 文件 | 操作 | 说明 |
|------|------|------|
| `config.py` | 修改 | 添加 DEBUG_MODE, DEBUG_CHANNEL_ID, DEBUG_AUTHOR_ID |
| `hub_listener.py` | 修改 | 添加调试消息发送功能 |
| `message_bus.py` | 修改 | 集成调试日志 |
| `role_bot.py` | 修改 | 集成调试日志 |
| `context_filter.py` | 修改 | 忽略调试消息 |
| `main.py` | 修改 | 连接调试发送器 |
| `discord_bot/` | 删除 | 整个目录删除 |
| `docs/debug_multi_bot.md` | 新增 | 本文档 |

---

## 测试计划

1. **单元测试**: 验证调试消息不被加入上下文
2. **集成测试**: 验证调试消息正确发送到金銮殿
3. **端到端测试**: 验证整个流程的调试输出

---

## 注意事项

1. **Token 安全**: DEBUG_MODE 仅在测试环境开启
2. **消息量**: 调试消息较多，生产环境必须关闭
3. **上下文隔离**: 确保调试消息绝不流入 Bot 上下文
4. **循环避免**: 调试消息本身不触发新的调试消息

---

*方案已细化，等待陛下指示执行。*