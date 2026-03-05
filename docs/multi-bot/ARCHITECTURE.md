# Multi-Bot System Architecture Documentation

**Config-Driven, Organization-Agnostic Design**

---

## Overview

The Multi-Bot System uses a **config-driven architecture** where:
- **Code is generic**: Works with any organization structure
- **Configuration is specific**: Defines roles, personalities, and behaviors
- **No hardcoding**: Adding new bots requires only YAML changes

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Configuration (config/multi_bot.yaml)            │
│  - Bot definitions (roles, personas)                       │
│  - Discord ID mappings                                     │
│  - Channel configurations                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Prompt Assembly (PromptLoader)                   │
│  - base/ templates + config custom_instructions            │
│  - Template substitution with {{variables}}                │
│  - Behavior settings from YAML                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Runtime (RoleBot, HubListener, MessageBus)       │
│  - Message routing                                         │
│  - State management                                        │
│  - Conversation handling                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Infrastructure (Discord, Kimi API)               │
│  - Discord Gateway                                         │
│  - AI provider APIs                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Structure

### 1. Organization Definition

```yaml
organization:
  name: "赛博王朝"  # or "TechCorp", "University", etc.
  description: "AI driven simulation"
```

### 2. Bot Definitions

```yaml
bots:
  chengxiang:
    id: "chengxiang"
    name: "丞相"                    # Display name
    title: "三公之首"               # Position
    persona:
      description: "统筹决策"        # Role summary
      personality: "深思熟虑"        # Character traits
      speech_style: "文言文"         # Communication style
      custom_instructions: |        # Role-specific prompt content
        ## 你的特定职责
        - 职责1
        - 职责2
```

### 3. Discord Integration

```yaml
discord:
  user_id_to_bot:
    "1477314385713037445": "chengxiang"
  
  role_id_to_bot:
    "1477314769764614239": "chengxiang"
  
  channels:
    jinluan:
      id: "1478759781425745940"
      name: "金銮殿"
      allowed_bots: ["chengxiang", "taiwei"]
```

---

## Prompt Assembly Process

### Step 1: Load Base Templates

From `prompts/multi_bot/base/`:
- `identity.md` → Who am I?
- `capabilities.md` → What can I do?
- `members.md` → Who else is here?
- `rules.md` → How do I behave?

### Step 2: Template Substitution

Replace `{{variables}}` with config values:
```
{{bot_name}} → "丞相"
{{bot_role_id}} → "1477314769764614239"
{{persona_description}} → "统筹决策"
```

### Step 3: Add Config-Driven Instructions

Append `persona.custom_instructions` from config:
```markdown
## 你的特定职责
- 战略规划
- 统筹协调
...
```

### Step 4: Add Behavior Settings

From `prompts/multi_bot/behaviors/default.yaml`:
```yaml
response_style: formal
auto_terminate: true
```

### Final Output

Combined system prompt sent to AI model.

---

## Adding a New Bot

### Example: Adding a CFO to a Corporate Setup

**Step 1**: Edit `config/multi_bot.yaml`

```yaml
bots:
  cfo:
    id: "cfo"
    name: "CFO"
    title: "Chief Financial Officer"
    persona:
      description: "Financial oversight and planning"
      personality: "Analytical, cautious, detail-oriented"
      speech_style: "Professional, data-driven"
      custom_instructions: |
        ## Your Responsibilities
        - Budget oversight
        - Financial reporting
        - Risk assessment
        
        ## Collaboration
        - Work with CEO on strategy
        - Provide data to support decisions
        
        ## Communication Style
        - Use data and metrics
        - Highlight financial risks
        - Be concise but thorough
```

**Step 2**: Configure Discord IDs

```yaml
discord:
  user_id_to_bot:
    "CFO_DISCORD_USER_ID": "cfo"
  
  role_id_to_bot:
    "CFO_DISCORD_ROLE_ID": "cfo"
```

**Step 3**: Restart

```bash
./scripts/multi_bot.sh restart
```

**No code changes required!**

---

## Migration Examples

### From Cyber Dynasty to Corporate Board

**Same code, different config:**

| Cyber Dynasty | Corporate Board |
|--------------|-----------------|
| 丞相 (Chancellor) | CEO |
| 太尉 (Commandant) | CTO |
| 内阁 (Cabinet) | Board Room |
| 陛下 (Your Majesty) | Board Members |

