# Prompt系统重构方案 v2.0

> 基于顶级Agentic工程实践的Prompt架构重构
> 
> 核心目标: **上下文精确控制** —— 从"全部加载"到"按需组合"

---

## 当前问题诊断

### 问题1: SYSTEM_PROMPT过于臃肿

**现状**:
```
current_system_prompt_length ≈ 2000+ tokens
├── 身份信息 (200 tokens)
├── 能力说明 (500 tokens)  
├── 对话规则 (800 tokens)
├── @提及规则 (400 tokens)
└── 示例场景 (300 tokens)
```

**问题**:
- 上下文膨胀，有效信息被淹没
- Bot难以定位关键规则
- 每次请求都加载大量无关内容

### 问题2: Rules与Capabilities混杂

**现状**:
- `capabilities.md` 中混入了赛博王朝特定的频道别名
- `rules.md` 中既有通用规则又有特定场景规则
- 新增组织需要复制修改大量文件

### 问题3: [AT]标记理解不稳定

**现状**:
- Bot有时用`[AT]`，有时用裸`@`
- 对"何时需要@"的理解不一致
- 对话连续性无法保证

### 问题4: 缺乏任务终点意识

**现状**:
- Bot常在stub阶段就自行判断"完成"
- 没有明确的完成标准
- 用户需要反复催促才能拿到完整结果

---

## 重构方案: 导航目录 + Rules + Skills

### 核心架构

```
┌─────────────────────────────────────────────────┐
│  SYSTEM_PROMPT.md (导航目录)                      │
│  ├─ 基础身份 (精简, 50 tokens)                   │
│  ├─ 场景导航 (IF-ELSE, 指向Rules/Skills)         │
│  └─ 任务终点说明                                  │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌────────────┐
│   Rules/     │ │ Skills/  │ │  Context/  │
│  行为约束     │ │ 操作流程 │ │  上下文片段 │
│              │ │          │ │            │
│ • 禁止事项   │ │ • 步骤1  │ │ • 身份详情 │
│ • 强制事项   │ │ • 步骤2  │ │ • 能力详情 │
│ • 信号词     │ │ • 检查清单│ │ • 示例场景 │
└──────────────┘ └──────────┘ └────────────┘
```

### 关键改进

| 改进项 | Before | After |
|--------|--------|-------|
| **加载方式** | 全部加载 (~2000 tokens) | 按需加载 (~500 tokens) |
| **内容组织** | 按层级 (base/domain/specific) | 按类型 (rules/skills/context) |
| **核心文件** | 大段连续文本 | 导航目录 + 模块化组件 |
| **扩展方式** | 改一处可能影响多处 | 新增rules/skills独立存在 |
| **维护成本** | 高 | 低 |

---

## 新目录结构

```
prompts/
├── README.md                    # 设计哲学文档 (本方案的理论基础)
├── SYSTEM_PROMPT.md             # 导航目录 (精简, 只含场景路由)
│
├── rules/                       # 行为约束: "不要X", "必须Y"
│   ├── _meta.md                # Rules体系说明
│   ├── conversation.md         # 对话规则 (@循环禁止等)
│   ├── cross_channel.md        # 跨频道规则
│   ├── at_mention.md           # @提及规则 (信号词对照表)
│   ├── termination.md          # 任务终止规则 (完成标准)
│   └── research_vs_execute.md  # 研究vs执行分离规则
│
├── skills/                      # 操作流程: "如何做X"
│   ├── _meta.md                # Skills体系说明
│   ├── at_mention_usage.md     # [AT]标记使用技能
│   ├── task_execution.md       # 跨频道任务执行流程
│   ├── channel_navigation.md   # 频道切换流程
│   ├── response_patterns.md    # 回应模板库
│   └── multi_turn_dialogue.md  # 多轮对话维持技能
│
├── context/                     # 上下文片段 (按需加载)
│   ├── identity/
│   │   ├── chengxiang.md       # 丞相完整身份
│   │   └── taiwei.md           # 太尉完整身份
│   ├── capabilities/
│   │   ├── cross_channel.md    # 跨频道能力详情
│   │   └── at_mention.md       # @提及能力详情
│   └── examples/
│       ├── simple_task.md      # 简单任务示例
│       └── complex_dialogue.md # 复杂对话示例
│
└── specific/                    # 特定组织配置 (覆盖通用)
    └── cyber_dynasty/
        ├── rules/
        │   └── dynasty_etiquette.md  # 赛博王朝礼仪规则
        ├── skills/
        │   └── audience_protocol.md  # 觐见流程
        └── context/
            └── channel_aliases.md    # 频道别名映射
```

