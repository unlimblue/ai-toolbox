"""Directed graph context management for multi-bot conversations.

Provides a graph-based approach to manage complex conversation contexts
including broadcasts, merges, and cross-channel tasks.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import copy


class EdgeType(Enum):
    """Types of relationships between messages."""
    DIRECT_MENTION = "direct_mention"      # Direct @ mention
    IMPLICIT_REPLY = "implicit_reply"      # Implicit reply (same channel, recent)
    TASK_RELATED = "task_related"          # Same task
    CROSS_CHANNEL = "cross_channel"        # Cross-channel link
    TEMPORAL = "temporal"                  # Temporal proximity


@dataclass
class MessageNode:
    """A node in the context graph representing a message."""
    
    # Basic properties
    id: str
    author_id: str
    author_name: str
    content: str
    channel_id: str
    timestamp: datetime
    
    # Graph structure
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    depth: int = 0
    
    # Visibility
    visible_to: Set[str] = field(default_factory=set)
    mention_targets: List[str] = field(default_factory=list)
    
    # Metadata
    message_type: str = "bot"  # user | bot | system
    task_id: Optional[str] = None
    
    # Cached visibility flag
    _visibility_calculated: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "content": self.content,
            "channel_id": self.channel_id,
            "timestamp": self.timestamp.isoformat(),
            "parents": self.parents,
            "children": self.children,
            "depth": self.depth,
            "visible_to": list(self.visible_to),
            "mention_targets": self.mention_targets,
            "message_type": self.message_type,
            "task_id": self.task_id
        }
    
    @classmethod
    def from_message(cls, message_id: str, author_id: str, author_name: str,
                     content: str, channel_id: str, timestamp: datetime,
                     mention_targets: Optional[List[str]] = None) -> "MessageNode":
        """Create a MessageNode from message data."""
        return cls(
            id=message_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            channel_id=channel_id,
            timestamp=timestamp,
            mention_targets=mention_targets or [],
            message_type="user" if not author_id.startswith("bot_") else "bot"
        )


@dataclass
class MessageEdge:
    """An edge representing relationship between two messages."""
    source: str
    target: str
    edge_type: EdgeType
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "strength": self.strength,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ContextGraph:
    """A directed graph representing conversation context."""
    
    graph_id: str
    graph_type: str  # channel | task | merged
    
    # Graph data
    nodes: Dict[str, MessageNode] = field(default_factory=dict)
    edges: List[MessageEdge] = field(default_factory=list)
    
    # Indexes
    adjacency_list: Dict[str, List[Tuple[str, EdgeType]]] = field(default_factory=dict)
    bot_nodes: Dict[str, List[str]] = field(default_factory=dict)
    time_index: List[Tuple[datetime, str]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    participating_bots: Set[str] = field(default_factory=set)
    
    def add_node(self, node: MessageNode) -> MessageNode:
        """Add a node to the graph and update indexes."""
        self.nodes[node.id] = node
        
        # Update time index
        self.time_index.append((node.timestamp, node.id))
        self.time_index.sort(key=lambda x: x[0])
        
        # Update bot index
        if node.author_id not in self.bot_nodes:
            self.bot_nodes[node.author_id] = []
        if node.id not in self.bot_nodes[node.author_id]:
            self.bot_nodes[node.author_id].append(node.id)
        
        # Update participating bots
        self.participating_bots.add(node.author_id)
        self.participating_bots.update(node.mention_targets)
        
        self.last_activity = datetime.now()
        return node
    
    def add_edge(self, edge: MessageEdge) -> MessageEdge:
        """Add an edge to the graph and update relationships."""
        self.edges.append(edge)
        
        # Update adjacency list
        if edge.source not in self.adjacency_list:
            self.adjacency_list[edge.source] = []
        self.adjacency_list[edge.source].append((edge.target, edge.edge_type))
        
        # Update node relationships
        if edge.source in self.nodes and edge.target in self.nodes:
            source_node = self.nodes[edge.source]
            target_node = self.nodes[edge.target]
            
            if edge.target not in source_node.children:
                source_node.children.append(edge.target)
            if edge.source not in target_node.parents:
                target_node.parents.append(edge.source)
                # Update depth
                target_node.depth = max(target_node.depth, source_node.depth + 1)
        
        self.last_activity = datetime.now()
        return edge
    
    def get_node(self, node_id: str) -> Optional[MessageNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_children(self, node_id: str) -> List[str]:
        """Get children of a node."""
        node = self.nodes.get(node_id)
        return node.children if node else []
    
    def get_parents(self, node_id: str) -> List[str]:
        """Get parents of a node."""
        node = self.nodes.get(node_id)
        return node.parents if node else []
    
    def get_recent_nodes(self, limit: int = 20) -> List[MessageNode]:
        """Get most recent nodes by time."""
        recent_ids = [nid for _, nid in self.time_index[-limit:]]
        return [self.nodes[nid] for nid in recent_ids if nid in self.nodes]
    
    def get_nodes_by_bot(self, bot_id: str) -> List[MessageNode]:
        """Get all nodes sent by a specific bot."""
        node_ids = self.bot_nodes.get(bot_id, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def to_dict(self) -> dict:
        """Convert graph to dictionary."""
        return {
            "graph_id": self.graph_id,
            "graph_type": self.graph_type,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "participating_bots": list(self.participating_bots)
        }


@dataclass
class SubGraph:
    """A subgraph representing a bot's view of the conversation."""
    
    nodes: Dict[str, MessageNode]
    edges: List[MessageEdge]
    entry_points: List[str]  # Nodes with no visible parents
    sorted_order: List[str]  # Topologically sorted
    bot_perspective: str     # Which bot this subgraph is for
    
    def get_linear_history(self) -> str:
        """Get linear history for simple prompts."""
        lines = []
        for node_id in self.sorted_order:
            node = self.nodes.get(node_id)
            if node:
                lines.append(f"{node.author_name}: {node.content}")
        return "\n".join(lines)
    
    def get_branching_history(self) -> str:
        """Get branching history showing tree structure."""
        lines = []
        for node_id in self.sorted_order:
            node = self.nodes.get(node_id)
            if node:
                indent = "  " * node.depth
                prefix = ""
                if len(node.parents) > 1:
                    prefix = "[Merge] "
                elif len(node.children) > 1:
                    prefix = "[Branch] "
                lines.append(f"{indent}{prefix}{node.author_name}: {node.content}")
        return "\n".join(lines)
    
    def get_stats(self) -> dict:
        """Get subgraph statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "entry_points": len(self.entry_points),
            "depth": max((node.depth for node in self.nodes.values()), default=0)
        }
