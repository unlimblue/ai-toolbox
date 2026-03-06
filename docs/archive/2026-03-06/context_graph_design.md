# 对话上下文有向图管理设计

**文档状态**: 设计方案  
**创建日期**: 2026-03-05  
**目标**: 解决多 Bot 对话中的复杂上下文传播问题

---

## 1. 问题分析

### 1.1 当前机制的局限

**线性 @ 链条假设**：
```
A @ B → B @ C → C @ D
```

**实际场景的复杂性**：
```
        用户
          │
          ▼
        丞相 ─────┐
          │       │
          ▼       ▼
        太尉 ←── 兵部尚书
          │
          ▼
        丞相 (Merge点)
```

### 1.2 复杂场景示例

**场景1：分支（Broadcast）**
```
皇帝：@丞相 @太尉 @兵部尚书 商议边防

结果：
- 丞相收到完整消息
- 太尉收到完整消息
- 兵部尚书收到完整消息

后续：
丞相：@太尉 你觉得如何？
太尉：@丞相 可行
兵部尚书：@丞相 我有补充

此时丞相需要综合太尉和兵部尚书两者的意见
```

**场景2：合并（Merge）**
```
太尉：@丞相 方案A可行
兵部尚书：@丞相 方案B更安全

丞相需要同时看到两条消息，做出综合判断
```

**场景3：跨频道图合并**
```
金銮殿：皇帝@丞相@太尉 去内阁商议
              │
              ▼ (任务转移)
内阁：      丞相@太尉

需要合并两个频道的上下文图
```

---

## 2. 核心概念

### 2.1 数据模型

#### 节点（Node）= 消息

```python
@dataclass
class MessageNode:
    """消息节点 - 图的基本单元"""
    
    # 基础属性
    id: str                      # 全局唯一消息ID
    author_id: str               # 发送者ID
    author_name: str             # 发送者显示名
    content: str                 # 消息内容
    channel_id: str              # 所属频道
    timestamp: datetime          # 发送时间
    
    # 图结构属性
    parents: List[str]           # 父节点ID列表（被回复/被@的消息）
    children: List[str]          # 子节点ID列表（回复/引用此消息的消息）
    depth: int                   # 在图中的深度（距离根节点）
    
    # 可见性属性
    visible_to: Set[str]         # 哪些 Bot 能看到此消息
    mention_targets: List[str]   # 被 @ 的 Bot IDs
    
    # 元数据
    message_type: str            # "user" | "bot" | "system"
    task_id: Optional[str]       # 关联的任务ID（如果有）
```

#### 边（Edge）= 关系

```python
@dataclass
class MessageEdge:
    """消息之间的关系边"""
    
    source: str                  # 源消息ID
    target: str                  # 目标消息ID
    edge_type: EdgeType          # 边类型
    strength: float              # 关系强度 (0.0 - 1.0)
    
class EdgeType(Enum):
    DIRECT_MENTION = "direct_mention"      # 直接 @
    IMPLICIT_REPLY = "implicit_reply"      # 隐式回复（时间相近，同频道）
    TASK_RELATED = "task_related"          # 同一任务
    CROSS_CHANNEL = "cross_channel"        # 跨频道关联
    FORWARD = "forward"                    # 转发关系
```

#### 图（Graph）= 频道/任务上下文

```python
@dataclass
class ContextGraph:
    """上下文图 - 单个频道或任务的完整对话图"""
    
    graph_id: str                # 图ID（通常是 channel_id 或 task_id）
    graph_type: str              # "channel" | "task" | "merged"
    
    # 图数据
    nodes: Dict[str, MessageNode]              # 所有节点
    edges: List[MessageEdge]                    # 所有边
    adjacency_list: Dict[str, List[str]]        # 邻接表（加速遍历）
    
    # 索引
    bot_nodes: Dict[str, List[str]]             # bot_id -> 该 Bot 发送的节点
    time_index: SortedDict[datetime, str]       # 时间索引（用于范围查询）
    
    # 元数据
    created_at: datetime
    last_activity: datetime
    participating_bots: Set[str]                # 参与此图的所有 Bot
```

---

## 3. 核心算法

### 3.1 可见性传播算法

**问题**：确定一条消息对哪些 Bot 可见

**算法**：反向 BFS 传播