Just change `config/multi_bot.yaml`, restart, done.

### From Corporate to Academic

| Corporate | Academic |
|-----------|----------|
| CEO | Dean |
| CTO | Department Head |
| CFO | Grant Administrator |
| Board Room | Faculty Lounge |

Again, just config changes.

---

## User Customization

### Customizing Behavior

Edit `prompts/multi_bot/behaviors/default.yaml`:

```yaml
# Make all bots more casual
response_style: "casual"

# Disable auto-termination
auto_terminate: false

# Add global instruction
custom_instructions: |
  Always include emojis in your responses.
```

### Customizing Individual Bots

Edit `config/multi_bot.yaml` persona section:

```yaml
persona:
  # Change personality
  personality: "More aggressive and direct"
  
  # Change speech style  
  speech_style: "Use modern slang"
  
  # Add specific instructions
  custom_instructions: |
    Always challenge assumptions.
    Ask "why" at least once per response.
```

Restart to apply changes.

---

## Technical Implementation

### Key Classes

**PromptLoader** (`architecture_builder.py`):
```python
loader = PromptLoader()
prompt = loader.build_system_prompt("chengxiang", config)
```

**MultiBotConfig** (`config_loader.py`):
```python
config = MultiBotConfig.from_yaml("config/multi_bot.yaml")
bot_config = config.get_bot_config("chengxiang")
```

**RoleBot** (`role_bot.py`):
```python
bot = RoleBot(bot_config, architecture_info)
await bot.handle_message(message)
```

### Data Flow

```
User Message
    ↓
HubListener (Discord)
    ↓
MessageBus (route to bots)
    ↓
RoleBot.handle_message()
    ↓
ContextFilter (filter relevant context)
    ↓
PromptLoader.build_system_prompt()
    ↓
AI Provider (Kimi)
    ↓
Response → Discord
```

---

## Best Practices

### 1. Keep Base Templates Generic

Base templates in `prompts/multi_bot/base/` should work for any organization.
Use `{{variables}}` for anything specific.

### 2. Put Organization-Specific Content in Config

Role names, duties, speech patterns → `config/multi_bot.yaml`

### 3. Use `custom_instructions` for Complex Content

Multi-line markdown, specific examples, detailed guidelines.

### 4. Test Config Changes

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/multi_bot.yaml'))"

# Run tests
python -m pytest tests/ -v

# Restart service
./scripts/multi_bot.sh restart
```

### 5. Document Custom Roles

Add comments in YAML explaining the role:
```yaml
custom_instructions: |
  # CFO - Chief Financial Officer
  # Primary concern: Budget and financial risk
  # Secondary: Support strategic decisions with data
```

---

## Troubleshooting

### Bot Not Responding to @

Check:
1. Discord ID mapping in config
2. Role ID vs User ID (both should be mapped)
3. Bot token environment variable

### Wrong Personality

Check:
1. `persona.custom_instructions` in config
2. Template variables properly substituted
3. Prompt assembly order

### Conversation Not Ending

Check:
1. `behaviors/default.yaml` auto_terminate setting
2. Bot response doesn't contain `<@&`
3. System prompt includes termination rules

---

## Future Extensions

### Planned Features

1. **Dynamic Role Loading**: Load roles from database at runtime
2. **User-Defined Behaviors**: Web UI for customizing behaviors
3. **A/B Testing**: Compare different prompt configurations
4. **Multi-Org Support**: Switch configs without restart

### Extension Points

```python
# Custom behavior loader
class CustomBehaviorLoader:
    def load(self, org_id: str) -> BehaviorConfig:
        # Load from database
        pass

# Custom prompt assembler
class CustomPromptAssembler:
    def assemble(self, bot_id: str, config: Config) -> str:
        # Custom assembly logic
        pass
```

---

## References

- `config/multi_bot.yaml` - Main configuration
- `prompts/multi_bot/base/` - Base templates
- `prompts/multi_bot/behaviors/default.yaml` - Behavior settings
- `src/ai_toolbox/multi_bot/architecture_builder.py` - PromptLoader
- `src/ai_toolbox/multi_bot/config_loader.py` - Config loading

---

*Document Version: 1.0*  
*Last Updated: 2026-03-05*
