# Multi-Bot System 改进实施方案

**日期**: 2026-03-05  
**需求**: 
1. 移除 Hard Code，赋予 AI 决策能力
2. 统一配置管理，支持任意组织

---

## 需求分析

### 需求 1: AI 驱动的 Bot 行为

**当前问题**:
```python
# role_bot.py - Hard Coded 逻辑
async def handle_task(self, task):
    # 固定回复
    await self.send_message(task.source_channel, "领旨，即刻去内阁商议。")
    await self.send_message(task.target_channel, "奉陛下旨意，来此商议...")
```

**目标**:
- Bot 理解命令语义
- 自主决定：去哪、做什么、@谁
- 灵活选择频道，不限于固定配置

### 需求 2: 统一配置管理

**当前问题**:
- ID 映射分散在代码中
- Token 在环境变量
- 频道配置硬编码
- 只支持赛博王朝

**目标**:
- 集中式配置文件
- 环境变量可覆盖
- 支持任意组织配置
- 多组织模板

---

## 实施方案

### 第一阶段: 统一配置管理 (优先级: 高)

**原因**: 配置管理是基础设施，先完成后才能灵活配置 Bot 行为

#### 1.1 创建统一配置文件

**文件**: `config/multi_bot.yaml`

```yaml
# Multi-Bot System Configuration

# Organization Settings
organization:
  name: "赛博王朝"
  description: "AI driven cyber dynasty simulation"

# Discord Settings
discord:
  # Bot Tokens (can be overridden by environment variables)
  hub_bot_token: "${HUB_BOT_TOKEN}"
  
  # ID Mappings
  user_id_to_bot:
    "1477314385713037445": "chengxiang"
    "1478216774171365466": "taiwei"
  
  role_id_to_bot:
    "1477314769764614239": "chengxiang"
    "1478217215936430092": "taiwei"
  
  # Channels
  channels:
    jinluan:
      id: "1478759781425745940"
      name: "金銮殿"
      allowed_bots: ["chengxiang", "taiwei"]
    neige:
      id: "1477312823817277681"
      name: "内阁"
      allowed_bots: ["chengxiang", "taiwei"]
    bingbu:
      id: "1477273291528867860"
      name: "兵部"
      allowed_bots: ["taiwei"]

# Bot Configurations
bots:
  chengxiang:
    name: "丞相"
    title: "三公之首"
    token: "${CHENGXIANG_BOT_TOKEN}"
    model_provider: "kimi"
    model_name: "kimi-k2-5"
    api_key: "${KIMI_API_KEY}"
    channels: ["jinluan", "neige"]
    persona:
      description: "统筹决策"
      personality: "深思熟虑、顾全大局"
      speech_style: "文雅的文言文风格"
      keywords: ["统筹", "决策", "协调", "大局"]
    
  taiwei:
    name: "太尉"
    title: "三公之一"
    token: "${TAIWEI_BOT_TOKEN}"
    model_provider: "kimi"
    model_name: "kimi-k2-5"
    api_key: "${KIMI_API_KEY}"
    channels: ["jinluan", "neige", "bingbu"]
    persona:
      description: "安全执行"
      personality: "果断坚决、执行力强"
      speech_style: "简洁有力"
      keywords: ["安全", "执行", "防御", "军事"]

# Debug Settings
debug:
  enabled: true
  channel: "jinluan"
```

#### 1.2 创建配置加载器

**文件**: `src/ai_toolbox/multi_bot/config_loader.py`

