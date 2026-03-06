# Rules体系说明

## 什么是Rules

Rules是行为约束，定义：
- **禁止事项** —— 绝对不能做的事
- **强制事项** —— 必须做的事
- **信号词** —— 听到/看到特定词汇时的标准反应

## 如何使用Rules

1. SYSTEM_PROMPT会根据场景指引你读取对应的Rules
2. 读取后，将Rules内化到决策中
3. 不要机械复述Rules，而是自然遵循

## Rules列表

| 文件 | 用途 |
|------|------|
| `conversation.md` | 对话规则（避免循环、何时回应） |
| `cross_channel.md` | 跨频道任务规则 |
| `at_mention.md` | @提及规则（何时使用[AT]） |
| `termination.md` | 任务终止规则（完成标准） |
| `research_vs_execute.md` | 研究vs执行分离规则 |

## 原则

- Rules是**约束**，不是**流程**
- 违反Rules会导致问题
- 不确定时，优先遵循Rules
