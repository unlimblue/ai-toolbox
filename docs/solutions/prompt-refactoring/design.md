# Prompt系统重构方案

> 解决当前Prompt系统中通用与特定混杂、[AT]标记不规范等问题

---

## 问题陈述

### 问题1: 通用与特定混杂

**具体表现**:
- `prompts/multi_bot/base/capabilities.md` 中频道别名是赛博王朝特定的
- `config/multi_bot.yaml` 中很多能力描述是通用的，但没有对应的通用Prompt

**影响**:
- 新增组织时需要复制修改大量Prompt
- 通用能力变更需要修改多个文件
- 难以维护一致性

### 问题2: [AT]标记不规范

**具体表现**:
- Prompt中`[AT]`和`@`标记混用
- AI Bot对何时使用[AT]的理解不稳定
- 有时出现`<@&ROLE_ID>`裸格式

**影响**:
- @提及有时不触发（显示为纯文本）
- 对话连续性中断
- 用户体验不一致

---

## 根因分析

### 架构层面
```
当前结构 (扁平化):
prompts/multi_bot/
├── base/
│   ├── identity.md       # 通用模板 ✓
│   ├── capabilities.md   # 混入了赛博王朝特定内容 ✗
│   └── rules.md          # 通用规则 ✓
└── system_prompt.md      # 整体组装

问题: base/ 目录下混入了特定内容
```

### 标记层面
```
配置阶段: [AT]丞相     # YAML安全
Prompt阶段: @丞相      # 有时出现
代码阶段: <@&ID>      # 最终格式

问题: 三阶段标记不统一
```

---

## 解决方案

### 方案1: 三层架构分离

**目标**: 清晰分离通用能力与特定配置

**新结构**:
```
prompts/
├── README.md                    # 设计哲学文档
├── base/                        # Layer 1: 基础通用
│   ├── identity.md             # 身份模板（完全通用）
│   ├── capabilities_framework.md # 能力框架（无具体能力）
│   └── rules.md                # 通用行为准则
├── domain/                      # Layer 2: 领域通用
│   ├── multi_bot/              # Multi-Bot协作领域
│   │   ├── collaboration.md    # 跨Bot协作规范
│   │   ├── conversation.md     # 对话管理
│   │   ├── at_mention.md       # @机制详解
│   │   └── cross_channel.md    # 跨频道能力
│   └── discord/                # Discord平台
│       ├── platform.md         # 平台特性
│       └── formatting.md       # 消息格式
└── specific/                    # Layer 3: 特定配置
    └── cyber_dynasty/          # 赛博王朝
        ├── channel_aliases.md  # 频道别名
        ├── role_relations.md   # 角色关系
        └── at_scenarios.md     # @使用场景
```

### 方案2: [AT]标记标准化

**目标**: 全链路统一使用[AT]标记

**规范**:

| 阶段 | 标记 | 示例 | 说明 |
|------|------|------|------|
| Config | `[AT]` | `[AT]丞相` | YAML安全 |
| Prompt | `[AT]` | `[AT]丞相` | 统一标记 |
| 代码输出 | `<@&ID>` | `<@&14773...4239>` | Discord识别 |
| 用户看到 | `@` | `@丞相` | 蓝色可点击 |

**Prompt规则强化**:
```markdown
## [AT]标记使用规则

### 何时使用[AT]
需要对方回应时，必须使用[AT]标记：
1. **问句结尾**: "...结果如何？[AT]丞相"
2. **请求确认**: "...请丞相定夺。[AT]丞相"
3. **继续对话**: 需要对方继续参与

### 何时不使用[AT]
对话自然结束时，不使用[AT]：
1. **结论已定**: "善。" "已定。"
2. **单纯告知**: "臣已通知。"
3. **等待对方主动**: 非你提问

### 信号词对照表
| 需要[AT] | 自然结束 |
|----------|----------|
| 如何? | 善。 |
| 可否? | 已定。 |
| 请定夺 | 领命。 |
| 请过目 | 臣已办。 |
| 请示下 | 知道了。 |

### 格式规范
- 正确: `[AT]丞相 请定夺`
- 错误: `@丞相` (YAML解析错误)
- 错误: `AT丞相` (缺少方括号)
- 错误: `[AT]丞相:` (冒号紧跟)
```

---

## 实施步骤