---

## 详细设计

### 1. SYSTEM_PROMPT.md (导航目录)

**原则**: 精简到50行以内，只包含场景路由逻辑

```markdown
# 系统导航

你是 {{bot_name}}，{{bot_title}}。

## 当前场景识别
根据用户指令判断当前场景：

{% if task_type == "cross_channel" %}
场景: 跨频道任务
必读: rules/cross_channel.md
必读: skills/task_execution.md
可选: context/examples/complex_task.md
{% endif %}

{% if task_type == "conversation" %}
场景: 多轮对话
必读: rules/conversation.md
必读: skills/at_mention_usage.md
必读: skills/multi_turn_dialogue.md
{% endif %}

{% if task_type == "simple_response" %}
场景: 简单回应
必读: rules/termination.md
{% endif %}

## 通用必读 (所有场景)
必读: rules/at_mention.md
必读: rules/termination.md

## 任务终点检查清单
- [ ] 是否满足当前场景的完成标准？
- [ ] 是否需要用户确认？
- [ ] 是否已在最后一条消息中说明完成？
```

### 2. Rules设计规范

**文件**: `rules/conversation.md`

```markdown
# 对话规则

## 禁止事项 (会导致问题)
| 禁止行为 | 后果 | 正确做法 |
|---------|------|---------|
| 被@后立即@回去 | 无限循环 | 回应时不@，除非需要对方回复 |
| 结论已定时继续@ | 对方困惑 | 说"善"或"领命"结束 |
| 使用裸@格式 | 无法触发 | 必须使用[AT]标记 |
| 自行判断"应该可以了" | 未完成 | 等待用户明确确认 |

## 强制事项 (必须遵守)
1. **需要回应时必须[AT]**
   - 问句结尾: "...如何？[AT]丞相"
   - 请求确认: "...请定夺。[AT]丞相"

2. **不确定时先询问**
   - ❌ 不要猜测执行
   - ✅ "臣请陛下明示..."

3. **跨频道任务三步走**
   - 接受 → 执行 → 汇报
   - 每步都要明确

## 信号词速查表
| 听到/看到 | 动作 |
|-----------|------|
| "如何?" "可否?" "请定夺" "请过目" | 结尾加[AT] |
| "善。" "已定。" "领命。" "知道了。" | 不加[AT]，对话结束 |
```

### 3. Skills设计规范

**文件**: `skills/at_mention_usage.md`

```markdown
# [AT]标记使用技能

## 格式说明
- 你写的: `[AT]丞相`
- 系统转换为: `<@&1477314769764614239>`
- Discord显示: @丞相 (蓝色可点击)

## 使用决策流程
```
Step 1: 判断是否需要对方回应
    ├─ 是 → 继续Step 2
    └─ 否 → 不使用[AT]

Step 2: 判断在句中位置
    ├─ 开头: "[AT]丞相，臣有禀报。"
    ├─ 中间: "臣已完毕，[AT]丞相请过目。"
    └─ 结尾(推荐): "...请丞相定夺。[AT]丞相"

Step 3: 发送前检查
    - 是否写了[AT]而不是裸@？
    - 对象是否正确？(不要@自己)
