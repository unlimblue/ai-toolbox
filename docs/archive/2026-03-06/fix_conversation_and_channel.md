# Multi-Bot System 问题修复方案

**日期**: 2026-03-05  
**问题**: 
1. Bot 相互 @ 不能持续，仅一轮就结束
2. Bot 不能识别"内阁"、"兵部"等频道名称

---

## 问题 1: Bot 相互 @ 不能持续

### 根因分析

**现象**: 丞相 @太尉 → 太尉回复 → 对话结束

**日志分析**:
```
07:28:34 丞相被 @，回复: "<@&1478217215936430092>，太尉大人安好..."
07:28:46 太尉被 @，回复: "<@&1477314769764614239>，太尉在此..."
07:28:55 对话结束
```

**问题**: 
1. **上下文过滤太严格**: `ContextFilter._is_relevant()` 只保留最近 5 分钟内的消息
2. **响应触发条件有限**: `_should_respond()` 只在被 @ 时响应，不会主动继续对话
3. **没有对话状态追踪**: Bot 不知道当前是否在持续对话中

### 解决方案

#### A. 放宽上下文时间窗口

```python
# context_filter.py
class ContextFilter:
    def __init__(self, bot_id: str, max_context: int = 15):
        # ...
        self.conversation_timeout = timedelta(minutes=10)  # 从 5 分钟延长到 10 分钟
    
    def _is_relevant(self, message: UnifiedMessage) -> bool:
        # ...
        # 如果是被 @，总是相关
        if self.bot_id in message.mentions:
            return True
        
        # 如果正在对话中（最近被 @ 过），放宽时间限制
        if self._in_active_conversation():
            return True
        
        # 常规时间检查（延长到10分钟）
        if time_diff < self.conversation_timeout:
            return True
```

#### B. 添加对话状态追踪

```python
# role_bot.py
class RoleBot:
    def __init__(self, ...):
        # ...
        self.conversation_state = {
            "active": False,
            "started_at": None,
            "last_message_at": None,
            "partners": [],  # 正在对话的 Bot
            "channel": None,
        }
    
    def _update_conversation_state(self, message: UnifiedMessage):
        """更新对话状态"""
        if self.bot_id in message.mentions:
            # 被 @ 了，激活对话状态
            self.conversation_state["active"] = True
            self.conversation_state["last_message_at"] = datetime.now()
            self.conversation_state["channel"] = message.channel_id
            
            # 记录对话伙伴
            for mention in message.mentions:
                if mention != self.bot_id and mention not in self.conversation_state["partners"]:
                    self.conversation_state["partners"].append(mention)
    
    def _should_respond(self, message: UnifiedMessage) -> bool:
        # 被 @ 时一定响应
        if self.bot_id in message.mentions:
            return True
        
        # 如果在活跃对话中，且对方是已知的 Bot，继续响应
        if self.conversation_state["active"]:
            # 检查是否是对话伙伴的消息
            if message.author_id in self.conversation_state["partners"]:
                return True
            
            # 检查对话是否超时（2分钟无消息则结束）
            if self._is_conversation_active():
                return True
        
        return False
    
    def _is_conversation_active(self) -> bool:
        """检查对话是否仍在活跃"""
        if not self.conversation_state["active"]:
            return False
        
        last = self.conversation_state.get("last_message_at")
        if last:
            # 2 分钟内有人说话，保持活跃
            return datetime.now() - last < timedelta(minutes=2)
        
        return False
```

#### C. AI 提示词引导持续对话

```python
# 在 system prompt 中添加持续对话指导
CONVERSATION_GUIDE = """
## 🔄 持续对话规则

当你被 @ 时：
1. **必须响应** - 回复对方的 @
2. **可以继续 @ 对方** - 如果你想继续讨论，在回复中再次 @ 对方
3. **对话终止条件** - 只有当以下情况才停止 @：
   - 对方明确表示结束（如"就这样吧"、"先这样吧"）
   - 你已经表达完整意见，且不需要对方回应
   - 超过 2 轮对话仍无结论，可以总结后结束

**示例 - 持续对话**:
```
丞相: @太尉，此事如何？
太尉: @丞相，我觉得可行，但需完善细节。你认为呢？
丞相: @太尉，善。那我们就此定论？
太尉: @丞相，可。
```

**示例 - 结束对话**:
```
丞相: @太尉，此事如何？
太尉: @丞相，可行。结论：采用方案A。
丞相: 善。（不再 @，对话结束）
```
"""
```

---

## 问题 2: 频道名称识别

### 根因分析

**现象**: Bot 不理解"内阁"、"兵部"指的是哪个频道

**日志分析**:
```
07:29:45 用户: "叫上太尉，去内阁相互问候"
07:29:46 创建了跨频道任务，target_channel="1477312823817277681" (内阁)
```

**问题**:
1. **频道名称映射只在代码中**: Bot 知道 `channel_id`，但不理解"内阁"这个词
2. **System Prompt 缺少频道名称对照表**
3. **AI 无法将自然语言映射到 channel_id**

### 解决方案

#### A. 在 System Prompt 中添加频道名称对照