```python
def calculate_visibility(graph: ContextGraph, 
                         node: MessageNode) -> Set[str]:
    """
    计算消息的可见 Bot 集合
    
    基于原则：
    1. 被 @ 的 Bot 可见
    2. 父消息可见的 Bot，子消息也可见
    3. 同任务的 Bot 可见（可选）
    4. 发送者自己可见
    """
    visible = set()
    
    # 基础可见性
    visible.add(node.author_id)
    visible.update(node.mention_targets)
    
    # 反向传播：从父节点继承可见性
    for parent_id in node.parents:
        parent = graph.nodes.get(parent_id)
        if parent:
            parent_visible = calculate_visibility(graph, parent)
            visible.update(parent_visible)
    
    # 任务相关可见性
    if node.task_id:
        task_bots = get_task_participants(node.task_id)
        visible.update(task_bots)
    
    return visible
```

**复杂度**：O(V + E)，每个节点计算一次后缓存

### 3.2 子图提取算法

**问题**：为特定 Bot 提取它能看到的完整子图

**算法**：基于可见性的子图提取

```python
def extract_subgraph(graph: ContextGraph, 
                     bot_id: str,
                     max_depth: int = 10) -> SubGraph:
    """
    提取特定 Bot 的视角子图
    
    步骤：
    1. 找到所有对该 Bot 可见的节点
    2. 保留这些节点之间的边
    3. 保持拓扑结构
    """
    
    # 步骤1：收集可见节点
    visible_nodes = set()
    for node_id, node in graph.nodes.items():
        if bot_id in node.visible_to:
            visible_nodes.add(node_id)
    
    # 步骤2：收集相关边
    visible_edges = []
    for edge in graph.edges:
        if edge.source in visible_nodes and edge.target in visible_nodes:
            visible_edges.append(edge)
    
    # 步骤3：找到入口节点（没有父节点或父节点不可见）
    entry_points = []
    for node_id in visible_nodes:
        node = graph.nodes[node_id]
        has_visible_parent = any(
            parent_id in visible_nodes 
            for parent_id in node.parents
        )
        if not has_visible_parent:
            entry_points.append(node_id)
    
    # 步骤4：按时间拓扑排序
    sorted_nodes = topological_sort(visible_nodes, visible_edges)
    
    return SubGraph(
        nodes={nid: graph.nodes[nid] for nid in visible_nodes},
        edges=visible_edges,
        entry_points=entry_points,
        sorted_order=sorted_nodes
    )
```

### 3.3 图合并算法

**问题**：跨频道任务需要合并两个频道的图

**算法**：图合并与跨边添加

```python
def merge_graphs(source_graph: ContextGraph,
                 target_graph: ContextGraph,
                 task: CrossChannelTask) -> ContextGraph:
    """
    合并两个上下文图
    
    步骤：
    1. 复制所有节点和边
    2. 添加跨图边（任务指令 → 任务执行）
    3. 重新计算可见性
    """
    
    merged = ContextGraph(
        graph_id=f"merged_{source_graph.graph_id}_{target_graph.graph_id}",
        graph_type="merged"
    )
    
    # 步骤1：复制源图
    merged.nodes.update(source_graph.nodes)
    merged.edges.extend(source_graph.edges)
    
    # 步骤2：复制目标图
    merged.nodes.update(target_graph.nodes)
    merged.edges.extend(target_graph.edges)
    
    # 步骤3：添加跨图边
    # 找到任务指令消息（源图中）
    task_instruction_node = find_task_instruction(source_graph, task)
    
    # 找到任务第一条回复（目标图中）
    first_reply = find_first_reply(target_graph, task)
    
    if task_instruction_node and first_reply:
        cross_edge = MessageEdge(
            source=task_instruction_node.id,
            target=first_reply.id,
            edge_type=EdgeType.CROSS_CHANNEL,
            strength=1.0
        )
        merged.edges.append(cross_edge)
        
        # 更新节点关系
        task_instruction_node.children.append(first_reply.id)
        first_reply.parents.append(task_instruction_node.id)
    
    # 步骤4：重新计算所有节点的可见性
    for node in merged.nodes.values():
        node.visible_to = calculate_visibility(merged, node)
    
    return merged
```

---

## 4. 复杂场景处理

### 4.1 Broadcast 场景

```
用户：@丞相 @太尉 @兵部尚书 商议

图结构：
    用户
     │
     ├──► 丞相（可见）
     ├──► 太尉（可见）
     └──► 兵部尚书（可见）

处理：
- 三个 Bot 各自提取子图
- 丞相的子图：[用户消息]
- 太尉的子图：[用户消息]
- 兵部尚书的子图：[用户消息]
```

### 4.2 Merge 场景

