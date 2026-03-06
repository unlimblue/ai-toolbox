# Prompt系统设计哲学 v2.0

> 融合OpenClaw技能系统与顶级Agentic工程实践的分层组合架构
> 
> 核心理念: **上下文就是一切** —— 只给Bot完成任务所需的精确信息

---

## 核心思想演进

### v1.0 → v2.0 的关键升级

| v1.0 (分层组合) | v2.0 (上下文精确控制) |
|-----------------|----------------------|
| 三层架构加载所有内容 | 按需加载，精确控制上下文 |
| 大段Prompt一次性注入 | SYSTEM_PROMPT作为**导航目录** |
| 静态模板渲染 | 动态Rules + Skills组合 |
| 研究实现混在一起 | **研究 vs 执行分离** |

### 从文章学到的关键原则

1. **保持简洁** —— 不是堆砌，而是精简到刚好够用
2. **上下文膨胀是敌人** —— 每多一个无关的skill都在降低性能
3. **Rules + Skills 体系** —— 约束与流程分离，按需组合
4. **导航目录模式** —— SYSTEM_PROMPT只包含IF-ELSE，指向具体内容
5. **定期清理整合** —— 当rules/skills矛盾时，主动整合优化

---

## 新架构: 导航目录 + Rules + Skills

### 1. SYSTEM_PROMPT.md = 导航目录

**原则**: 精简到只包含导航逻辑，告诉Bot在什么场景下去哪里找上下文

```markdown
# 系统导航

你是 {{bot_name}}。

## 基础身份
{{identity_summary}}

## 能力导航
根据当前场景，读取对应的Rules和Skills：

{% if scene == "cross_channel_task" %}
必读: rules/cross_channel.md
必读: skills/execute_task.md
{% endif %}

{% if scene == "multi_bot_conversation" %}
必读: rules/conversation.md  
必读: skills/at_mention.md
{% endif %}

## 任务终点判定
- 有明确测试/验收标准 → 测试通过 = 完成
- 无明确标准 → 用户确认 = 完成
- 不要自然停止，必须明确终点
```

### 2. Rules = 行为约束

**原则**: "不要做X" 或 "在Y场景下必须Z"

```markdown
# rules/conversation.md

## 禁止事项
- ❌ 不要在自己被@时立即@回去（会导致循环）
- ❌ 不要在结论已定时继续@对方
- ❌ 不要使用@裸格式，必须使用[AT]标记

## 强制事项
- ✅ 需要回应时，必须在句末使用[AT]标记
- ✅ 跨频道任务必须先接受，再执行，最后汇报
- ✅ 不确定时，先询问而非假设

## 信号词规则
| 听到/看到 | 动作 |
|-----------|------|
| "如何?" "可否?" "请定夺" | 结尾加[AT] |
| "善。" "已定。" "领命。" | 不加[AT]，对话结束 |
```

### 3. Skills = 操作流程

**原则**: "如何做X" 的编码化流程

```markdown
# skills/execute_task.md

## 跨频道任务执行流程

### Step 1: 接受任务
在当前频道回应: "臣领命，即刻前往{{target_channel}}办理。"

### Step 2: 前往目标频道
发送消息到{{target_channel}}: "臣已至{{target_channel}}，[AT]{{partner_name}} 请前来会合。"

### Step 3: 协作执行
与{{partner_name}}在{{target_channel}}商议，使用[AT]保持对话。

### Step 4: 汇报结果
返回原频道: "{{emperor_name}}，臣已完成{{task_summary}}，结果如下: {{result}}"

## 检查清单
- [ ] 已通知协作对象
- [ ] 已在正确频道完成任务
- [ ] 已总结可汇报的结果
```

```markdown
# skills/at_mention.md

## [AT]标记使用技能

### 格式转换
- 你写的: `[AT]丞相`
- 系统转换为: `<@&1477314769764614239>`
- Discord显示为: @丞相 (蓝色可点击)

### 使用决策树
```
是否需要对方回应?
├─ 是 → 使用[AT]
│   ├─ 问句结尾: "...如何？[AT]丞相"
│   ├─ 请求确认: "...请定夺。[AT]丞相"
│   └─ 继续讨论: "...请补充。[AT]丞相"
│
└─ 否 → 不使用[AT]
    ├─ 结论已定: "善。"
    ├─ 单纯告知: "臣已通知。"
    └─ 等待对方主动
```

### 常见错误
- ❌ "...请丞相定夺。" (无[AT]，丞相收不到)
- ✅ "...请丞相定夺。[AT]丞相"
```

---

## 上下文精确控制策略

### 1. 场景化加载

不是所有Bot都需要所有Rules和Skills，根据当前场景动态选择：

