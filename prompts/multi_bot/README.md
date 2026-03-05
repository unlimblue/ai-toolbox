# Multi-Bot System Prompts

**Config-driven, modular prompt system** for any multi-bot architecture.

## Design Philosophy

- **Configuration-Driven**: All role definitions are in `config/multi_bot.yaml`, not hardcoded
- **Organization-Agnostic**: Same code works for any organization (Cyber Dynasty, Corporate, etc.)
- **Modular**: Base templates + config-specific custom instructions
- **User-Customizable**: Behaviors can be customized without code changes

---

## Directory Structure

```
prompts/multi_bot/
├── base/              # Core prompt templates (organization-agnostic)
│   ├── identity.md    # Bot identity with {{variables}}
│   ├── capabilities.md # Capabilities and channel info
│   ├── rules.md       # Conversation rules (anti-loop, termination)
│   └── members.md     # System members with {{variables}}
├── behaviors/         # User-customizable behavior settings
│   └── default.yaml   # Response style, auto_terminate, etc.
└── README.md          # This file
```

**Note**: No `roles/` directory! Roles are defined entirely in configuration.

---

## How It Works

### Prompt Assembly Order

```
1. base/identity.md         → Bot identity with {{bot_name}}, {{persona_*}}
2. base/capabilities.md     → Capabilities and channel aliases
3. base/members.md          → Other members info
4. base/rules.md            → Conversation rules
5. config persona.custom_instructions → Role-specific content from YAML
6. behaviors/default.yaml   → User behavior settings
7. Current Context          → Dynamic context
```

### Template Variables

All `base/` templates use `{{variable}}` syntax:

| Variable | Description |
|----------|-------------|
| `{{bot_id}}` | Bot identifier (e.g., "chengxiang") |
| `{{bot_name}}` | Display name (e.g., "丞相") |
| `{{bot_role_id}}` | Discord role ID |
| `{{bot_title}}` | Title/position |
| `{{persona_description}}` | From config persona.description |
| `{{persona_personality}}` | From config persona.personality |
| `{{persona_speech_style}}` | From config persona.speech_style |
| `{{mention_examples}}` | Auto-generated mention examples |
| `{{other_members}}` | Auto-generated member list |
| `{{channel_info}}` | Auto-generated channel info |

---

## Adding a New Role

### Step 1: Add to `config/multi_bot.yaml`

```yaml
bots:
  your_new_bot:
    id: "your_new_bot"
    name: "新角色名"
    title: "职位"
    persona:
      description: "角色描述"
      personality: "性格特点"
      speech_style: "说话风格"
      # Role-specific custom instructions (markdown supported)
      custom_instructions: |
        ## 你的特定职责
        
        - 职责1
        - 职责2
        
        ## 与其他角色协作
        
        - 如何协作
        
        ## 对话风格
        
        - 特定风格要求
```

### Step 2: Configure Discord IDs

```yaml
discord:
  user_id_to_bot:
    "DISCORD_USER_ID": "your_new_bot"
  
  role_id_to_bot:
    "DISCORD_ROLE_ID": "your_new_bot"
```

### Step 3: Restart Service

```bash
./scripts/multi_bot.sh restart
```

**No code changes needed!**

---

## Customizing Behaviors

Edit `behaviors/default.yaml`:

```yaml
# Response style: formal, casual, concise, detailed
response_style: formal

# Auto-terminate when no @ in response
auto_terminate: true

# Max conversation rounds
max_conversation_rounds: 5

# Custom global instructions
custom_instructions: |
  Additional instructions appended to all bots.
```

---

## Migrating to Different Organization

To use this system for a completely different organization:

1. **Keep**: `prompts/multi_bot/base/` (generic templates)
2. **Edit**: `config/multi_bot.yaml` (your organization structure)
3. **Set**: Discord IDs and tokens in environment variables
4. **Restart**: Service with new config

The base templates work with any organization because they use `{{variables}}` populated from config.

---

## Example: Corporate Board vs Cyber Dynasty

### Same Code, Different Config

**Cyber Dynasty** (current):
```yaml
bots:
  chengxiang: { name: "丞相", title: "三公之首" }
  taiwei: { name: "太尉", title: "三公之一" }
```

**Corporate Board** (future):
```yaml
bots:
  ceo: { name: "CEO", title: "Chief Executive" }
  cfo: { name: "CFO", title: "Chief Financial" }
  cto: { name: "CTO", title: "Chief Technology" }
```

Same `base/` templates work for both! Only config changes.

---

## Technical Details

- **PromptLoader** class in `architecture_builder.py` handles assembly
- Template substitution happens at runtime
- Config changes don't require code deployment (just restart)
- YAML frontmatter supported in custom_instructions

---

*Last updated: 2026-03-05*
