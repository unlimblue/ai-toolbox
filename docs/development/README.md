# Development Documents

Current development documentation.

---

## Active Documents

| Document | Description |
|----------|-------------|
| [fix_conversation_and_channel.md](fix_conversation_and_channel.md) | Fix for conversation continuity and channel name recognition |
| [context_graph_design.md](context_graph_design.md) | **NEW** - Directed graph context management design for complex multi-bot conversations |

## Archive

Historical development plans are in [../archive/](../archive/).

---

## Context Graph Design

The `context_graph_design.md` document provides a comprehensive design for managing complex conversation contexts using a directed graph structure. This addresses scenarios such as:

- **Broadcast**: One message mentioning multiple bots
- **Merge**: Multiple bots responding to the same bot
- **Cross-channel tasks**: Conversations spanning multiple Discord channels

### Key Concepts

- **Nodes**: Messages with visibility and relationship metadata
- **Edges**: @ mentions, replies, and cross-channel links
- **Graphs**: Per-channel or per-task conversation contexts
- **Subgraphs**: Bot-specific views of the conversation

### Implementation Status

**Status**: Design Phase  
**Priority**: Medium  
**Estimated Effort**: 2-3 weeks

See the full design document for detailed data structures, algorithms, and implementation steps.
