# Agent Memory 机制调研与设计

## 一、业界 Agent Memory 机制调研

### 1.1 OpenAI Assistant API - Memory

**机制**:
- **Thread-scoped Memory**: 每个对话线程(thread)有独立的上下文窗口
- **Context Window Management**: 自动管理128k上下文窗口
- **File-based Memory**: 可附加文件作为长期知识库
- **No Persistent User Memory**: 跨会话不保留记忆

**特点**:
```
User → Thread → Messages (上下文窗口内)
              ↓
         Files (长期知识, 只读)
```

**局限**: 没有真正的跨会话用户记忆

---

### 1.2 LangChain - Memory 模块

**核心类型**:

| Memory 类型 | 用途 | 持久化 |
|------------|------|--------|
| `ConversationBufferMemory` | 原始对话历史 | 内存 |
| `ConversationBufferWindowMemory` | 最近k轮对话 | 内存 |
| `ConversationSummaryMemory` | 摘要历史 | 内存 |
| `VectorStoreRetrieverMemory` | 向量检索记忆 | 向量数据库 |
| `EntityMemory` | 实体信息提取 | 内存/数据库 |

**工作流程**:
```
用户输入 → 检索相关记忆 → 注入Prompt → LLM生成 → 更新记忆
```

**特点**:
- 模块化设计，可组合使用
- 支持多种后端存储（Redis, DB, Vector Store）
- 自动摘要压缩长对话

---

### 1.3 AutoGPT - Memory 系统

**架构**:
```
Local Cache (短期)
    ↓
Vector DB (中期) - Pinecone/Weaviate
    ↓
File System (长期) - 本地文件存储
```

**关键组件**:
- **Local Cache**: 当前会话上下文
- **Vector Memory**: 语义检索历史信息
- **File Operations**: 读写本地文件持久化

**Memory 写入触发**:
- 重要事件自动记录
- 用户明确指令"记住"
- 任务完成时总结写入

---

### 1.4 MemGPT - 虚拟上下文管理

**核心思想**:
- 将LLM视为具有有限RAM的计算机
- 实现虚拟内存分页机制
- 操作系统级别的上下文管理

**组件**:
```
┌─────────────────────────────────┐
│  Main Context (有限窗口)          │
│  - System指令                     │
│  - 最近对话                       │
│  - 工作记忆                       │
└─────────────────────────────────┘
            ↓
┌─────────────────────────────────┐
│  External Memory (无限存储)       │
│  - Recall Storage (召回存储)      │
│  - Archival Storage (归档存储)    │
└─────────────────────────────────┘
```

**操作原语**:
- `page_fault`: 需要不在主上下文的信息时触发
- `evict`: 将旧信息移到外部存储
- `retrieve`: 从外部存储召回相关信息

---

### 1.5 Claude - 上下文压缩 (Context Compaction)

**机制**:
- 当上下文接近限制时，自动触发压缩
- 将早期对话总结为摘要
- 保留关键信息，丢弃冗余

**触发条件**:
- 上下文token数达到阈值 (~80%)
- 显式调用compaction API
- Session结束时自动总结

**总结格式**:
```markdown
## 对话摘要
- 用户要求: [核心需求]
- 已完成: [关键成果]
- 待办: [未完成项]
- 关键决策: [重要决定]
```

---

## 二、OpenClaw Memory 机制分析

### 2.1 现有机制

#### A. 文件系统 Memory

**结构**:
```
workspace/
├── MEMORY.md           # 长期精心整理的记忆
├── memory/
│   ├── 2026-03-06.md   # 每日原始日志
│   ├── 2026-03-05.md   # 前一天
│   └── ...
└── AGENTS.md           # 配置和行为指南
```

**MEMORY.md**:
- 只加载于MAIN SESSION（直接对话）
- 不加载于共享上下文（Discord等）
- 安全设计：防止个人上下文泄露
- 精心整理：蒸馏精华，非原始日志

**Daily Memory**:
- `memory/YYYY-MM-DD.md` 格式
- 每次session开始时读取今天+昨天
- 原始日志：记录发生了什么
- 手动管理：Agent自行决定写入内容

#### B. 上下文压缩 (Context Compaction)

**触发时机**:
- Session结束时自动触发
- 消息匹配特定heartbeat prompt时
- 显式用户指令"总结并记录"