### Step 1: 目录结构创建
```bash
mkdir -p prompts/{base,domain/multi_bot,domain/discord,specific/cyber_dynasty}
```

### Step 2: 基础层 (Layer 1)
**文件**: `prompts/base/identity.md`
```markdown
# 身份

你是 {{bot_name}}（{{bot_title}}）。

## 基本信息
- **Bot ID**: `{{bot_id}}`
- **角色 ID**: `{{bot_role_id}}`
- **名称**: {{bot_name}}
- **职位**: {{bot_title}}

## 人设
- **描述**: {{persona_description}}
- **性格**: {{persona_personality}}
- **说话风格**: {{persona_speech_style}}

## 系统角色
{{role_description}}
```

### Step 3: 领域层 (Layer 2)
**文件**: `prompts/domain/multi_bot/at_mention.md`
```markdown
# @提及机制

## 说明
本系统使用特殊标记 `[AT]` 来触发其他Bot。

## 转换规则
- 你写的: `[AT]丞相`
- 系统转换为: `<@&{{chengxiang_role_id}}>`
- Discord显示: @丞相 (蓝色可点击)

## 使用规则
... (详细规则)
```

### Step 4: 特定层 (Layer 3)
**文件**: `prompts/specific/cyber_dynasty/channel_aliases.md`
```markdown
# 频道别名

## 映射表
| 自然语言 | 配置键 | 频道ID |
|----------|--------|--------|
| 金銮殿、大殿、朝堂 | jinluan | {{jinluan_channel_id}} |
| 内阁、议事厅 | neige | {{neige_channel_id}} |
| 兵部、军事部 | bingbu | {{bingbu_channel_id}} |

## 使用场景
当用户说"去内阁"时，你应该前往 `{{neige_channel_id}}` 频道。
```

### Step 5: 动态渲染
更新 `role_bot.py` 中的Prompt组装逻辑：
```python
def _build_system_prompt(self) -> str:
    """动态组装System Prompt"""
    parts = []
    
    # Layer 1: Base
    parts.append(self._render_template("base/identity.md"))
    parts.append(self._render_template("base/rules.md"))
    
    # Layer 2: Domain (根据能力选择)
    if self.has_capability("multi_bot"):
        parts.append(self._render_template("domain/multi_bot/collaboration.md"))
        parts.append(self._render_template("domain/multi_bot/at_mention.md"))
    
    # Layer 3: Specific
    parts.append(self._render_template(f"specific/{self.org_id}/channels.md"))
    parts.append(self._render_template(f"specific/{self.org_id}/at_scenarios.md"))
    
    return "\n\n".join(parts)
```

---

## 验证测试

### 测试1: 三层架构
```
新增测试组织 "test_org":
1. 创建 config/organizations/test_org.yaml
2. 创建 prompts/specific/test_org/ (仅3个文件)
3. 验证自动继承 base/ 和 domain/ 的能力

期望: 无需修改 base/ 和 domain/ 即可运行新组织
```

### 测试2: [AT]标记
```
场景: 太尉计算后请求丞相确认

输入AI生成: "232456 = 2³ × 29057，[AT]丞相 请定夺"
代码转换后: "232456 = 2³ × 29057，<@&14773...4239> 请定夺"
Discord显示: "232456 = 2³ × 29057，@丞相 请定夺" (蓝色)

期望: @丞相显示为蓝色可点击链接
```

### 测试3: 对话连续性
```
场景: @丞相 @太尉 商议质因数分解

期望流程:
1. 太尉计算完成，[AT]丞相请求确认
2. 丞相同意，[AT]太尉通知回禀
3. 太尉回禀皇帝，对话自然结束

验证: 三轮对话，所有[AT]正确触发
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 重构期间服务中断 | 高 | 在分支开发，验证后合并 |
| Prompt长度增加 | 中 | 优化模板，移除冗余 |
| AI理解新格式 | 中 | 充分测试，必要时回滚 |
| 向后兼容 | 低 | 保留旧Prompt作为fallback |

---

## 参考

- **设计哲学**: `prompts/README.md`
- **当前配置**: `config/multi_bot.yaml`
- **当前Prompt**: `prompts/multi_bot/`
- **OpenClaw参考**: `/usr/lib/node_modules/openclaw/skills/`

---

*方案版本: v1.0*  
*创建日期: 2026-03-06*  
*状态: 待实施*
