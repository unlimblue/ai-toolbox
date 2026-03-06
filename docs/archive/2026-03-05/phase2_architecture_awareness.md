# Multi-Bot System V2 - 第二阶段细化方案（架构感知）

**日期**: 2026-03-05  
**核心问题**: Bot 不知道自己的 ID，无法识别 @ID 消息中的身份  
**解决方案**: 将 config 内容结构化注入 system prompt

---

## 问题分析

### 当前问题

**场景**: 用户发送 `@丞相 @太尉 去内阁商议`

**当前 System Prompt**:
```
你是丞相，三公之首...
你可以 @ 任何人...
```

**问题**:
1. Bot 知道自己是"丞相"，但不知道自己的 `bot_id` 是 `chengxiang`
2. Bot 知道可以 @ "太尉"，但不知道太尉的 `bot_id` 是 `taiwei`
3. Bot 不知道"内阁"对应的 `channel_id` 是 `1477312823817277681`
4. Bot 不知道如何在消息中正确格式化 @（使用角色ID还是用户ID）

**结果**: Bot 生成的响应可能是纯文本 "@太尉"，而不是可被路由的 `<@&role_id>`

---

## 解决方案：结构化系统架构注入

### 1. 增强 System Prompt 模板

```python
SYSTEM_PROMPT_TEMPLATE = """你是 {bot_name}（{bot_title}），在 {organization_name} 中担任重要角色。

## 🆔 你的身份标识

**你的基本信息**:
- 显示名称: {bot_name}
- 职位: {bot_title}
- Bot ID: {bot_id}
- Discord 用户ID: {bot_user_id}
- Discord 角色ID: {bot_role_id}

**你的职责**: {bot_description}
**你的性格**: {bot_personality}
**说话风格**: {bot_speech_style}

## 👥 系统成员（你可以 @ 的人）

{other_bots_info}

## 📍 可用频道（你可以发言的地方）

{channels_info}

## 💬 如何正确 @ 人

当你想 @ 某人时，必须使用以下格式：

### 方法1: 使用角色 @（推荐）
格式: `<@&角色ID>`

可用角色映射:
{role_mention_map}

### 方法2: 使用用户 @
格式: `<@用户ID>`

可用用户映射:
{user_mention_map}

### 方法3: 使用名称（不推荐）
如果上述ID不可用，可以使用 `@名称`，但可能无法正确路由。

## 🎯 响应格式指南

当你需要响应并 @ 某人时，请使用以下格式：

**示例1 - 使用角色 @**:
```
<@{other_bot_role_id}>，我们去{channel_name}商议此事如何？
```

**示例2 - 确认指令**:
```
领旨，我这就去{channel_name}部署。
```

**示例3 - 多人讨论**:
```
<@{bot1_role_id}> <@{bot2_role_id}>，我们去{channel_name}商议。
```

## 🏃 行动指南

当收到指令时，你需要：

1. **理解意图**: 分析说话人想要什么
2. **识别目标**: 确定需要 @ 谁（从系统成员中选择）
3. **选择频道**: 确定在哪个频道响应（从可用频道中选择）
4. **格式化 @**: 使用 `<@&角色ID>` 或 `<@用户ID>` 格式
5. **生成回复**: 结合以上信息生成完整回复

## 📋 当前对话上下文

{context}

## ⚠️ 重要提醒

- 必须正确使用 `<@&角色ID>` 或 `<@用户ID>` 格式，否则消息无法被正确路由
- 频道名称是给人看的，实际发送时需要使用频道ID（系统会自动处理）
- 你可以在任何可用频道发言，不限于当前频道

## 🎭 你的角色特性

{bot_keywords}
{bot_responsibilities}

请根据以上信息，自主决定如何响应。
"""
```

### 2. 动态生成系统架构信息