```python
"""Configuration loader for multi-bot system."""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class MultiBotConfig:
    """Multi-bot configuration manager."""
    
    def __init__(self, config_path: str = None):
        """
        Load configuration from file and environment.
        
        Args:
            config_path: Path to config file. If None, use default.
        """
        if config_path is None:
            config_path = os.getenv(
                "MULTI_BOT_CONFIG",
                "config/multi_bot.yaml"
            )
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and process configuration."""
        # Load from file
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Process environment variable references
        config = self._process_env_vars(config)
        
        return config
    
    def _process_env_vars(self, obj: Any) -> Any:
        """Process ${VAR} references in configuration."""
        if isinstance(obj, dict):
            return {k: self._process_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._process_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            # Extract variable name
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj
    
    # Property accessors
    @property
    def organization(self) -> Dict[str, str]:
        return self._config.get("organization", {})
    
    @property
    def discord_config(self) -> Dict[str, Any]:
        return self._config.get("discord", {})
    
    @property
    def bots(self) -> Dict[str, Dict]:
        return self._config.get("bots", {})
    
    @property
    def channels(self) -> Dict[str, Dict]:
        return self.discord_config.get("channels", {})
    
    @property
    def debug_config(self) -> Dict[str, Any]:
        return self._config.get("debug", {})
    
    def get_bot_config(self, bot_id: str) -> Dict:
        """Get configuration for specific bot."""
        return self.bots.get(bot_id, {})
    
    def get_channel_config(self, channel_id_or_name: str) -> Dict:
        """Get channel config by ID or name."""
        channels = self.channels
        
        # Try by name first
        if channel_id_or_name in channels:
            return channels[channel_id_or_name]
        
        # Try by ID
        for name, config in channels.items():
            if config.get("id") == channel_id_or_name:
                return config
        
        return {}
    
    def resolve_channel_id(self, name: str) -> str:
        """Resolve channel name to ID."""
        config = self.channels.get(name, {})
        return config.get("id", name)
```

#### 1.3 更新 config.py 使用新配置

**修改**: `src/ai_toolbox/multi_bot/config.py`

```python
# Remove hardcoded configurations
# Use config_loader instead

from .config_loader import MultiBotConfig

# Global config instance
_config = None

def get_config() -> MultiBotConfig:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = MultiBotConfig()
    return _config
```

#### 1.4 创建多组织模板

**目录**: `config/organizations/`

```
config/
├── multi_bot.yaml              # 默认配置（赛博王朝）
└── organizations/
    ├── cyber_dynasty.yaml      # 赛博王朝
    ├── corporate_board.yaml    # 企业董事会
    └── ai_council.yaml         # AI 委员会
```

**corporate_board.yaml 示例**:

```yaml
organization:
  name: "未来科技董事会"
  description: "企业决策模拟"

discord:
  user_id_to_bot:
    "123456789": "ceo"
    "987654321": "cto"
  
  role_id_to_bot:
    "111111111": "ceo"
    "222222222": "cto"
  
  channels:
    board_room:
      id: "999999999"
      name: "董事会"
      allowed_bots: ["ceo", "cto"]

bots:
  ceo:
    name: "CEO"
    title: "首席执行官"
    # ...
```

#### 1.5 测试

**测试文件**: `tests/unit/multi_bot/test_config_loader.py`

```python
def test_config_loading():
    config = MultiBotConfig("test_config.yaml")
    assert config.organization["name"] == "赛博王朝"

def test_env_var_substitution():
    os.environ["TEST_TOKEN"] = "test_value"
    config = MultiBotConfig()
    # Check ${TEST_TOKEN} is replaced

def test_channel_resolution():
    config = MultiBotConfig()
    assert config.resolve_channel_id("jinluan") == "1478759781425745940"
```

**预计时间**: 2-3 小时

---

### 第二阶段: AI 驱动的 Bot 行为 (优先级: 高)

#### 2.1 重新设计 System Prompt

**目标**: 让 Bot 理解语义，自主决策

**新的 System Prompt 模板**:

```python
BASE_SYSTEM_PROMPT = """你是 {role_name}（{title}），一个智能 Discord Bot。

## 你的能力

1. **理解命令**: 你可以理解皇帝的指令，并自主决定如何执行
2. **选择频道**: 你可以在任意频道发言，不限于固定频道
3. **@任何人**: 你可以 @ 任何人（人类或其他 Bot）
4. **灵活响应**: 根据情境选择适当的回复方式和行动

## 可用频道

{channels_info}

## 其他官员

{other_bots_info}

## 决策指南

当收到指令时，你需要：

1. **理解意图**: 分析皇帝想要什么
2. **选择行动**: 决定：
   - 去哪讨论？
   - @谁参与？
   - 做什么？
3. **执行响应**: 在合适的频道回复并行动

## 回复格式

你的回复应该直接且行动导向。例如：

- "@太尉，我们去内阁商议此事，如何？"
- "领旨，我这就去兵部部署。"
- "@皇帝，臣认为应当先调查再决策。"

## 当前对话上下文

{context}

## 任务

请根据以上信息，自主决定如何响应。
"""
```