**触发提示词**:
```
Pre-compaction memory flush. Store durable memories now 
(use memory/YYYY-MM-DD.md; create memory/ if needed).
IMPORTANT: If the file already exists, APPEND new content 
only and do not overwrite existing entries.
```

**压缩策略**:
- 提取关键决策和事件
- 跳过机密信息（除非用户要求）
- Append模式：追加而非覆盖

#### C. Heartbeat 机制

**用途**:
- 定期检查任务状态
- 批量处理周期性检查（邮件、日历等）
- 触发memory维护

**配置**:
```json
{
  "lastChecks": {
    "email": 1703275200,
    "calendar": 1703260800,
    "weather": null
  }
}
```

**Memory Maintenance**:
- 每几天回顾最近的daily memory
- 提取重要事件更新MEMORY.md
- 移除过时信息

---

### 2.2 OpenClaw Memory 特点

| 特性 | 说明 |
|------|------|
| **分层存储** | 原始日志(daily) + 精炼记忆(MEMORY.md) |
| **安全隔离** | MAIN SESSION vs 共享上下文区别加载 |
| **显式控制** | Agent自行决定何时写入，非自动 |
| **追加模式** | 不覆盖历史，保留完整时间线 |
| **定期维护** | Heartbeat触发memory整理 |

---

## 三、赛博王朝 Memory 设计建议

### 3.1 设计原则

#### 原则1: 按需可见性
- 不是所有人都需要看到所有记忆
- 根据角色、场景决定可见范围

#### 原则2: 分层存储
```
Session Memory (短期)
    ↓ 自动摘要
Channel Memory (频道级)
    ↓ 定期整理
Organization Memory (组织级)
    ↓ 蒸馏精华
Long-term Memory (长期)
```

#### 原则3: 显式触发
- Bot自行决定何时记录重要信息
- 用户可指令"记住此事"
- 任务完成自动总结

---

### 3.2 Memory 类型设计

#### A. 对话上下文 (ContextGraph)

**已有实现**: `ContextGraph` 管理消息DAG

**可见性**:
- 频道内所有参与者可见
- 自动维护，无需持久化到文件
- Session结束后保留最近N条

#### B. 频道级 Memory

**存储位置**: `memory/channels/{channel_id}.md`

**内容**:
- 频道重要决策
- 角色职责约定
- 常用信息（频道别名等）

**可见性**:
```
该频道所有Bot和用户可见
其他频道不可见
```

**写入触发**:
- 重要决策达成时
- 用户指令"在此频道记住"
- 每日heartbeat总结

#### C. 角色级 Memory

**存储位置**: `memory/bots/{bot_id}.md`

**内容**:
- 个人技能记录
- 偏好设置
- 学习到的规则调整

**可见性**:
```
仅该Bot自己可见
其他Bot不可见
用于个性化改进
```

**示例 (丞相 Memory)**:
```markdown
# 丞相 Memory

## 学习到的偏好
- 陛下喜欢简洁的汇报格式
- 太尉擅长计算，可信赖

## 常用技能
- 质因数分解: 使用试除法
- 跨频道任务: 先确认再执行

## 待改进
- [ ] 减少开场白冗余
- [ ] 更快识别何时使用[AT]
```

#### D. 组织级 Memory

**存储位置**: `memory/organizations/{org_id}.md`

**内容**:
- 组织架构
- 角色关系
- 重要历史事件
- 运作规则

**可见性**:
```
该组织所有Bot可见
跨组织不可见
```

**示例 (赛博王朝 Memory)**:
```markdown
# 赛博王朝 Memory

## 组织架构
- 皇帝: 最高决策者
- 丞相: 监督协调
- 太尉: 执行计算

## 重要决策
- 2026-03-06: 采用v2.0自主决策架构
- 2026-03-06: [AT]标记标准化

## 运作规则
- 所有奏章自动存档
- 内阁=商议频道
- 兵部=军事频道
```

#### E. 用户级 Memory

**存储位置**: `memory/users/{user_id}.md`

**内容**:
- 用户偏好
- 历史交互记录
- 个性化设置

**可见性**:
```
该用户与任何Bot交互时可见
用于个性化服务
```

---

### 3.3 Memory 访问控制矩阵