```python
def build_system_architecture_info(bot_id: str, config: MultiBotConfig) -> dict:
    """
    构建 Bot 的系统架构感知信息
    
    Args:
        bot_id: 当前 Bot 的 ID
        config: 配置对象
        
    Returns:
        用于填充 System Prompt 的字典
    """
    bot_config = config.get_bot_config(bot_id)
    persona = bot_config.get("persona", {})
    
    # 1. 构建其他 Bot 信息
    other_bots_info = []
    for other_id, other_config in config.bots.items():
        if other_id != bot_id:
            user_id = config.get_user_id_for_bot(other_id)
            role_id = config.get_role_id_for_bot(other_id)
            
            other_bots_info.append(
                f"- {other_config.get('name')} ({other_config.get('title')})\n"
                f"  - Bot ID: `{other_id}`\n"
                f"  - 用户ID: `{user_id}`\n"
                f"  - 角色ID: `{role_id}`\n"
                f"  - 职责: {other_config.get('persona', {}).get('description', '')}"
            )
    
    # 2. 构建频道信息
    channels_info = []
    for channel_name, channel_config in config.channels.items():
        channels_info.append(
            f"- {channel_config.get('name')} (`{channel_name}`)\n"
            f"  - 频道ID: `{channel_config.get('id')}`\n"
            f"  - 描述: {channel_config.get('description', '')}\n"
            f"  - 可用Bot: {', '.join(channel_config.get('allowed_bots', []))}"
        )
    
    # 3. 构建 @ 映射表
    role_mention_map = []
    user_mention_map = []
    
    for bid in config.bots.keys():
        role_id = config.get_role_id_for_bot(bid)
        user_id = config.get_user_id_for_bot(bid)
        name = config.get_bot_config(bid).get('name', bid)
        
        if role_id:
            role_mention_map.append(f"- {name}: `<@&{role_id}>`")
        if user_id:
            user_mention_map.append(f"- {name}: `<@{user_id}>`")
    
    # 4. 获取当前 Bot 的 ID 信息
    my_user_id = config.get_user_id_for_bot(bot_id)
    my_role_id = config.get_role_id_for_bot(bot_id)
    
    return {
        "bot_id": bot_id,
        "bot_name": bot_config.get('name', bot_id),
        "bot_title": bot_config.get('title', ''),
        "bot_user_id": my_user_id or "N/A",
        "bot_role_id": my_role_id or "N/A",
        "bot_description": persona.get('description', ''),
        "bot_personality": persona.get('personality', ''),
        "bot_speech_style": persona.get('speech_style', ''),
        "organization_name": config.organization.get('name', '组织'),
        "other_bots_info": "\n\n".join(other_bots_info),
        "channels_info": "\n\n".join(channels_info),
        "role_mention_map": "\n".join(role_mention_map),
        "user_mention_map": "\n".join(user_mention_map),
        "bot_keywords": "擅长领域: " + ", ".join(persona.get('keywords', [])),
        "bot_responsibilities": "职责范围: " + ", ".join(persona.get('responsibilities', [])),
    }
```

### 3. 更新 main.py 中的 Bot 创建

```python
async def main():
    # ... 加载配置 ...
    
    # 创建 Bot 时注入系统架构信息
    for bot_id in config.bots.keys():
        try:
            # 构建系统架构感知信息
            arch_info = build_system_architecture_info(bot_id, config)
            
            # 创建带有完整系统架构感知的 Bot
            bot = create_bot_with_architecture(bot_id, config, arch_info)
            bus.register_bot(bot)
            
        except Exception as e:
            logger.error(f"Failed to create bot {bot_id}: {e}")

def create_bot_with_architecture(
    bot_id: str, 
    config: MultiBotConfig,
    arch_info: dict
) -> RoleBot:
    """创建带有系统架构感知的 Bot"""
    
    bot_config_dict = config.get_bot_config(bot_id)
    
    # 生成完整的 system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**arch_info)
    
    persona = BotPersona(
        name=bot_config_dict.get("name", bot_id),
        description=bot_config_dict.get("persona", {}).get("description", ""),
        system_prompt=system_prompt
    )
    
    bot_config = BotConfig(
        bot_id=bot_id,
        name=bot_config_dict.get("name", bot_id),
        token_env=f"{bot_id.upper()}_BOT_TOKEN",
        model_provider=bot_config_dict.get("model_provider", "kimi"),
        model_name=bot_config_dict.get("model_name", "kimi-k2-5"),
        api_key_env="KIMI_API_KEY",
        channels=bot_config_dict.get("channels", []),
        persona=persona
    )
    
    return RoleBot(bot_config, architecture_info=arch_info)
```

### 4. 在 RoleBot 中保存架构信息

```python
class RoleBot:
    def __init__(self, config: BotConfig, architecture_info: dict = None):
        # ... 原有初始化 ...
        
        # 保存系统架构信息
        self.architecture_info = architecture_info or {}
        
        # 提取常用信息方便访问
        self.my_bot_id = self.architecture_info.get('bot_id')
        self.my_role_id = self.architecture_info.get('bot_role_id')
        self.my_user_id = self.architecture_info.get('bot_user_id')
        
        # 构建 @ 格式映射表
        self.mention_formats = self._build_mention_formats()
    
    def _build_mention_formats(self) -> dict:
        """构建 bot_id -> @格式的映射"""
        formats = {}
        
        # 从 architecture_info 中解析
        role_map_text = self.architecture_info.get('role_mention_map', '')
        user_map_text = self.architecture_info.get('user_mention_map', '')
        
        # 解析角色 @ 格式
        import re
        for line in role_map_text.split('\n'):
            match = re.search(r'- (.+?): `<@&(.+?)>`', line)
            if match:
                name, role_id = match.groups()
                # 通过名称找到 bot_id
                # ... 反向查找逻辑 ...
        
        return formats
    
    def format_mention(self, bot_id: str) -> str:
        """
        将 bot_id 格式化为 Discord @ 格式
        
        优先使用角色 @，其次用户 @
        """
        # 使用配置中的映射
        config = get_config()
        
        # 尝试角色ID
        role_id = config.get_role_id_for_bot(bot_id)
        if role_id:
            return f"<@&{role_id}>"
        
        # 尝试用户ID
        user_id = config.get_user_id_for_bot(bot_id)
        if user_id:
            return f"<@{user_id}>"
        
        # 兜底：使用名称
        return f"@{config.get_bot_config(bot_id).get('name', bot_id)}"
```

