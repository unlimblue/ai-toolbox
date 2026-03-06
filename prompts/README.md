# 🎭 Prompt System Design Philosophy v2.0

> **Context is Everything** —— Only provide the Bot with precise information needed to complete the task

![Version](https://img.shields.io/badge/version-2.0-blue)
![Architecture](https://img.shields.io/badge/architecture-Navigation%20+%20Rules%20+%20Skills-green)

---

## 🎯 Core Philosophy

### The Problem with v1.0

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ff6b6b', 'primaryTextColor': '#fff'}}}%%
flowchart TB
    subgraph V1["❌ v1.0: Monolithic Loading"]
        A1[SYSTEM_PROMPT
        <span style='font-size:11px'>~2000 tokens</span>]
        A1 --> B1[Identity 200t]
        A1 --> C1[Capabilities 500t]
        A1 --> D1[Rules 800t]
        A1 --> E1[Examples 300t]
        A1 --> F1[...]
    end

    subgraph V2["✅ v2.0: Navigation + On-Demand"]
        A2[SYSTEM_PROMPT
        <span style='font-size:11px'>~200 tokens</span>]
        A2 --> B2[Scene Detection]
        B2 --> C2[Load Rules]
        B2 --> D2[Load Skills]
        B2 --> E2[Load Context]
    end

    V1 -->|"Context Bloat
    Bot Confused"| V2
```

### Key Upgrades: v1.0 → v2.0

| Aspect | v1.0 (Layered) | v2.0 (Navigation + Rules + Skills) |
|--------|----------------|-----------------------------------|
| **Loading** | Load everything (~2000 tokens) | On-demand loading (~500 tokens) |
| **SYSTEM_PROMPT** | Large content dump | **Navigation directory** |
| **Rendering** | Static template | Dynamic Rules + Skills composition |
| **Research/Execute** | Mixed together | **Research vs Execute separation** |

---

## 🏗️ Architecture: Navigation + Rules + Skills

### High-Level Flow

```mermaid
flowchart TB
    subgraph Input["📥 Input"]
        User[User Message]
    end

    subgraph System["⚙️ SYSTEM_PROMPT.md (Navigation)"]
        Nav[Scene Detection
        <span style='font-size:10px'>IF cross_channel → load X</span>
        <span style='font-size:10px'>IF conversation → load Y</span>]
    end

    subgraph Components["📚 Components (On-Demand)"]
        direction TB
        Rules["🚫 Rules/
        <span style='font-size:10px'>What NOT to do</span>
        <span style='font-size:10px'>What MUST do</span>"]
        Skills["📝 Skills/
        <span style='font-size:10px'>How to do X</span>
        <span style='font-size:10px'>Step-by-step</span>"]
        Context["📄 Context/
        <span style='font-size:10px'>Identity, Examples</span>"]
    end

    subgraph Output["📤 Output"]
        Response[Bot Response]
    end

    User --> Nav
    Nav --> Rules
    Nav --> Skills
    Nav --> Context
    Rules --> Response
    Skills --> Response
    Context --> Response
```

### Component Responsibilities

```mermaid
flowchart LR
    subgraph System["SYSTEM_PROMPT.md"]
        S1["Navigation Only
        <span style='font-size:10px'>• Scene detection</span>
        <span style='font-size:10px'>• IF-ELSE routing</span>
        <span style='font-size:10px'>• Component pointers</span>"]
    end

    subgraph Rules["🚫 Rules/"]
        R1["Constraints
        <span style='font-size:10px'>• DON'T do X</span>
        <span style='font-size:10px'>• MUST do Y</span>
        <span style='font-size:10px'>• Signal words</span>"]
    end

    subgraph Skills["📝 Skills/"]
        SK1["Procedures
        <span style='font-size:10px'>• How to do X</span>
        <span style='font-size:10px'>• Step-by-step</span>
        <span style='font-size:10px'>• Checklists</span>"]
    end

    subgraph Context["📄 Context/"]
        C1["Information
        <span style='font-size:10px'>• Identity details</span>
        <span style='font-size:10px'>• Capabilities</span>
        <span style='font-size:10px'>• Examples</span>"]
    end

    System -->|"Points to"| Rules
    System -->|"Points to"| Skills
    System -->|"Points to"| Context
```

---

## 🎮 [AT] Mention Decision Flow

### When to Use [AT]

```mermaid
flowchart TD
    Start(["Need Response?"])
    
    Start --> Check{"Check Message Type"}
    
    Check -->|Question| UseAT1["End with [AT]
    <span style='font-size:10px'>'...how?' [AT]丞相</span>"]
    
    Check -->|Request Confirm| UseAT2["End with [AT]
    <span style='font-size:10px'>'Please decide.' [AT]丞相</span>"]
    
    Check -->|Continue Dialogue| UseAT3["End with [AT]
    <span style='font-size:10px'>'Any thoughts?' [AT]太尉</span>"]
    
    Check -->|Conclusion Reached| NoAT1["NO [AT]
    <span style='font-size:10px'>'Agreed.'</span>"]
    
    Check -->|Simple Info| NoAT2["NO [AT]
    <span style='font-size:10px'>'I have notified.'</span>"]
    
    Check -->|Wait for Other| NoAT3["NO [AT]
    <span style='font-size:10px'>Natural end</span>"]

    UseAT1 --> Convert[Format Conversion]
    UseAT2 --> Convert
    UseAT3 --> Convert
    
    Convert -->|"[AT]丞相"| Discord["<@&ROLE_ID>"]
    Discord --> Display["@丞相 (Blue Link)"]
    
    NoAT1 --> End([End])
    NoAT2 --> End
    NoAT3 --> End
    Display --> End
```

### Signal Word Mapping

```mermaid
flowchart LR
    subgraph NeedAT["📢 Use [AT]"]
        N1["如何?
        How?"]
        N2["可否?
        Can?"]
        N3["请定夺
        Please decide"]
        N4["请过目
        Please review"]
        N5["请示下
        Please advise"]
    end
    
    subgraph NoAT["🔚 End Dialogue"]
        E1["善
        Good"]
        E2["已定
        Decided"]
        E3["领命
        Will do"]
        E4["知道了
        Understood"]
    end
    
    NeedAT -->|"[AT] at end"| Response[Bot Response]
    NoAT -->|"NO [AT]"| Response
```

---

## 🔄 Cross-Channel Task Execution

### 4-Step Process

```mermaid
sequenceDiagram
    participant User as Emperor (User)
    participant Bot as Bot (丞相/太尉)
    participant Target as Target Channel
    participant Partner as Partner Bot

    Note over User,Partner: Step 1: Accept Task
    User->>Bot: "Go to 内阁 and notify 太尉"
    Bot->>User: "臣领命，即刻前往内阁办理"

    Note over User,Partner: Step 2: Go to Target
    Bot->>Target: "臣已至内阁，[AT]太尉 请前来会合"
    
    Note over User,Partner: Step 3: Collaborate
    Bot->>Partner: "[AT]太尉，陛下让我们商议..."
    Partner->>Bot: "[AT]丞相，我的想法是..."
    Bot->>Partner: "[AT]太尉 所言甚是..."
    Note right of Partner: Use [AT] to<br/>maintain dialogue

    Note over User,Partner: Step 4: Report Back
    Bot->>User: "陛下，臣已完成商议，结果如下..."
    Note right of User: NO [AT] here<br/>Natural ending
```

### State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle: System Start
    
    Idle --> Accepting: Receive Cross-Channel Task
    Accepting --> Moving: Acknowledge in Original Channel
    
    Moving --> Collaborating: Arrive at Target Channel
    Collaborating --> Collaborating: Use [AT] to Continue
    Collaborating --> Reporting: Task Complete
    
    Reporting --> Idle: Report to Emperor
    Reporting --> Collaborating: Need More Discussion
    
    Idle --> Responding: Receive Direct @
    Responding --> Idle: Response Sent (NO [AT])
    Responding --> Collaborating: Need Partner Input ([AT])
```

---

## 📁 Directory Structure

```mermaid
flowchart TB
    subgraph Root["📁 prompts/"]
        README["📄 README.md
        <span style='font-size:10px'>Design Philosophy</span>"]
        SYS["📄 SYSTEM_PROMPT.md
        <span style='font-size:10px'>Navigation Directory</span>"]
        
        subgraph Rules["📁 rules/"]
            RM["_meta.md"]
            R1["conversation.md"]
            R2["at_mention.md"]
            R3["termination.md"]
        end
        
        subgraph Skills["📁 skills/"]
            SM["_meta.md"]
            S1["at_mention_usage.md"]
            S2["task_execution.md"]
            S3["multi_turn_dialogue.md"]
        end
        
        subgraph Context["📁 context/"]
            subgraph Id["identity/"]
                I1["chengxiang.md"]
                I2["taiwei.md"]
            end
        end
        
        subgraph Specific["📁 specific/"]
            subgraph CD["cyber_dynasty/"]
                CD1["rules/"]
                CD2["skills/"]
                CD3["context/"]
            end
        end
    end
    
    SYS -->|Points to| Rules
    SYS -->|Points to| Skills
    SYS -->|Points to| Context
    SYS -->|Points to| Specific
```

---

## 🧠 Research vs Execute Separation

### Decision Flow

```mermaid
flowchart TD
    Start(["Receive Command"]) --> Clear{"Clear Enough?"}
    
    Clear -->|Yes| Execute["📝 EXECUTE MODE
    <span style='font-size:10px'>• Focus on implementation</span>
    <span style='font-size:10px'>• Follow Skill procedures</span>
    <span style='font-size:10px'>• Do not explore alternatives</span>"]
    
    Clear -->|No| Research["🔍 RESEARCH MODE
    <span style='font-size:10px'>• List options</span>
    <span style='font-size:10px'>• Explain trade-offs</span>
    <span style='font-size:10px'>• WAIT for user choice</span>"]
    
    Research --> Ask["Ask for Clarification
    <span style='font-size:10px'>'陛下是指A还是B？'"]
    
    Ask --> UserResponse{User Response}
    UserResponse -->|A| Execute
    UserResponse -->|B| Execute
    
    Execute --> Complete([Task Complete])
```

### Anti-Patterns to Avoid

```mermaid
flowchart LR
    subgraph Bad["❌ Anti-Patterns"]
        B1["Guess and Execute"]
        B2["Research Halfway
        Then Implement"]
        B3["Choose for User"]
    end
    
    subgraph Good["✅ Best Practices"]
        G1["Ask When Uncertain"]
        G2["Research Only
        Then Wait"]
        G3["Let User Decide"]
    end
    
    Bad -->|"Leads to"| Problem["Hallucination
Wrong Assumptions"]
    Good -->|"Leads to"| Success["Correct Execution
User Satisfaction"]
```

---

## 📊 v1.0 vs v2.0 Comparison

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#4ecdc4', 'primaryTextColor': '#fff'}}}%%
flowchart TB
    subgraph Comparison["Architecture Comparison"]
        direction LR
        
        subgraph V1["v1.0 (Static Layered)"]
            V1_1["Base/
Identity
Rules"]
            V1_2["Domain/
Capabilities
Multi-Bot"]
            V1_3["Specific/
Channels
Examples"]
            
            V1_1 --- V1_2 --- V1_3
        end
        
        subgraph V2["v2.0 (Dynamic Composition)"]
            V2_1["SYSTEM_PROMPT
Navigation
<span style='font-size:10px'>~200 tokens</span>"]
            
            V2_2["rules/
Constraints"]
            V2_3["skills/
Procedures"]
            V2_4["context/
Information"]
            
            V2_1 --> V2_2
            V2_1 --> V2_3
            V2_1 --> V2_4
        end
    end
    
    V1 -->|"Load Everything
~2000 tokens
❌ Bloat"| Problem["Context Bloat
Poor Performance"]
    
    V2 -->|"Load On-Demand
~500 tokens
✅ Precise"| Benefit["Precise Context
Better Performance"]
```

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| SYSTEM_PROMPT Size | ~2000 tokens | ~200 tokens | **-90%** |
| Per-Request Context | ~3000 tokens | ~800 tokens | **-73%** |
| @ Mention Success | 60% | 95% | **+58%** |
| Dialogue Continuity | 2-3 rounds | 5+ rounds | **+150%** |

---

## ✅ Best Practices

### DO's

```mermaid
flowchart LR
    subgraph Do["✅ DO"]
        D1["Keep SYSTEM_PROMPT
< 50 lines"]
        D2["One Rule per
Specific Problem"]
        D3["One Skill per
Complete Workflow"]
        D4["Regular Cleanup
Monthly Integration"]
    end
```

### DON'Ts

```mermaid
flowchart LR
    subgraph Dont["❌ DON'T"]
        N1["Make SYSTEM_PROMPT
Too Long"]
        N2["Mix Rules & Skills
Unclear Responsibility"]
        N3["Load Too Many Skills
Context Bloat"]
        N4["Never Cleanup
Accumulate Contradictions"]
    end
```

---

## 📚 References

- **OpenClaw Skills**: `/usr/lib/node_modules/openclaw/skills/`
- **Agentic Engineering Best Practices**: `docs/archive/2026-03-06/HowToBeAWorld-ClassAgenticEngineer.md`
- **Current Config**: `config/multi_bot.yaml`
- **System Prompt**: `SYSTEM_PROMPT.md`

---

*Design Version: v2.0*  
*Last Updated: 2026-03-06*  
*Core Principle: **Context is Everything***