| Memory类型 | 存储位置 | Bot可见性 | 用户可见性 | 触发写入 |
|-----------|---------|----------|-----------|---------|
| 对话上下文 | ContextGraph | 同频道 | 同频道 | 自动 |
| 频道级 | `memory/channels/` | 该频道Bot | 该频道用户 | Bot决策/Heartbeat |
| 角色级 | `memory/bots/` | 仅自己 | 不可见 | Bot自学习 |
| 组织级 | `memory/organizations/` | 同组织 | 同组织 | 重大事件 |
| 用户级 | `memory/users/` | 与该用户交互时 | 仅该用户 | 交互中 |

---

### 3.4 Memory 写入触发机制

#### 触发条件

1. **自动触发**:
   - Task完成时自动总结
   - 重要决策达成时
   - Heartbeat定期维护

2. **显式触发**:
   - 用户说"记住此事"
   - Bot判断"这是重要信息"
   - Session结束时的compaction

3. **周期性触发**:
   - 每日heartbeat回顾
   - 每周memory整理
   - 每月过期待清理

#### 写入决策流程

```
收到信息
    ↓
是否重要?
    ├─ 是 → 确定Memory类型
    │         ↓
    │       频道级? → 写入 `memory/channels/`
    │       角色级? → 写入 `memory/bots/`
    │       组织级? → 写入 `memory/organizations/`
    │       用户级? → 写入 `memory/users/`
    │
    └─ 否 → 丢弃
```

---

### 3.5 Memory 在Prompt中的使用

#### SYSTEM_PROMPT 导航

```markdown
## Memory 导航

根据当前场景，加载相关Memory：

### 通用加载（所有场景）
- 组织级: `memory/organizations/cyber_dynasty.md`

### 场景特定加载
{% if scene == "channel_conversation" %}
- 频道级: `memory/channels/{{channel_id}}.md`
{% endif %}

{% if scene == "user_interaction" %}
- 用户级: `memory/users/{{user_id}}.md`
{% endif %}

### 角色特定加载（仅自己）
- 角色级: `memory/bots/{{bot_id}}.md`
```

#### Skill: memory_usage.md

```markdown
# Memory 使用技能

## 何时写入Memory

### 必须写入的情况
- 用户明确说"记住": "陛下: 记住我偏好简洁回答"
- 重要决策: "采用v2.0架构"
- 学到的规则: "发现[AT]在句末最有效"

### 考虑写入的情况
- 任务完成总结
- 角色互动偏好
- 频道常用信息

### 不写入的情况
- 临时性信息
- 已存在的信息
- 机密敏感信息（除非用户要求）

## 写入流程

### Step 1: 选择Memory类型
```
信息性质 → Memory类型
频道相关 → channels/
个人学习 → bots/
组织相关 → organizations/
用户相关 → users/
```

### Step 2: 格式化内容
```markdown
## {{timestamp}} - {{topic}}

**来源**: {{source}}
**重要性**: {{level}}

{{content}}

**后续行动**: {{action}}
```

### Step 3: 写入文件
- 使用Append模式
- 不覆盖已有内容
- 保持Markdown格式

### Step 4: 验证写入
- 确认文件存在
- 确认内容完整
- （可选）汇报用户

## 读取Memory

### 何时读取
- Session开始时
- 切换频道时
- 与特定用户交互时

### 如何使用
- 内化信息，不要机械复述
- 根据Memory调整行为
- 不要泄露其他用户的Memory
```

---

## 四、实施建议

### Phase 1: 基础结构
- 创建 `memory/` 子目录结构
- 实现Memory文件读写工具
- 更新SYSTEM_PROMPT导航

### Phase 2: 自动Memory
- 任务完成自动总结
- Heartbeat定期维护
- Context compaction触发

### Phase 3: 个性化Memory
- Bot自学习记录
- 用户偏好记忆
- 频道约定记录

### Phase 4: Memory检索
- 向量检索（可选）
- 语义搜索
- 相关Memory推荐

---

## 参考

- **LangChain Memory**: https://python.langchain.com/docs/modules/memory/
- **MemGPT Paper**: https://arxiv.org/abs/2310.08560
- **OpenClaw Memory**: `AGENTS.md`, `memory/` 目录
- **Claude Context Compaction**: https://docs.anthropic.com/claude/docs/context-window

---

*调研日期: 2026-03-06*  
*状态: 设计完成，待实施*