### 5. AI 决策时的架构感知

```python
async def _decide_action(self, context: dict) -> dict:
    """
    使用 AI 决策，带有完整的系统架构信息
    """
    # 构建包含架构信息的 prompt
    prompt = f"""基于以下系统架构信息做出决策：

## 你的身份
- Bot ID: {self.my_bot_id}
- 显示名称: {self.config.persona.name}

## 可用 @ 目标
{self.architecture_info.get('other_bots_info', '')}

## 可用频道
{self.architecture_info.get('channels_info', '')}

## 如何 @ 人
{self.architecture_info.get('role_mention_map', '')}

## 当前情境
{context}

## 任务
请决定：
1. 在哪个频道响应？（使用频道ID）
2. @谁参与？（使用 `<@&角色ID>` 格式）
3. 说什么内容？

请以 JSON 格式返回决策：
{{
    "channel": "频道名称或ID",
    "mentions": ["<@&角色ID>"],
    "message": "回复内容"
}}
"""
    
    response = await self._call_ai(prompt)
    
    # 解析 AI 的决策
    action = self._parse_ai_decision(response)
    
    return action
```

---

## 实施步骤

### Step 1: 创建系统架构构建器 (1小时)

- 创建 `build_system_architecture_info()` 函数
- 测试信息生成正确性

### Step 2: 更新 System Prompt 模板 (30分钟)

- 使用新的 `SYSTEM_PROMPT_TEMPLATE`
- 确保包含所有必要信息

### Step 3: 更新 RoleBot (1小时)

- 添加 `architecture_info` 参数
- 添加 `format_mention()` 方法
- 保存常用架构信息

### Step 4: 更新 main.py (30分钟)

- 在创建 Bot 时调用架构构建器
- 注入架构信息到每个 Bot

### Step 5: 更新 AI 决策逻辑 (1小时)

- 在决策 prompt 中包含架构信息
- 确保 AI 知道如何格式化 @

### Step 6: 测试 (1小时)

- 测试架构信息正确注入
- 测试 AI 生成的 @ 格式正确
- 测试消息路由正常

**总计: 5 小时**

---

## 预期效果

### 之前
```
用户: @丞相 @太尉 去内阁商议
Bot 思考: 我是谁？太尉是谁？内阁在哪？
Bot 回复: "@太尉，我们去内阁商议" （纯文本，无法路由）
```

### 之后
```
用户: @丞相 @太尉 去内阁商议
Bot 思考: 
  - 我是丞相（bot_id=chengxiang, role_id=1477314769764614239）
  - 太尉的 role_id 是 1478217215936430092
  - 内阁的 ID 是 1477312823817277681
Bot 回复: "<@&1478217215936430092>，我们去内阁商议" （可路由）
```

---

## 测试方案

### 测试1: 架构信息注入
```python
def test_architecture_info_injection():
    arch_info = build_system_architecture_info("chengxiang", config)
    
    assert arch_info["bot_id"] == "chengxiang"
    assert "1477314769764614239" in arch_info["bot_role_id"]  # 丞相角色ID
    assert "太尉" in arch_info["other_bots_info"]
    assert "<@&" in arch_info["role_mention_map"]  # 包含角色@格式
```

### 测试2: @ 格式化
```python
def test_format_mention():
    bot = RoleBot(config, architecture_info=arch_info)
    
    # 测试角色 @
    mention = bot.format_mention("taiwei")
    assert mention == "<@&1478217215936430092>"
```

### 测试3: AI 决策包含架构
```python
async def test_ai_decision_with_architecture():
    bot = RoleBot(config, architecture_info=arch_info)
    
    action = await bot._decide_action({"message": "@丞相 @太尉 商议"})
    
    # AI 应该返回格式化的 @
    assert "<@&" in action["message"]
```

---

*方案细化完成，等待陛下指示实施。*