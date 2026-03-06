"""Graph manager for context graphs.

Manages the lifecycle and operations of context graphs across channels and tasks.
"""

from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from .context_graph import (
    ContextGraph, MessageNode, MessageEdge, 
    SubGraph, EdgeType
)


class ContextGraphManager:
    """
    Manages all context graphs in the system.
    
    This is a singleton class that maintains:
    - Channel graphs (one per Discord channel)
    - Task graphs (one per cross-channel task)
    - Merged graphs (combined for complex tasks)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Graph storage
        self.graphs: Dict[str, ContextGraph] = {}
        
        # Mappings
        self.channel_to_graph: Dict[str, str] = {}  # channel_id -> graph_id
        self.task_to_graph: Dict[str, str] = {}     # task_id -> graph_id
        self.bot_active_graphs: Dict[str, Set[str]] = {}  # bot_id -> set of graph_ids
        
        # Settings
        self.max_graph_age = timedelta(hours=24)
        self.max_nodes_per_graph = 1000
        
        self._initialized = True
    
    def create_channel_graph(self, channel_id: str) -> ContextGraph:
        """Create a new graph for a channel."""
        graph_id = f"channel_{channel_id}"
        
        if graph_id in self.graphs:
            return self.graphs[graph_id]
        
        graph = ContextGraph(
            graph_id=graph_id,
            graph_type="channel"
        )
        
        self.graphs[graph_id] = graph
        self.channel_to_graph[channel_id] = graph_id
        
        return graph
    
    def create_task_graph(self, task_id: str, source_channel: str, 
                          target_channel: str, participants: List[str]) -> ContextGraph:
        """Create a new graph for a cross-channel task."""
        graph_id = f"task_{task_id}"
        
        # Create merged graph from source and target channels
        source_graph = self.get_or_create_channel_graph(source_channel)
        target_graph = self.get_or_create_channel_graph(target_channel)
        
        merged = self._merge_graphs(source_graph, target_graph, task_id)
        merged.graph_id = graph_id
        merged.graph_type = "task"
        
        self.graphs[graph_id] = merged
        self.task_to_graph[task_id] = graph_id
        
        # Register participants
        for bot_id in participants:
            if bot_id not in self.bot_active_graphs:
                self.bot_active_graphs[bot_id] = set()
            self.bot_active_graphs[bot_id].add(graph_id)
        
        return merged
    
    def get_or_create_channel_graph(self, channel_id: str) -> ContextGraph:
        """Get existing channel graph or create new one."""
        graph_id = self.channel_to_graph.get(channel_id)
        if graph_id and graph_id in self.graphs:
            return self.graphs[graph_id]
        return self.create_channel_graph(channel_id)
    
    def get_or_create_graph(self, graph_id: str, graph_type: str = "channel",
                           channel_id: str = None) -> ContextGraph:
        """Get existing graph or create new one.
        
        Args:
            graph_id: The graph ID
            graph_type: Type of graph ("channel" or "task")
            channel_id: Channel ID (required for channel graphs)
        """
        if graph_id in self.graphs:
            return self.graphs[graph_id]
        
        # Create new graph
        if graph_type == "channel" and channel_id:
            return self.create_channel_graph(channel_id)
        else:
            # Generic graph creation
            graph = ContextGraph(
                graph_id=graph_id,
                graph_type=graph_type
            )
            self.graphs[graph_id] = graph
            return graph
    
    def get_graph(self, graph_id: str) -> Optional[ContextGraph]:
        """Get a graph by ID."""
        return self.graphs.get(graph_id)
    
    def get_graph_by_task(self, task_id: str) -> Optional[ContextGraph]:
        """Get graph for a task."""
        graph_id = self.task_to_graph.get(task_id)
        if graph_id:
            return self.graphs.get(graph_id)
        return None
    
    def get_graph_by_channel(self, channel_id: str) -> Optional[ContextGraph]:
        """Get graph for a channel."""
        graph_id = self.channel_to_graph.get(channel_id)
        if graph_id:
            return self.graphs.get(graph_id)
        return None
    
    def add_message_to_graph(self, graph_id: str, message_id: str,
                            author_id: str, author_name: str,
                            content: str, channel_id: str,
                            timestamp: datetime,
                            mention_targets: List[str],
                            parent_node_ids: Optional[List[str]] = None) -> MessageNode:
        """Add a message to a graph."""
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        # Create node
        node = MessageNode.from_message(
            message_id=message_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            channel_id=channel_id,
            timestamp=timestamp,
            mention_targets=mention_targets
        )
        
        # Set parents if provided
        if parent_node_ids:
            node.parents = parent_node_ids
            for parent_id in parent_node_ids:
                if parent_id in graph.nodes:
                    parent = graph.nodes[parent_id]
                    node.depth = max(node.depth, parent.depth + 1)
        
        # Add to graph
        graph.add_node(node)
        
        # Create edges to parents
        if parent_node_ids:
            for parent_id in parent_node_ids:
                if parent_id in graph.nodes:
                    edge = MessageEdge(
                        source=parent_id,
                        target=node.id,
                        edge_type=EdgeType.IMPLICIT_REPLY
                    )
                    graph.add_edge(edge)
        
        # Calculate visibility
        self._calculate_visibility(graph, node)
        
        # Cleanup if needed
        self._cleanup_graph_if_needed(graph)
        
        return node
    
    def create_reply_node(self, original_message_id: str, 
                         graph_id: str,
                         sender_bot_id: str,
                         sender_name: str,
                         content: str,
                         mentions: List[str],
                         channel_id: str) -> MessageNode:
        """Create a reply node that inherits the chain."""
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        # Find parent node
        parent_node = graph.get_node(original_message_id)
        
        # Create new node
        node = MessageNode(
            id=str(uuid.uuid4()),
            author_id=sender_bot_id,
            author_name=sender_name,
            content=content,
            channel_id=channel_id,
            timestamp=datetime.now(),
            parents=[original_message_id] if parent_node else [],
            mention_targets=mentions,
            message_type="bot"
        )
        
        if parent_node:
            node.depth = parent_node.depth + 1
            node.task_id = parent_node.task_id
        
        # Add to graph
        graph.add_node(node)
        
        # Add edge
        if parent_node:
            edge = MessageEdge(
                source=original_message_id,
                target=node.id,
                edge_type=EdgeType.DIRECT_MENTION
            )
            graph.add_edge(edge)
        
        # Calculate visibility
        self._calculate_visibility(graph, node)
        
        # Update bot active graphs
        if sender_bot_id not in self.bot_active_graphs:
            self.bot_active_graphs[sender_bot_id] = set()
        self.bot_active_graphs[sender_bot_id].add(graph_id)
        
        return node
    
    def extract_subgraph(self, graph_id: str, bot_id: str,
                        max_depth: int = 10) -> Optional[SubGraph]:
        """Extract a subgraph visible to a specific bot."""
        graph = self.graphs.get(graph_id)
        if not graph:
            return None
        
        # Find all visible nodes
        visible_nodes: Dict[str, MessageNode] = {}
        
        for node_id, node in graph.nodes.items():
            # Check if visible to this bot
            if self._is_visible_to_bot(node, bot_id):
                visible_nodes[node_id] = node
        
        if not visible_nodes:
            return None
        
        # Find relevant edges
        visible_edges = []
        for edge in graph.edges:
            if edge.source in visible_nodes and edge.target in visible_nodes:
                visible_edges.append(edge)
        
        # Find entry points (nodes with no visible parents)
        entry_points = []
        for node_id, node in visible_nodes.items():
            has_visible_parent = any(
                parent_id in visible_nodes 
                for parent_id in node.parents
            )
            if not has_visible_parent:
                entry_points.append(node_id)
        
        # Topological sort
        sorted_order = self._topological_sort(visible_nodes, visible_edges)
        
        return SubGraph(
            nodes=visible_nodes,
            edges=visible_edges,
            entry_points=entry_points,
            sorted_order=sorted_order,
            bot_perspective=bot_id
        )
    
    def get_context_for_bot(self, bot_id: str, channel_id: str,
                           task_id: Optional[str] = None,
                           max_depth: int = 10) -> Optional[SubGraph]:
        """Get context subgraph for a bot."""
        # Prefer task graph if available
        if task_id:
            graph = self.get_graph_by_task(task_id)
            if graph:
                return self.extract_subgraph(graph.graph_id, bot_id, max_depth)
        
        # Fall back to channel graph
        graph = self.get_graph_by_channel(channel_id)
        if graph:
            return self.extract_subgraph(graph.graph_id, bot_id, max_depth)
        
        return None
    
    def end_task(self, task_id: str):
        """End a task and clean up."""
        graph_id = self.task_to_graph.get(task_id)
        if graph_id:
            # Remove from active graphs
            for bot_id, graph_ids in self.bot_active_graphs.items():
                graph_ids.discard(graph_id)
            
            # Optionally archive before removing
            # self._archive_graph(graph_id)
            
            # Remove task mapping
            del self.task_to_graph[task_id]
    
    def _calculate_visibility(self, graph: ContextGraph, node: MessageNode):
        """Calculate which bots can see this message."""
        visible = set()
        
        # Author always visible
        visible.add(node.author_id)
        
        # Mentioned bots
        visible.update(node.mention_targets)
        
        # Inherit from parents (visibility propagates down)
        for parent_id in node.parents:
            if parent_id in graph.nodes:
                parent = graph.nodes[parent_id]
                visible.update(parent.visible_to)
        
        # If this is a task-related message, all participants can see
        if node.task_id:
            task_graph = self.get_graph_by_task(node.task_id)
            if task_graph:
                visible.update(task_graph.participating_bots)
        
        node.visible_to = visible
        node._visibility_calculated = True
    
    def _is_visible_to_bot(self, node: MessageNode, bot_id: str) -> bool:
        """Check if a message is visible to a bot."""
        if not node._visibility_calculated:
            return False
        return bot_id in node.visible_to
    
    def _topological_sort(self, nodes: Dict[str, MessageNode],
                         edges: List[MessageEdge]) -> List[str]:
        """Topological sort of nodes."""
        # Build adjacency list
        adj = {nid: [] for nid in nodes}
        in_degree = {nid: 0 for nid in nodes}
        
        for edge in edges:
            if edge.source in nodes and edge.target in nodes:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Kahn's algorithm
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            # Sort by timestamp for consistent ordering
            queue.sort(key=lambda x: nodes[x].timestamp)
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in adj[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _merge_graphs(self, source: ContextGraph, target: ContextGraph,
                     task_id: str) -> ContextGraph:
        """Merge two graphs for a cross-channel task."""
        merged = ContextGraph(
            graph_id=f"merged_{task_id}",
            graph_type="merged"
        )
        
        # Copy all nodes from source
        for node_id, node in source.nodes.items():
            merged.nodes[node_id] = self._copy_node(node)
        
        # Copy all nodes from target
        for node_id, node in target.nodes.items():
            if node_id not in merged.nodes:
                merged.nodes[node_id] = self._copy_node(node)
        
        # Copy edges
        for edge in source.edges:
            if edge.source in merged.nodes and edge.target in merged.nodes:
                merged.edges.append(edge)
        
        for edge in target.edges:
            if edge.source in merged.nodes and edge.target in merged.nodes:
                merged.edges.append(edge)
        
        # Update indexes
        for node in merged.nodes.values():
            merged.time_index.append((node.timestamp, node.id))
            if node.author_id not in merged.bot_nodes:
                merged.bot_nodes[node.author_id] = []
            merged.bot_nodes[node.author_id].append(node.id)
            merged.participating_bots.add(node.author_id)
        
        merged.time_index.sort(key=lambda x: x[0])
        
        return merged
    
    def _copy_node(self, node: MessageNode) -> MessageNode:
        """Deep copy a node."""
        return MessageNode(
            id=node.id,
            author_id=node.author_id,
            author_name=node.author_name,
            content=node.content,
            channel_id=node.channel_id,
            timestamp=node.timestamp,
            parents=node.parents.copy(),
            children=node.children.copy(),
            depth=node.depth,
            visible_to=node.visible_to.copy(),
            mention_targets=node.mention_targets.copy(),
            message_type=node.message_type,
            task_id=node.task_id
        )
    
    def _cleanup_graph_if_needed(self, graph: ContextGraph):
        """Cleanup old nodes if graph exceeds size limit."""
        if len(graph.nodes) > self.max_nodes_per_graph:
            # Remove oldest 20% of nodes
            to_remove = len(graph.nodes) // 5
            oldest_ids = [nid for _, nid in graph.time_index[:to_remove]]
            
            for node_id in oldest_ids:
                if node_id in graph.nodes:
                    del graph.nodes[node_id]
            
            # Rebuild indexes
            graph.time_index = [
                (ts, nid) for ts, nid in graph.time_index 
                if nid in graph.nodes
            ]
    
    def get_stats(self) -> dict:
        """Get manager statistics."""
        return {
            "total_graphs": len(self.graphs),
            "channel_graphs": len(self.channel_to_graph),
            "task_graphs": len(self.task_to_graph),
            "active_bots": len(self.bot_active_graphs),
            "total_nodes": sum(len(g.nodes) for g in self.graphs.values())
        }