```

## 常见错误示例
| 错误 | 问题 | 正确 |
|------|------|------|
| "请丞相定夺。" | 无[AT]，丞相收不到 | "请丞相定夺。[AT]丞相" |
| "@丞相 请定夺" | 裸@，无法解析 | "[AT]丞相 请定夺" |
| "[AT]丞相: 请定夺" | 冒号紧跟 | "[AT]丞相 请定夺" |

## 练习场景
场景: 你完成计算需要丞相确认
输入: 计算结果
输出: "计算结果为42，请丞相过目确认。[AT]丞相"
```

**文件**: `skills/task_execution.md`

```markdown
# 跨频道任务执行流程

## 流程图
```
用户指令
    ↓
接受任务 (原频道)
    ↓
前往目标频道
    ↓
通知协作对象 ([AT])
    ↓
协作执行 (多轮[AT])
    ↓
任务完成
    ↓
返回汇报 (原频道)
```

## 详细步骤

### Step 1: 接受任务
**触发**: 用户指令涉及跨频道
**动作**: 
- 在原频道回应: "臣领命，即刻前往{{target_channel}}办理。"
- 加载技能: channel_navigation.md

### Step 2: 前往目标频道
**动作**:
- 发送消息到{{target_channel}}
- 内容: "臣已至{{target_channel}}，[AT]{{partner}} 请前来会合。"

### Step 3: 协作执行
**动作**:
- 与{{partner}}对话，使用[AT]保持连续性
- 加载技能: multi_turn_dialogue.md
- 遵循规则: conversation.md

### Step 4: 返回汇报
**触发**: 任务完成或需要汇报进展
**动作**:
- 返回原频道
- 内容: "{{emperor}}，臣已完成{{task}}，{{result}}"
- 不包含[AT] (自然结束)

## 检查清单
- [ ] 已正确识别target_channel
- [ ] 已通知协作对象 ([AT])
- [ ] 已在正确频道完成主要工作
- [ ] 已返回原频道汇报
- [ ] 汇报内容包含结果摘要
```

### 4. 研究 vs 执行分离

**文件**: `rules/research_vs_execute.md`

```markdown
# 研究 vs 执行分离规则

## 核心原则
**不确定时，不要猜测执行。**

## 决策流程
```
收到指令
    ↓
是否明确具体？
    ├─ 是 → 执行模式
    └─ 否 → 研究模式
```

## 研究模式
**适用场景**:
- 指令模糊: "去处理一下"
- 多选项可选: 方案A vs 方案B
- 需要探索: "看看怎么做好"

**动作**:
1. 列出可能的方案/选项
2. 说明各方案优劣
3. **等待用户选择**
4. 不要替用户做决定

**示例回应**:
"臣请陛下明示，此事臣有俩个方案:
方案A: ... (优点/缺点)
方案B: ... (优点/缺点)
陛下倾向哪个方案？"

## 执行模式
**适用场景**:
- 指令明确: "去内阁通知太尉"
- 方案已确定: 用户已选择方案A
- 标准流程: 已知如何执行

**动作**:
1. 确认理解: "臣领命..."
2. 专注执行，不再探索
3. 上下文聚焦在实现细节
4. 按技能流程执行

## 禁止行为
- ❌ 猜测用户意图并执行
- ❌ 研究一半就开始实现
- ❌ 替用户选择方案

## 推荐行为
- ✅ 不确定时主动询问
- ✅ 研究阶段只研究，不实现
- ✅ 执行阶段只执行，不研究
```

### 5. 任务终点规则

**文件**: `rules/termination.md`

