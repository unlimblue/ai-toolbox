# Multi-Bot System Prompts

Modular prompt system for the Cyber Dynasty multi-bot architecture.

## Directory Structure

```
prompts/multi_bot/
├── base/              # Core prompt components (required)
│   ├── identity.md    # Bot identity template
│   ├── capabilities.md # Capabilities and channel info
│   ├── rules.md       # Conversation rules (anti-loop, termination)
│   └── members.md     # System members template
├── roles/             # Role-specific configurations
│   ├── chengxiang.md  # 丞相 - Chancellor
│   ├── taiwei.md      # 太尉 - Grand Commandant
│   └── ...            # Add more roles as needed
└── behaviors/         # User-customizable behaviors
    ├── default.yaml   # Default behavior settings
    └── custom/        # User-defined custom behaviors
```

## How It Works

1. **Base Components**: These form the foundation of every bot's system prompt
2. **Role Configuration**: Each bot loads its specific role configuration
3. **Behavior Settings**: Users can customize bot behavior via YAML files
4. **Template Variables**: Files use `{{variable}}` syntax for dynamic substitution

## Customization

### Add a New Role

1. Create `roles/your_role.md`
2. Define role-specific personality and instructions
3. Reference in bot configuration

### Customize Behavior

1. Edit `behaviors/default.yaml` or create new YAML files
2. Set configuration values (response_style, auto_terminate, etc.)
3. Add custom instructions that will be appended to the prompt

### Template Variables

Available in all prompt files:
- `{{bot_id}}` - Bot identifier
- `{{bot_name}}` - Bot display name
- `{{bot_role_id}}` - Discord role ID
- `{{bot_title}}` - Bot title/position
- `{{persona_description}}` - Persona description
- `{{persona_personality}}` - Personality traits
- `{{persona_speech_style}}` - Speech style
- `{{mention_examples}}` - Auto-generated mention examples
- `{{other_members}}` - Auto-generated member list
- `{{channel_info}}` - Auto-generated channel information

## Usage

The `PromptLoader` class in `architecture_builder.py` dynamically loads
and combines these files to build the complete system prompt for each bot.