```python
def build_prompt(bot_id, scene, context):
    parts = ["system/navigation.md"]  # 导航目录
    
    # 根据场景加载
    if scene == "cross_channel":
        parts.append("rules/cross_channel.md")
        parts.append("skills/task_execution.md")
    
    if scene == "conversation":
        parts.append("rules/conversation.md")
        parts.append("skills/at_mention.md")
    
    # 特定组织覆盖
    parts.append(f"specific/{org_id}/custom_rules.md")
    
    return combine(parts)
```

### 2. 研究 vs 执行分离

**问题**: Bot不确定如何做时，会"连点成线"、自己脑补，导致幻觉

**解决方案**:
```markdown
## 研究 vs 执行分离规则

### 当你不确定时
如果用户指令模糊，或你不确定最佳方案:
1. **不要猜测执行**
2. **先回应**: "臣请陛下明示..."
3. **或询问**: "陛下是指A方案还是B方案？"

### 研究模式
如果需要探索多个选项:
- 在当前对话中列出选项
- 等待用户选择
- 不要替用户做决定

### 执行模式
一旦方案确定:
- 专注执行，不再探索其他选项
- 上下文聚焦在实现细节
```

### 3. 任务终点明确化

**防止Bot只写stub就停止**:

```markdown
## 任务完成标准

### 有明确测试的场景
除非以下测试通过，否则任务未完成:
- [ ] 测试1: ...
- [ ] 测试2: ...

### 无明确测试的场景
必须获得用户明确确认:
- "善" / "可以" / "就这样"
- 不要自行判断"应该可以了"

### 禁止提前终止
- ❌ "框架已搭建，细节陛下可自行完善"
- ❌ "基本完成了，可能还需要微调"
- ✅ "全部完成，请陛下验收"
```

---

## 目录结构 v2.0

```
prompts/
├── README.md                    # 本文件: 设计哲学
├── SYSTEM_PROMPT.md             # 导航目录 (精简, 只含IF-ELSE)
├── 
├── rules/                       # 行为约束 (不要X, 必须Y)
│   ├── _meta.md                # Rules使用说明
│   ├── conversation.md         # 对话规则
│   ├── cross_channel.md        # 跨频道规则
│   ├── at_mention.md           # @提及规则
│   └── termination.md          # 任务终止规则
│
├── skills/                      # 操作流程 (如何做X)
│   ├── _meta.md                # Skills使用说明
│   ├── task_execution.md       # 任务执行流程
│   ├── at_mention_usage.md     # [AT]标记使用
│   ├── channel_navigation.md   # 频道切换流程
│   └── response_templates.md   # 回应模板库
│
├── context/                     # 上下文片段 (可选加载)
│   ├── identity/               # 身份信息
│   ├── capabilities/           # 能力说明
│   └── examples/               # 示例场景
│
└── specific/                    # 特定组织配置
    └── cyber_dynasty/
        ├── rules/               # 赛博王朝特定规则
        ├── skills/              # 赛博王朝特定技能
        └── context/             # 赛博王朝特定上下文
```

---

## 与v1.0的对比

| 维度 | v1.0 (静态分层) | v2.0 (动态组合) |
|------|-----------------|-----------------|
| **核心文件** | 大段prompt一次性加载 | SYSTEM_PROMPT作为导航目录 |
| **内容组织** | 按层级(base/domain/specific) | 按类型(rules/skills/context) |
| **加载方式** | 全部加载，模板变量替换 | 按需加载，场景化组合 |
| **扩展方式** | 新增层级文件 | 新增rules或skills |
| **维护成本** | 高(改一处可能影响多处) | 低(rules/skills独立) |
| **上下文控制** | 容易膨胀 | 精确控制，只加载需要的 |

---

## 实施建议

### 迁移路径

1. **Phase 1**: 创建新的目录结构
2. **Phase 2**: 将现有prompt拆分为rules和skills
3. **Phase 3**: 重写SYSTEM_PROMPT为导航目录
4. **Phase 4**: 实现动态加载逻辑
5. **Phase 5**: 测试验证，逐步迁移

### 避免的错误

- ❌ SYSTEM_PROMPT写得太长，失去导航意义
- ❌ Rules和Skills职责不清，互相重叠
- ❌ 加载太多skills导致上下文膨胀
- ❌ 没有定期清理，rules/skills堆积矛盾

### 最佳实践

- ✅ SYSTEM_PROMPT控制在50行以内，只含导航
- ✅ 每个Rule只解决一个具体问题
- ✅ 每个Skill只编码一个完整流程
- ✅ 定期(如每月)让Bot帮忙整合rules/skills

---

## 参考

- **OpenClaw Skills**: `/usr/lib/node_modules/openclaw/skills/`
- **Agentic工程最佳实践**: `docs/archive/2026-03-06/HowToBeAWorld-ClassAgenticEngineer.md`
- **当前配置**: `config/multi_bot.yaml`

---

*设计版本: v2.0*  
*更新日期: 2026-03-06*  
*核心升级: 从静态分层到动态组合，从全部加载到精确控制*