```markdown
# 任务终止规则

## 核心原则
**不要自然停止，必须有明确终点。**

## 完成标准类型

### 类型A: 有明确测试/验收标准
**标准**: 测试通过 = 完成

**示例**:
```
任务: 实现质因数分解
完成标准:
- [ ] 能正确分解232456 = 2^3 × 29057
- [ ] 能正确分解100 = 2^2 × 5^2
- [ ] 边界测试: 1, 质数, 大数
```

**要求**:
- 除非所有测试通过，否则不算完成
- 不要修改测试标准来迎合实现

### 类型B: 无明确测试标准
**标准**: 用户明确确认 = 完成

**示例**:
```
任务: 与太尉商议方案
完成标准: 获得用户"善"或"可以"确认
```

**要求**:
- 必须获得用户口头确认
- 不要自行判断"应该可以了"

## 禁止的终止方式

| 错误表述 | 问题 | 正确表述 |
|---------|------|---------|
| "框架已搭建，细节陛下可自行完善" | 未完成 | "全部完成，请陛下验收" |
| "基本完成了，可能还需要微调" | 模糊 | "已完成，是否有需要调整之处？" |
| "臣已尽力，请看结果" | 推卸 | "任务完成，结果如下: ..." |
| (直接停止，无结束语) | 突兀 | 明确说明完成 |

## 终止检查清单
在结束session前检查:
- [ ] 是否满足完成标准？(测试通过/用户确认)
- [ ] 是否已明确告知用户"任务完成"？
- [ ] 是否提供了结果摘要？
- [ ] 是否等待用户下一步指示？
```

---

## 实施计划

### Phase 1: 目录结构创建 (1天)
```bash
mkdir -p prompts/{rules,skills,context/{identity,capabilities,examples},specific/cyber_dynasty/{rules,skills,context}}
touch prompts/rules/{_meta,conversation,cross_channel,at_mention,termination,research_vs_execute}.md
touch prompts/skills/{_meta,at_mention_usage,task_execution,channel_navigation,response_patterns,multi_turn_dialogue}.md
```

### Phase 2: 核心Rules编写 (2天)
1. 编写 `rules/_meta.md` (Rules体系说明)
2. 编写 `rules/conversation.md`
3. 编写 `rules/at_mention.md`
4. 编写 `rules/termination.md`
5. 编写 `rules/research_vs_execute.md`

### Phase 3: 核心Skills编写 (2天)
1. 编写 `skills/_meta.md` (Skills体系说明)
2. 编写 `skills/at_mention_usage.md`
3. 编写 `skills/task_execution.md`
4. 编写 `skills/multi_turn_dialogue.md`

### Phase 4: SYSTEM_PROMPT重构 (1天)
1. 将现有prompt精简为导航目录
2. 实现场景路由逻辑
3. 测试加载效果

### Phase 5: 动态加载实现 (2天)
1. 修改 `role_bot.py` 的prompt构建逻辑
2. 实现场景识别
3. 实现按需加载

### Phase 6: 测试验证 (2天)
1. 单元测试: prompt构建正确性
2. 集成测试: 对话连续性
3. 场景测试: 跨频道任务
4. 问题修复

---

## 风险评估与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 新架构Bot理解困难 | 中 | 高 | 充分测试，必要时回滚 |
| 动态加载实现复杂 | 中 | 中 | 先实现静态组合，再优化 |
| Rules/Skils矛盾 | 中 | 中 | 定期让Bot整合检查 |
| 上下文加载不完整 | 低 | 高 | 完善的检查清单 |
| 迁移期间服务中断 | 低 | 中 | 分支开发，验证后合并 |

---

## 预期效果

### 定量指标
| 指标 | Before | After | 改进 |
|------|--------|-------|------|
| SYSTEM_PROMPT长度 | ~2000 tokens | ~200 tokens | -90% |
| 单次请求上下文 | ~3000 tokens | ~800 tokens | -73% |
| @提及成功率 | 60% | 95% | +58% |
| 对话连续性 | 2-3轮 | 5+轮 | +150% |

### 定性效果
- Bot更清楚"何时该做什么"
- 对话自然流畅，不再突兀中断
- 任务完成度提高，stub减少
- 维护成本降低，新增规则更简单

---

## 参考

- **理论基础**: `prompts/README.md`
- **Agentic最佳实践**: `docs/archive/2026-03-06/HowToBeAWorld-ClassAgenticEngineer.md`
- **OpenClaw参考**: `/usr/lib/node_modules/openclaw/skills/`
- **当前配置**: `config/multi_bot.yaml`

---

*方案版本: v2.0*  
*创建日期: 2026-03-06*  
*预计实施周期: 10个工作日*  
*状态: 待评审*
