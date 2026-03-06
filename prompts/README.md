# Prompt系统设计哲学

> 基于OpenClaw技能系统的分层组合思想，为赛博王朝Multi-Bot系统设计的Prompt架构

---

## 核心思想

### 1. Skill = Markdown组合

每个Skill不是单个Prompt，而是一组Markdown文件的动态组合：

```
Skill: 跨频道协作
├── identity.md      # 你是谁
├── capabilities.md  # 你能做什么
├── rules.md         # 行为规则
└── examples.md      # 示例场景
```

### 2. 三层架构

```
┌─────────────────────────────────────────┐
│ Layer 3: Specific (特定组织配置)          │
│ ├─ 赛博王朝: 频道别名、角色关系、@规则      │
│ └─ 企业董事会: 部门架构、决策流程          │
├─────────────────────────────────────────┤
│ Layer 2: Domain (领域通用)                │
│ ├─ Multi-Bot: 跨Bot协作、对话管理         │
│ ├─ Discord: 频道、@提及、消息格式          │
│ └─ AI Agent: 推理、决策、JSON输出          │
├─────────────────────────────────────────┤
│ Layer 1: Base (基础通用)                  │
│ ├─ 身份认同: 角色、职责、边界              │
│ ├─ 行为准则: 安全、伦理、限制              │
│ └─ 输出规范: 格式、结构化、验证            │
└─────────────────────────────────────────┘
```

### 3. 动态渲染引擎

**模板变量**: `{{variable}}`
```markdown
你是 {{bot_name}}，{{bot_title}}。
你的职责是: {{role_description}}
```

**条件渲染**: `{% if condition %}`
```markdown
{% if has_cross_channel_capability %}
## 跨频道能力
你可以在不同的频道之间移动和发言。
{% endif %}
```

**Skill组合**: `{% include "skill_name" %}`
```markdown
{% include "base/identity" %}
{% include "domain/multi_bot/collaboration" %}
{% include "specific/cyber_dynasty/channels" %}
```

---

## 当前问题与解决方案

### 问题1: 通用与特定的混杂

**现状**:
- `capabilities.md` 中频道别名是赛博王朝特定的
- `multi_bot.yaml` 中很多能力是通用的

**解决方案**:
```
prompts/
├── base/                    # Layer 1: 基础通用
│   ├── identity.md         # 身份模板（变量化）
│   ├── capabilities.md     # 基础能力框架
│   └── rules.md            # 通用行为准则
├── domain/                  # Layer 2: 领域通用
│   ├── multi_bot/          # Multi-Bot领域
│   │   ├── collaboration.md    # 跨Bot协作
│   │   ├── conversation.md     # 对话管理
│   │   └── at_mention.md       # @机制
│   └── discord/            # Discord平台
│       ├── channels.md     # 频道概念
│       └── mentions.md     # @提及格式
└── specific/               # Layer 3: 特定配置
    └── cyber_dynasty/      # 赛博王朝
        ├── channels.md     # 频道别名映射
        ├── roles.md        # 角色关系
        └── at_rules.md     # @规则场景化
```

### 问题2: [AT]与@标记混杂

**现状**:
- Prompt中有时写`@`，有时写`[AT]`
- Bot对何时触发@的理解不稳定

**解决方案**:
1. **统一标记**: 所有Prompt使用`[AT]`
2. **代码转换**: Python自动转换为`<@&ROLE_ID>`
3. **规则明确**: 专门的`at_rules.md`说明何时使用

```markdown
## @触发规则

### 必须使用[AT]的情况
- 问句需要回应: "...如何？[AT]丞相"
- 请求确认: "...请定夺。[AT]丞相"
- 继续对话: 需要对方继续参与讨论

### 不使用[AT]的情况
- 结论已定: "善。" "已定。"
- 单纯告知: "臣已通知。"
- 自然结束: 不需要对方回应

### 信号词
- **需要@**: "如何?", "可否?", "请定夺", "请过目"
- **自然结束**: "善。", "已定。", "领命。"
```

---

## 配置与Prompt分离

### 原则

**Config (`config/multi_bot.yaml`)**:
- 定义"是什么": 角色、频道、ID
- 不包含"怎么做": 行为规则、示例场景

**Prompt (`prompts/`)**:
- 定义"怎么做": 能力、规则、示例
- 使用变量引用Config中的定义

### 示例

**Config**:
```yaml
bots:
  chengxiang:
    name: "丞相"
    role_id: "1477314769764614239"
    capabilities:
      - cross_channel
      - at_mention
```

**Prompt** (渲染后):
```markdown
你是 丞相。

## 你的能力
{% for cap in capabilities %}
- {{ cap.description }}
{% endfor %}

## @提及格式
使用 `[AT]丞相` 格式提及丞相，系统会自动转换为 <@&1477314769764614239>。
```

---

## 扩展机制

### 新增组织

1. 创建 `config/organizations/new_org.yaml`
2. 创建 `prompts/specific/new_org/` 目录
3. 继承 `domain/multi_bot/` 和 `base/` 的通用能力
4. 只需编写特定于组织的Prompt片段

### 新增能力

1. 在 `domain/multi_bot/` 添加新的Skill Markdown
2. 在 `config/multi_bot.yaml` 中为Bot启用该能力
3. 动态渲染时自动包含

---

## 实现路线图

### Phase 1: 目录结构重构
- [ ] 创建 `prompts/base/`
- [ ] 创建 `prompts/domain/multi_bot/`
- [ ] 创建 `prompts/domain/discord/`
- [ ] 迁移 `prompts/specific/cyber_dynasty/`

### Phase 2: 动态渲染引擎
- [ ] 实现模板变量替换 `{{var}}`
- [ ] 实现条件渲染 `{% if %}`
- [ ] 实现Skill组合 `{% include %}`

### Phase 3: [AT]标准化
- [ ] 更新所有Prompt使用`[AT]`
- [ ] 更新代码转换逻辑
- [ ] 测试验证

### Phase 4: 文档完善
- [ ] 更新 `prompts/README.md`
- [ ] 创建扩展教程
- [ ] 示例组织配置

---

## 参考

- **OpenClaw Skills**: `/usr/lib/node_modules/openclaw/skills/`
- **当前配置**: `config/multi_bot.yaml`
- **当前Prompt**: `prompts/multi_bot/`

---

*设计版本: v1.0*  
*更新日期: 2026-03-06*