```python
# architecture_builder.py

def _build_channels_info(config: MultiBotConfig) -> str:
    """构建详细的频道信息"""
    lines = []
    
    for channel_key, channel_config in config.channels.items():
        lines.append(
            f"\n### {channel_config.get('name')} ({channel_key})"
            f"\n- **显示名称**: {channel_config.get('name')}"
            f"\n- **配置键**: `{channel_key}`"
            f"\n- **频道ID**: `{channel_config.get('id')}`"
            f"\n- **用途**: {channel_config.get('description', '')}"
            f"\n- **谁可以使用**: {', '.join(channel_config.get('allowed_bots', []))}"
        )
    
    return "\n".join(lines)


# 添加到 SYSTEM_PROMPT_TEMPLATE
CHANNEL_USAGE_GUIDE = """
## 📍 频道使用指南

可用频道列表:
{channels_info}

### 如何选择频道

当你听到以下词语时，对应到正确的频道：

| 用户说的 | 对应的频道配置键 | 频道ID |
|---------|----------------|--------|
| 金銮殿、大殿、朝堂 | `jinluan` | `1478759781425745940` |
| 内阁、议事厅、商议处 | `neige` | `1477312823817277681` |
| 兵部、军事部、防务处 | `bingbu` | `1477273291528867860` |

### 频道选择规则

1. **听指令**: 如果用户明确说"去XX"，就去对应的频道
2. **根据内容**: 
   - 军事话题 → 兵部
   - 政策商议 → 内阁
   - 汇报皇帝 → 金銮殿
3. **多人讨论**: 如果涉及多个 Bot 讨论，优先去内阁

### 如何切换频道

**示例 1 - 用户指定频道**:
```
用户: "去内阁商议"
你: <@&太尉角色ID>，我们去内阁商议。
然后在内阁频道发言。
```

**示例 2 - 自主决定切换**:
```
用户: "讨论军事部署"
你: <@&太尉角色ID>，此事涉及军事，我们去兵部详谈。
然后在兵部频道发言。
```
"""
```

#### B. 添加频道名称解析工具

```python
# architecture_builder.py

CHANNEL_NAME_ALIASES = {
    # 金銮殿
    "金銮殿": "jinluan",
    "大殿": "jinluan",
    "朝堂": "jinluan",
    "皇帝殿": "jinluan",
    # 内阁
    "内阁": "neige",
    "议事厅": "neige",
    "商议处": "neige",
    "议事堂": "neige",
    # 兵部
    "兵部": "bingbu",
    "军事部": "bingbu",
    "防务处": "bingbu",
    "军部": "bingbu",
}


def resolve_channel_name(text: str, config: MultiBotConfig) -> Optional[str]:
    """
    从文本中解析频道名称
    
    Args:
        text: 用户输入文本
        config: 配置对象
        
    Returns:
        频道配置键，或 None
    """
    # 直接匹配别名
    for alias, channel_key in CHANNEL_NAME_ALIASES.items():
        if alias in text:
            return channel_key
    
    # 模糊匹配（可选）
    # TODO: 使用更智能的匹配
    
    return None


def build_channel_resolution_prompt(config: MultiBotConfig) -> str:
    """构建频道识别指导"""
    aliases_text = "\n".join([
        f"- '{alias}' → `{channel_key}` ({config.channels[channel_key]['name']})"
        for alias, channel_key in CHANNEL_NAME_ALIASES.items()
        if channel_key in config.channels
    ])
    
    return f"""
## 🎯 频道名称识别速查

当你看到以下词语时，去对应的频道：

{aliases_text}

**重要**: 
- 用户说"去内阁"，你要去 `neige` 频道
- 用户说"去兵部"，你要去 `bingbu` 频道
- 用 `format_channel_id("jinluan")` 获取真实频道ID
"""
```

#### C. 在 RoleBot 中添加频道解析方法

```python
# role_bot.py

class RoleBot:
    def resolve_channel_from_text(self, text: str) -> Optional[str]:
        """从文本中解析频道 ID"""
        from .architecture_builder import resolve_channel_name
        
        channel_key = resolve_channel_name(text, get_config())
        if channel_key:
            return get_config().resolve_channel_id(channel_key)
        
        return None
    
    async def _decide_action(self, context: dict) -> dict:
        """决策时考虑频道选择"""
        message = context.get("message", "")
        
        # 解析用户指定的频道
        target_channel = self.resolve_channel_from_text(message)
        
        if target_channel:
            # 用户指定了频道
            return {
                "type": "discuss",
                "target_channel": target_channel,
                "message": self.format_message_with_mentions(
                    "{target_bot}，我们去{channel}商议。",
                    mentions=context.get("mentions", [])
                ),
                "channel_name": self._get_channel_name(target_channel)
            }
        
        # 默认逻辑...
```

---

## 实施计划

### 修改文件列表

| 文件 | 修改内容 | 预计时间 |
|------|----------|----------|
| `context_filter.py` | 放宽时间窗口，添加对话状态感知 | 30分钟 |
| `role_bot.py` | 添加 conversation_state，修改 _should_respond | 45分钟 |
| `architecture_builder.py` | 增强频道信息，添加频道别名映射 | 30分钟 |
| `SYSTEM_PROMPT_TEMPLATE` | 添加持续对话规则和频道使用指南 | 30分钟 |
| 测试 | 添加持续对话测试和频道识别测试 | 45分钟 |
| **总计** | | **3小时** |

### 实施顺序

1. **修改 ContextFilter** - 放宽相关性判断
2. **修改 RoleBot** - 添加对话状态
3. **增强 architecture_builder** - 完善频道信息
4. **更新 System Prompt** - 添加对话和频道指南
5. **添加测试** - 验证修复效果
6. **部署测试** - 验证 Bot 行为

---

## 预期效果

### 修复前
```
丞相: @太尉，此事如何？
太尉: @丞相，可行。（对话结束）

用户: 去内阁商议
Bot: （不理解"内阁"是什么）
```

### 修复后
```
丞相: @太尉，此事如何？
太尉: @丞相，我觉得可行，但需完善。你认为呢？
丞相: @太尉，善。那我们就此定论？
太尉: @丞相，可。（自然结束）

用户: 去内阁商议
Bot: @太尉，我们去内阁商议。（正确切换到内阁频道）
```

---

*方案已细化，等待陛下指示实施。*