#### 2.2 重构 RoleBot

**修改**: `src/ai_toolbox/multi_bot/role_bot.py`

```python
class RoleBot:
    """AI-driven role bot with flexible behavior."""
    
    async def handle_message(self, message: UnifiedMessage):
        """
        Handle message using AI to decide action.
        
        The AI will:
        1. Understand the command semantics
        2. Decide what to do
        3. Choose which channel to respond in
        4. Decide who to @
        """
        # Build context with all available information
        context = self._build_decision_context(message)
        
        # Call AI to decide action
        action = await self._decide_action(context)
        
        # Execute the decided action
        await self._execute_action(action, message)
    
    async def _decide_action(self, context: dict) -> dict:
        """
        Use AI to decide what action to take.
        
        Returns action dict like:
        {
            "type": "discuss",
            "target_channel": "neige",
            "message": "@太尉，我们去内阁商议此事如何？",
            "mentions": ["taiwei"]
        }
        """
        prompt = self._build_decision_prompt(context)
        
        response = await self._call_ai(prompt)
        
        # Parse AI response into action
        return self._parse_action_response(response)
    
    async def _execute_action(self, action: dict, original_message: UnifiedMessage):
        """Execute the decided action."""
        action_type = action.get("type")
        
        if action_type == "discuss":
            # Go to target channel and start discussion
            channel_id = self._resolve_channel(action["target_channel"])
            await self.send_message(
                channel_id,
                action["message"]
            )
        
        elif action_type == "respond":
            # Respond in current channel
            await self.send_message(
                original_message.channel_id,
                action["message"]
            )
        
        elif action_type == "cross_channel":
            # Handle cross-channel task
            await self._handle_cross_channel_task(action)
        
        # ... other action types
```

#### 2.3 移除 Hard Coded 逻辑

**删除**:
```python
# 删除固定的回复
"领旨，即刻去内阁商议。"
"奉陛下旨意，来此商议..."
```

**改为 AI 生成**:
```python
# AI 根据上下文决定回复内容
response = await self._generate_response(context)
```

#### 2.4 支持任意频道发言

**修改**: 移除频道限制检查

```python
# Old: Check if bot can speak in channel
if channel_id not in self.config.channels:
    raise PermissionError("Cannot speak in this channel")

# New: Allow speaking in any channel
channel = self._client.get_channel(int(channel_id))
if channel:
    await channel.send(message)
```

#### 2.5 测试

**测试文件**: `tests/unit/multi_bot/test_ai_behavior.py`

```python
@pytest.mark.asyncio
async def test_bot_decides_discussion_channel():
    """Test bot can decide which channel to discuss in."""
    bot = RoleBot(config)
    
    message = UnifiedMessage(
        content="@丞相 @太尉 去内阁商议",
        mentions=["chengxiang", "taiwei"]
    )
    
    action = await bot._decide_action({"message": message})
    
    assert action["type"] == "discuss"
    assert action["target_channel"] == "neige"
```

**预计时间**: 4-6 小时

---

## 实施顺序

| 阶段 | 内容 | 预计时间 | 依赖 |
|------|------|----------|------|
| 1 | 统一配置管理 | 2-3 小时 | 无 |
| 2 | AI 驱动 Bot 行为 | 4-6 小时 | 阶段 1 |
| **总计** | | **6-9 小时** | |

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| YAML 解析错误 | 低 | 中 | 添加配置验证 |
| AI 决策不稳定 | 中 | 高 | 添加决策日志，可回退到规则 |
| 权限问题 | 低 | 高 | 测试 Bot 在任意频道的权限 |

---

## 回滚方案

```bash
# 如果出现问题，回滚到当前存档点
git checkout 71b2195
./scripts/multi_bot.sh restart
```

---

## 成功标准

### 阶段 1 成功标准
- [ ] 配置文件正确加载
- [ ] 环境变量正确覆盖
- [ ] 支持多组织模板
- [ ] 所有测试通过

### 阶段 2 成功标准
- [ ] Bot 理解语义命令
- [ ] Bot 自主选择频道
- [ ] Bot @ 任意人
- [ ] 无 Hard Code 逻辑
- [ ] 所有测试通过

---

*方案已细化，等待陛下审阅指示。*