# AI-Toolbox 设计哲学

**版本**: 2.0  
**核心**: 自主决策架构

---

## 核心思想

### 从命令执行到自主协作

```mermaid
flowchart LR
    subgraph 传统架构[传统架构：命令执行]
        A[用户指令] --> B[系统解析]
        B --> C[创建任务]
        C --> D[Bot执行]
        style B fill:#f99
        style C fill:#f99
    end
    
    subgraph 新架构[新架构：自主决策]
        E[用户指令] --> F[系统转发]
        F --> G[AI理解]
        G --> H[AI决策]
        H --> I[AI执行]
        style F fill:#9f9
        style G fill:#9f9
        style H fill:#9f9
        style I fill:#9f9
    end
```

**转变**: 红色=硬编码限制，绿色=自主灵活

---

## 三大设计原则

### 1. 无硬编码

```mermaid
mindmap
  root((无硬编码))
    不解析指令
      不识别关键词
      不预设模式
    不创建任务
      无任务模板
      无固定流程
    不限制行为
      AI决定频道
      AI决定@谁
      AI决定内容
```

**为什么**: 让AI像人类一样自然理解和响应

### 2. 上下文感知

```mermaid
graph TB
    subgraph ContextGraph[Context Graph]
        M1[消息1] --> M2[消息2]
        M1 --> M3[消息3]
        M2 --> M4[消息4]
        M3 --> M4
        
        style M1 fill:#bbf
        style M2 fill:#bbf
        style M3 fill:#bbf
        style M4 fill:#bbf
    end
    
    subgraph Visibility[可见性]
        V1[丞相可见] --> V2[太尉可见]
        V3[自动传播] --> V4[继承可见]
    end
```

**机制**: 图结构存储 + 自动可见性传播

### 3. 配置驱动

```yaml
# 新增Bot只需配置，无需代码
bots:
  new_bot:
    name: "新角色"
    persona:
      description: "角色描述"
      # AI自主决策指南
      custom_instructions: |
        你可以...
```

---

## 系统思维

### 单一职责

| 组件 | 职责 | 边界 |
|------|------|------|
| **系统层** | 消息路由 | 不解析、不决策 |
| **上下文层** | 存储与提取 | 不干预决策 |
| **AI层** | 理解与决策 | 完全自主 |

```mermaid
flowchart TD
    S[系统层：转发] --> C[上下文层：存储]
    C --> A[AI层：决策]
    A --> E[执行]
    
    style S fill:#ff9
    style C fill:#9ff
    style A fill:#9f9
```

---

## 设计价值

| 维度 | 传统方案 | 自主决策 |
|------|---------|----------|
| **灵活性** | 预设指令模式 | 任意自然语言 |
| **扩展性** | 改代码添加功能 | 配置即可 |
| **智能性** | 固定响应 | 自适应决策 |
| **维护性** | 硬编码难维护 | 配置化易维护 |

---

*设计哲学文档，指导架构演进*
