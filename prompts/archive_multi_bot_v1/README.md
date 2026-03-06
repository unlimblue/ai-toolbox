# 多 Bot 系统提示词

**配置驱动、模块化提示词系统** - 适用于任何多 Bot 架构。

## 设计理念

- **配置驱动**: 所有角色定义都在 `config/multi_bot.yaml` 中，非硬编码
- **组织无关**: 同一套代码适用于任何组织结构
- **模块化**: 基础模板 + 配置特定的自定义指令
- **用户可定制**: 行为可自定义，无需修改代码

---

## 目录结构

```
prompts/multi_bot/
├── base/              # 核心提示词模板（组织无关）
│   ├── identity.md    # Bot 身份与 {{变量}}
│   ├── capabilities.md # 能力和频道信息
│   ├── rules.md       # 对话规则（防循环、终止）
│   └── members.md     # 系统成员与 {{变量}}
├── behaviors/         # 用户可自定义的行为设置
│   └── default.yaml   # 响应风格、自动终止等
└── README.md          # 本文档

注意：没有 roles/ 目录！角色完全在配置中定义。
```

---

## 工作原理

### 提示词组装顺序

```
1. base/identity.md         → Bot 身份 {{bot_name}}, {{persona_*}}
2. base/capabilities.md     → 能力和频道别名
3. base/members.md          → 其他成员信息
4. base/rules.md            → 对话规则
5. config persona.custom_instructions → YAML 中的角色特定内容
6. behaviors/default.yaml   → 用户行为设置
7. 当前上下文              → 动态上下文
```

### 模板变量

所有 `base/` 模板使用 `{{变量}}` 语法：

| 变量 | 说明 |
|------|------|
| `{{bot_id}}` | Bot 标识符（如 "chengxiang"） |
| `{{bot_name}}` | 显示名称（如 "丞相"） |
| `{{bot_role_id}}` | Discord 角色 ID |
| `{{bot_title}}` | 职位/头衔 |
| `{{persona_description}}` | 来自 config persona.description |
| `{{persona_personality}}` | 来自 config persona.personality |
| `{{persona_speech_style}}` | 来自 config persona.speech_style |
| `{{mention_examples}}` | 自动生成的 @ 示例 |
| `{{other_members}}` | 自动生成的成员列表 |
| `{{channel_info}}` | 自动生成的频道信息 |

---

## 添加新角色

### 步骤 1：添加到 `config/multi_bot.yaml`

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
      # 角色特定的自定义指令（支持 Markdown）
      custom_instructions: |
        ## 你的特定职责
        
        - 职责1
        - 职责2
        
        ## 与其他角色协作
        
        - 如何协作
        
        ## 对话风格
        
        - 特定风格要求
```

### 步骤 2：配置 Discord ID

```yaml
discord:
  user_id_to_bot:
    "DISCORD_USER_ID": "your_new_bot"
  
  role_id_to_bot:
    "DISCORD_ROLE_ID": "your_new_bot"
```

### 步骤 3：重启服务

```bash
./scripts/multi_bot.sh restart
```

**无需代码变更！**

---

## 自定义行为

编辑 `behaviors/default.yaml`：

```yaml
# 响应风格：formal, casual, concise, detailed
response_style: formal

# 无 @ 时自动终止对话
auto_terminate: true

# 最大对话轮数
max_conversation_rounds: 5

# 添加全局指令
custom_instructions: |
  所有回应都必须包含表情符号。
```

---

## 迁移到不同组织

将此系统用于完全不同的组织：

1. **保留**: `prompts/multi_bot/base/`（通用模板）
2. **编辑**: `config/multi_bot.yaml`（你的组织结构）
3. **设置**: Discord ID 和令牌在环境变量中
4. **重启**: 使用新配置启动服务

基础模板适用于任何组织，因为它们使用从配置填充的 `{{变量}}`。

---

## 示例：企业董事会 vs 赛博王朝

### 相同代码，不同配置

**赛博王朝**（当前）：
```yaml
bots:
  chengxiang: { name: "丞相", title: "三公之首" }
  taiwei: { name: "太尉", title: "三公之一" }
```

**企业董事会**（未来）：
```yaml
bots:
  ceo: { name: "CEO", title: "Chief Executive" }
  cfo: { name: "CFO", title: "Chief Financial" }
  cto: { name: "CTO", title: "Chief Technology" }
```

相同的 `base/` 模板适用于两者！只需更改配置。

---

## 技术详情

- **PromptLoader** 类在 `architecture_builder.py` 中处理组装
- 模板替换在运行时发生
- 配置更改不需要代码部署（只需重启）
- 支持 YAML 前言的 custom_instructions

---

*最后更新: 2026-03-05*