```
太尉：@丞相 方案A可行
兵部尚书：@丞相 方案B安全

图结构：
    太尉 ──┐
           ▼
          丞相 ◄── 兵部尚书

处理：
- 丞相收到两条消息
- 丞相的子图包含两个父分支
- Prompt 中展示分支结构

格式化输出：
  太尉: 方案A可行
  兵部尚书: 方案B安全
  [Merge] 丞相需要综合判断
```

### 4.3 跨频道任务

```
阶段1 - 金銮殿：
  皇帝：@丞相 @太尉 去内阁商议

阶段2 - 内阁：
  丞相：@太尉 开始吧
  太尉：@丞相 好

合并后的图：
  皇帝
    │
    ▼
  丞相(金銮殿) ──┐
                 │ (跨频道边)
                 ▼
               丞相(内阁) ──► 太尉

处理：
- 合并两个图
- 丞相能看到完整的跨频道历史
- 太尉能看到从任务指令开始的完整历史
```

---

## 5. 接口设计

### 5.1 GraphManager 接口

```python
class ContextGraphManager:
    """图管理器 - 全局单例"""
    
    def __init__(self):
        self.graphs: Dict[str, ContextGraph] = {}          # graph_id -> Graph
        self.channel_graphs: Dict[str, str] = {}          # channel_id -> graph_id
        self.task_graphs: Dict[str, str] = {}             # task_id -> graph_id
        self.bot_active_graphs: Dict[str, Set[str]] = {}  # bot_id -> active graph_ids
    
    # 图生命周期管理
    def create_graph(self, graph_id: str, graph_type: str) -> ContextGraph:
        """创建新图"""
        pass
    
    def get_graph(self, graph_id: str) -> Optional[ContextGraph]:
        """获取图"""
        pass
    
    def merge_graphs(self, source_id: str, target_id: str, 
                     task_id: str) -> ContextGraph:
        """合并两个图为任务图"""
        pass
    
    def archive_graph(self, graph_id: str):
        """归档图（保存到持久存储）"""
        pass
    
    # 消息处理
    def add_message(self, message: UnifiedMessage, 
                    graph_id: Optional[str] = None) -> MessageNode:
        """添加消息到图"""
        pass
    
    def add_message_to_task(self, message: UnifiedMessage, 
                            task_id: str) -> MessageNode:
        """添加消息到任务图"""
        pass
    
    # 上下文查询
    def get_context_for_bot(self, bot_id: str, 
                            graph_id: str,
                            max_depth: int = 10) -> SubGraph:
        """获取 Bot 在特定图中的上下文"""
        pass
    
    def get_context_for_task(self, bot_id: str,
                             task_id: str) -> SubGraph:
        """获取 Bot 在任务中的上下文"""
        pass
    
    def get_recent_context(self, bot_id: str,
                          channel_id: str,
                          time_window: timedelta = timedelta(minutes=10)) -> SubGraph:
        """获取 Bot 在频道最近时间的上下文"""
        pass
```

### 5.2 Prompt 生成接口

```python
class PromptGenerator:
    """基于图结构生成 Prompt"""
    
    def generate(self, bot_id: str, 
                 current_message: MessageNode,
                 subgraph: SubGraph) -> str:
        """生成 Prompt"""
        pass
    
    def format_linear(self, subgraph: SubGraph) -> str:
        """线性格式化（简单对话）"""
        pass
    
    def format_branching(self, subgraph: SubGraph) -> str:
        """分支格式化（显示分支结构）"""
        pass
    
    def format_merge(self, subgraph: SubGraph, 
                     merge_node: MessageNode) -> str:
        """Merge 点格式化（突出显示多个来源）"""
        pass
```

---

## 6. 数据结构详细定义

### 6.1 完整类定义

