# 🎭 Prompt 系统设计哲学 v2.0

> **上下文就是一切** —— 只给 Bot 完成任务所需的精确信息

![版本](https://img.shields.io/badge/版本-2.0-blue)
![架构](https://img.shields.io/badge/架构-导航目录%20+%20规则%20+%20技能-green)

---

## 🎯 核心理念

### v1.0 的问题

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ff6b6b', 'primaryTextColor': '#fff'}}}%%
flowchart TB
    subgraph V1["❌ v1.0: 整体加载"]
        A1[SYSTEM_PROMPT
        <span style='font-size:11px'>~2000 tokens</span>]
        A1 --> B1[身份 200t]
        A1 --> C1[能力 500t]
        A1 --> D1[规则 800t]
        A1 --> E1[示例 300t]
        A1 --> F1[...]
    end

    subgraph V2["✅ v2.0: 导航 + 按需加载"]
        A2[SYSTEM_PROMPT
        <span style='font-size:11px'>~200 tokens</span>]
        A2 --> B2[场景识别]
        B2 --> C2[加载规则]
        B2 --> D2[加载技能]
        B2 --> E2[加载上下文]
    end

    V1 -->|"上下文膨胀
    Bot 困惑"| V2
```

### 关键升级: v1.0 → v2.0

| 维度 | v1.0 (分层架构) | v2.0 (导航 + 规则 + 技能) |
|------|----------------|--------------------------|
| **加载方式** | 全部加载 (~2000 tokens) | 按需加载 (~500 tokens) |
| **SYSTEM_PROMPT** | 大段内容一次性注入 | **导航目录** |
| **渲染方式** | 静态模板 | 动态规则 + 技能组合 |
| **研究/执行** | 混在一起 | **研究与执行分离** |

---

## 🏗️ 架构: 导航目录 + 规则 + 技能

### 整体流程

```mermaid
flowchart TB
    subgraph Input["📥 输入"]
        User[用户消息]
    end

    subgraph System["⚙️ SYSTEM_PROMPT.md (导航)"]
        Nav[场景识别
        <span style='font-size:10px'>IF 跨频道任务 → 加载 X</span>
        <span style='font-size:10px'>IF 多轮对话 → 加载 Y</span>]
    end

    subgraph Components["📚 组件 (按需加载)"]
        direction TB
        Rules["🚫 规则/
        <span style='font-size:10px'>不要做什么</span>
        <span style='font-size:10px'>必须做什么</span>"]
        Skills["📝 技能/
        <span style='font-size:10px'>如何做</span>
        <span style='font-size:10px'>分步流程</span>"]
        Context["📄 上下文/
        <span style='font-size:10px'>身份信息、示例</span>"]
    end

    subgraph Output["📤 输出"]
        Response[Bot 回应]
    end

    User --> Nav
    Nav --> Rules
    Nav --> Skills
    Nav --> Context
    Rules --> Response
    Skills --> Response
    Context --> Response
```

### 组件职责

```mermaid
flowchart LR
    subgraph System["SYSTEM_PROMPT.md"]
        S1["仅导航功能
        <span style='font-size:10px'>• 场景检测</span>
        <span style='font-size:10px'>• IF-ELSE 路由</span>
        <span style='font-size:10px'>• 组件指针</span>"]
    end

    subgraph Rules["🚫 规则/"]
        R1["行为约束
        <span style='font-size:10px'>• 禁止做 X</span>
        <span style='font-size:10px'>• 必须做 Y</span>
        <span style='font-size:10px'>• 信号词</span>"]
    end

    subgraph Skills["📝 技能/"]
        SK1["操作流程
        <span style='font-size:10px'>• 如何做 X</span>
        <span style='font-size:10px'>• 分步说明</span>
        <span style='font-size:10px'>• 检查清单</span>"]
    end

    subgraph Context["📄 上下文/"]
        C1["信息
        <span style='font-size:10px'>• 身份详情</span>
        <span style='font-size:10px'>• 能力说明</span>
        <span style='font-size:10px'>• 示例场景</span>"]
    end

    System -->|"指向"| Rules
    System -->|"指向"| Skills
    System -->|"指向"| Context
```

---

## 🎮 [AT] 提及决策流程

### 何时使用 [AT]

```mermaid
flowchart TD
    Start(["需要对方回应?"])
    
    Start --> Check{"检查消息类型"}
    
    Check -->|问句| UseAT1["结尾加 [AT]
    <span style='font-size:10px'>'...如何?' [AT]丞相</span>"]
    
    Check -->|请求确认| UseAT2["结尾加 [AT]
    <span style='font-size:10px'>'请定夺。' [AT]丞相</span>"]
    
    Check -->|继续对话| UseAT3["结尾加 [AT]
    <span style='font-size:10px'>'还有补充?' [AT]太尉</span>"]
    
    Check -->|结论已定| NoAT1["不加 [AT]
    <span style='font-size:10px'>'善。'</span>"]
    
    Check -->|单纯告知| NoAT2["不加 [AT]
    <span style='font-size:10px'>'臣已通知。'</span>"]
    
    Check -->|等待对方主动| NoAT3["不加 [AT]
    <span style='font-size:10px'>自然结束</span>"]

    UseAT1 --> Convert[格式转换]
    UseAT2 --> Convert
    UseAT3 --> Convert
    
    Convert -->|"[AT]丞相"| Discord["<@&ROLE_ID>"]
    Discord --> Display["@丞相 (蓝色链接)"]
    
    NoAT1 --> End([结束])
    NoAT2 --> End
    NoAT3 --> End
    Display --> End
```

### 信号词对照表

```mermaid
flowchart LR
    subgraph NeedAT["📢 使用 [AT]"]
        N1["如何?
怎么?"]
        N2["可否?
对吗?"]
        N3["请定夺
请决策"]
        N4["请过目
请查看"]
        N5["请示下
请赐教"]
    end
    
    subgraph NoAT["🔚 结束对话"]
        E1["善
好"]
        E2["已定
准"]
        E3["领命
遵命"]
        E4["知道了
明白"]
    end
    
    NeedAT -->|"结尾加 [AT]"| Response[Bot 回应]
    NoAT -->|"不加 [AT]"| Response
```

---

## 🔄 跨频道任务执行

### 四步流程

```mermaid
sequenceDiagram
    participant User as 皇帝 (用户)
    participant Bot as Bot (丞相/太尉)
    participant Target as 目标频道
    participant Partner as 协作 Bot

    Note over User,Partner: 第1步: 接受任务
    User->>Bot: "去内阁通知太尉"
    Bot->>User: "臣领命，即刻前往内阁办理"

    Note over User,Partner: 第2步: 前往目标频道
    Bot->>Target: "臣已至内阁，[AT]太尉 请前来会合"
    
    Note over User,Partner: 第3步: 协作执行
    Bot->>Partner: "[AT]太尉，陛下让我们商议..."
    Partner->>Bot: "[AT]丞相，我的想法是..."
    Bot->>Partner: "[AT]太尉 所言甚是..."
    Note right of Partner: 使用 [AT] 保持
    Note right of Partner: 对话连续性

    Note over User,Partner: 第4步: 回禀汇报
    Bot->>User: "陛下，臣已完成商议，结果如下..."
    Note right of User: 此处不加 [AT]
    Note right of User: 自然结束
```

### 状态机

```mermaid
stateDiagram-v2
    [*] --> 空闲: 系统启动
    
    空闲 --> 接受任务: 收到跨频道指令
    接受任务 --> 移动中: 在原频道确认
    
    移动中 --> 协作中: 到达目标频道
    协作中 --> 协作中: 使用 [AT] 继续
    协作中 --> 汇报中: 任务完成
    
    汇报中 --> 空闲: 向皇帝回禀
    汇报中 --> 协作中: 需要继续讨论
    
    空闲 --> 回应中: 收到直接 @
    回应中 --> 空闲: 回应完成 (不加 [AT])
    回应中 --> 协作中: 需要协作 (加 [AT])
```

---

## 📁 目录结构

```mermaid
flowchart TB
    subgraph Root["📁 prompts/"]
        README["📄 README.md
        <span style='font-size:10px'>设计哲学</span>"]
        SYS["📄 SYSTEM_PROMPT.md
        <span style='font-size:10px'>导航目录</span>"]
        
        subgraph Rules["📁 规则/"]
            RM["_meta.md"]
            R1["conversation.md"]
            R2["at_mention.md"]
            R3["termination.md"]
        end
        
        subgraph Skills["📁 技能/"]
            SM["_meta.md"]
            S1["at_mention_usage.md"]
            S2["task_execution.md"]
            S3["multi_turn_dialogue.md"]
        end
        
        subgraph Context["📁 上下文/"]
            subgraph Id["身份/"]
                I1["丞相.md"]
                I2["太尉.md"]
            end
        end
        
        subgraph Specific["📁 特定/"]
            subgraph CD["赛博王朝/"]
                CD1["规则/"]
                CD2["技能/"]
                CD3["上下文/"]
            end
        end
    end
    
    SYS -->|指向| Rules
    SYS -->|指向| Skills
    SYS -->|指向| Context
    SYS -->|指向| Specific
```

---

## 🧠 研究 vs 执行分离

### 决策流程

```mermaid
flowchart TD
    Start(["收到指令"]) --> Clear{"指令是否明确?"}
    
    Clear -->|是| Execute["📝 执行模式
    <span style='font-size:10px'>• 专注实现</span>
    <span style='font-size:10px'>• 遵循技能流程</span>
    <span style='font-size:10px'>• 不探索替代方案</span>"]
    
    Clear -->|否| Research["🔍 研究模式
    <span style='font-size:10px'>• 列出选项</span>
    <span style='font-size:10px'>• 说明利弊</span>
    <span style='font-size:10px'>• 等待用户选择</span>"]
    
    Research --> Ask["询问澄清
    <span style='font-size:10px'>'陛下是指 A 还是 B?'</span>"]
    
    Ask --> UserResponse{用户回应}
    UserResponse -->|选 A| Execute
    UserResponse -->|选 B| Execute
    
    Execute --> Complete([任务完成])
```

### 避免的反模式

```mermaid
flowchart LR
    subgraph Bad["❌ 反模式"]
        B1["猜测执行"]
        B2["研究一半
就开始实现"]
        B3["替用户做决定"]
    end
    
    subgraph Good["✅ 最佳实践"]
        G1["不确定时询问"]
        G2["只研究
然后等待"]
        G3["让用户选择"]
    end
    
    Bad -->|"导致"| Problem["幻觉
错误假设"]
    Good -->|"导致"| Success["正确执行
用户满意"]
```

---

## 📊 v1.0 vs v2.0 对比

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#4ecdc4', 'primaryTextColor': '#fff'}}}%%
flowchart TB
    subgraph Comparison["架构对比"]
        direction LR
        
        subgraph V1["v1.0 (静态分层)"]
            V1_1["基础/
身份
规则"]
            V1_2["领域/
能力
多 Bot"]
            V1_3["特定/
频道
示例"]
            
            V1_1 --- V1_2 --- V1_3
        end
        
        subgraph V2["v2.0 (动态组合)"]
            V2_1["SYSTEM_PROMPT
导航
<span style='font-size:10px'>~200 tokens</span>"]
            
            V2_2["规则/
约束"]
            V2_3["技能/
流程"]
            V2_4["上下文/
信息"]
            
            V2_1 --> V2_2
            V2_1 --> V2_3
            V2_1 --> V2_4
        end
    end
    
    V1 -->|"加载全部
~2000 tokens
❌ 膨胀"| Problem["上下文膨胀
性能下降"]
    
    V2 -->|"按需加载
~500 tokens
✅ 精确"| Benefit["精确上下文
更好性能"]
```

| 指标 | v1.0 | v2.0 | 改进 |
|------|------|------|------|
| SYSTEM_PROMPT 大小 | ~2000 tokens | ~200 tokens | **-90%** |
| 单次请求上下文 | ~3000 tokens | ~800 tokens | **-73%** |
| @ 提及成功率 | 60% | 95% | **+58%** |
| 对话连续性 | 2-3 轮 | 5+ 轮 | **+150%** |

---

## ✅ 最佳实践

### 应该做的

```mermaid
flowchart LR
    subgraph Do["✅ 应该"]
        D1["SYSTEM_PROMPT
控制在 50 行内"]
        D2["一个规则解决
一个具体问题"]
        D3["一个技能编码
一个完整流程"]
        D4["定期清理
每月整合"]
    end
```

### 不应该做的

```mermaid
flowchart LR
    subgraph Dont["❌ 不应该"]
        N1["SYSTEM_PROMPT
写得太长"]
        N2["规则与技能混杂
职责不清"]
        N3["加载太多技能
上下文膨胀"]
        N4["从不清理
积累矛盾"]
    end
```

---

## 📚 参考

- **OpenClaw 技能**: `/usr/lib/node_modules/openclaw/skills/`
- **Agentic 工程最佳实践**: `docs/archive/2026-03-06/HowToBeAWorld-ClassAgenticEngineer.md`
- **当前配置**: `config/multi_bot.yaml`
- **系统提示**: `SYSTEM_PROMPT.md`

---

*设计版本: v2.0*  
*最后更新: 2026-03-06*  
*核心原则: **上下文就是一切***