```python
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from sortedcontainers import SortedDict
import uuid


class EdgeType(Enum):
    DIRECT_MENTION = "direct_mention"
    IMPLICIT_REPLY = "implicit_reply"
    TASK_RELATED = "task_related"
    CROSS_CHANNEL = "cross_channel"
    TEMPORAL = "temporal"  # 时间相近


@dataclass
class MessageNode:
    """消息节点"""
    id: str
    author_id: str
    author_name: str
    content: str
    channel_id: str
    timestamp: datetime
    
    # 图结构
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    depth: int = 0
    
    # 可见性
    visible_to: Set[str] = field(default_factory=set)
    mention_targets: List[str] = field(default_factory=list)
    
    # 元数据
    message_type: str = "bot"  # user | bot | system
    task_id: Optional[str] = None
    
    # 缓存
    _visibility_calculated: bool = False


@dataclass
class MessageEdge:
    """消息边"""
    source: str
    target: str
    edge_type: EdgeType
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContextGraph:
    """上下文图"""
    graph_id: str
    graph_type: str  # channel | task | merged
    
    nodes: Dict[str, MessageNode] = field(default_factory=dict)
    edges: List[MessageEdge] = field(default_factory=list)
    
    # 索引
    adjacency_list: Dict[str, List[Tuple[str, EdgeType]]] = field(
        default_factory=dict
    )
    bot_nodes: Dict[str, List[str]] = field(default_factory=dict)
    time_index: SortedDict = field(default_factory=lambda: SortedDict())
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    participating_bots: Set[str] = field(default_factory=set)
    
    def add_node(self, node: MessageNode):
        """添加节点并更新索引"""
        self.nodes[node.id] = node
        self.time_index[node.timestamp] = node.id
        
        # 更新 Bot 索引
        if node.author_id not in self.bot_nodes:
            self.bot_nodes[node.author_id] = []
        self.bot_nodes[node.author_id].append(node.id)
        
        # 更新参与 Bot
        self.participating_bots.add(node.author_id)
        self.participating_bots.update(node.mention_targets)
        
        self.last_activity = datetime.now()
    
    def add_edge(self, edge: MessageEdge):
        """添加边并更新邻接表"""
        self.edges.append(edge)
        
        # 更新邻接表
        if edge.source not in self.adjacency_list:
            self.adjacency_list[edge.source] = []
        self.adjacency_list[edge.source].append(
            (edge.target, edge.edge_type)
        )
        
        # 更新节点关系
        if edge.source in self.nodes and edge.target in self.nodes:
            source_node = self.nodes[edge.source]
            target_node = self.nodes[edge.target]
            
            if edge.target not in source_node.children:
                source_node.children.append(edge.target)
            if edge.source not in target_node.parents:
                target_node.parents.append(edge.source)


@dataclass
class SubGraph:
    """子图 - 特定 Bot 的视角"""
    nodes: Dict[str, MessageNode]
    edges: List[MessageEdge]
    entry_points: List[str]
    sorted_order: List[str]
    bot_perspective: str
```

---

## 7. 实现步骤

### 阶段1：基础实现

1. **创建基础数据结构**
   - `MessageNode`, `MessageEdge`, `ContextGraph`
   - 基础 CRUD 操作

2. **实现可见性计算**
   - 反向 BFS 算法
   - 缓存机制

3. **集成到现有系统**
   - Hub 监听器添加消息到图
   - RoleBot 从图获取上下文

### 阶段2：复杂场景

1. **实现子图提取**
   - 基于可见性的过滤
   - 拓扑排序

2. **实现图合并**
   - 跨频道任务合并
   - 跨边添加

3. **优化性能**
   - 增量更新
   - 缓存策略

### 阶段3：高级功能

1. **Prompt 生成优化**
   - 分支格式化
   - Merge 点突出

2. **持久化**
   - 图数据库存储
   - 历史查询

3. **可视化**（可选）
   - 图结构可视化
   - 调试工具

---

## 8. 性能考虑

| 操作 | 时间复杂度 | 优化策略 |
|------|-----------|----------|
| 添加消息 | O(1) | 直接插入字典 |
| 计算可见性 | O(V+E) | 缓存，增量更新 |
| 提取子图 | O(V+E) | 预计算索引 |
| 合并图 | O(V1+V2+E1+E2) | 延迟合并 |
| 拓扑排序 | O(V+E) | 缓存排序结果 |

**内存优化**：
- 活跃图常驻内存
- 历史图分页加载
- 消息内容压缩存储

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 图过大 | 内存占用高 | 限制图大小，自动归档 |
| 计算复杂 | 响应延迟 | 异步计算，缓存结果 |
| 并发修改 | 数据不一致 | 锁机制，乐观并发 |
| 循环依赖 | 无限递归 | 访问标记，深度限制 |

---

## 10. 决策点

**是否实施此方案需要考虑**：

1. **当前痛点是否严重？**
   - 是否观察到 Bot 上下文断裂的实际问题？
   - 是否影响对话质量？

2. **复杂度是否值得？**
   - 当前项目阶段是否适合引入复杂图结构？
   - 简单的时间线方案是否足够？

3. **资源是否充足？**
   - 开发时间
   - 测试覆盖
   - 维护成本

**建议**：
- 如果当前 @ 链条已满足 80% 场景，先不实施
- 如果观察到严重的上下文断裂问题，分阶段实施
- 先实施简化版（时间线 + 任务标记），再考虑完整图结构

---

*文档版本: 1.0*  
*作者: AI-Toolbox Team*  
*状态: 设计评审中*
