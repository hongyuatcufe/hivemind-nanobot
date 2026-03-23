# HiveMind-nanobot

> Lightweight Multi-Agent Evolution System - Three-Layer Mother Node Architecture built on [nanobot](https://github.com/HKUDS/nanobot)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: Prototype](https://img.shields.io/badge/Status-Prototype-yellow.svg)]()

**Language**: [English](README.md) | [简体中文](README-zh.md)

---

## 📖 Introduction

HiveMind-nanobot is a lightweight multi-agent evolution system **built on top of [nanobot](https://github.com/HKUDS/nanobot)** (~4,000 lines). While preserving nanobot's lightweight nature, 40+ channel integrations, and ClawHub Skill ecosystem, we introduce a **three-layer mother node architecture** to enable agent self-evolution and knowledge accumulation.

**Design Philosophy**: Not to replace nanobot, but to add evolutionary capabilities on top of it — transforming nanobot from a "single-agent framework" into a "system that designs and manages multi-agent swarms autonomously."

### Core Features

- 🧠 **Three-Layer Mother Nodes**: Wizard (individual evolution), Mother (swarm evolution), Librarian (knowledge evolution)
- 🔄 **Message Bus**: Asynchronous inter-node communication with decoupled design
- 💾 **Shared Memory**: SQLite-based persistence for experience accumulation and knowledge stratification
- 🐝 **Swarm Management**: Dynamic creation and orchestration of sub-agents
- 🌱 **Evolution Mechanism**: Learn from failures and continuously optimize strategies

---

## 🏗️ Architecture

### Three-Layer Mother Nodes

```
┌─────────────────────────────────────────────────────────┐
│              Three-Layer Mother Node                     │
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │  Wizard  │◄──►│  Mother  │◄──►│ Librarian│        │
│   │   Node   │    │   Node   │    │   Node   │        │
│   │          │    │          │    │          │        │
│   │•Reflect  │    │•Spawn    │    │•Extract  │        │
│   │•Optimize │    │•Manage   │    │•Evolve   │        │
│   │•Evolve   │    │•Balance  │    │•Recognize│        │
│   └────┬─────┘    └────┬─────┘    └──────────┘        │
│        │               │                               │
│        └───────────────┘                               │
│                  │                                      │
│           Message Bus                                  │
└──────────────────┴──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                 Worker Swarm Layer                       │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│   │ Coder   │ │ Writer  │ │ Searcher│ │ Reviewer│     │
│   │Subagent │ │Subagent │ │Subagent │ │Subagent │     │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Node Responsibilities

| Node | Responsibility | Input | Output |
|------|----------------|-------|--------|
| **Wizard** | Individual evolution: self-reflection, strategy optimization | Decision history, Librarian knowledge | Strategy updates, replication requests |
| **Mother** | Swarm evolution: agent orchestration, load balancing | Task requests, Wizard requests | Agent creation/termination commands |
| **Librarian** | Knowledge evolution: experience extraction, pattern recognition | Worker execution records | Knowledge insights, optimization suggestions |

---

## 📊 Current Status

**Stage**: Proof-of-Concept Prototype

✅ **Completed**:
- Three-layer node infrastructure
- Message bus communication mechanism
- Shared memory (SQLite)
- Basic health monitoring

⚠️ **Prototype Limitations**:
- ❌ Subagent creation is a stub (not bridged to nanobot API)
- ❌ Evolution mechanism lacks LLM-driven analysis (simple counting only)
- ❌ No dynamic task graph generation
- ❌ Knowledge extraction lacks deep analysis

See: [Technical Specification](docs/HIVEMIND_NANOBOT_TECH_SPEC.md) (Chinese)

---

## 🎯 Roadmap

### Design Inspirations

This project stands on the shoulders of two excellent open-source projects:

#### Foundation: nanobot

> **Acknowledgment**: Special thanks to the [HKUDS](https://github.com/HKUDS) team for open-sourcing [nanobot](https://github.com/HKUDS/nanobot). nanobot provides a lightweight (~4,000 lines), highly extensible agent infrastructure with 40+ communication channels and a rich ClawHub Skill ecosystem. Our three-layer mother node architecture is built as an extension on top of nanobot, reusing its message bus, subagent management, channel integrations, and other core capabilities.

**Core capabilities inherited from nanobot**:
- 40+ channel integrations (Telegram, Discord, Feishu, etc.)
- ClawHub Skill ecosystem (browser control, file operations, API calls)
- Lightweight architecture design (easy deployment, low resource footprint)
- Subagent lifecycle management

#### Evolution Roadmap: Hive

> **Acknowledgment**: Special thanks to the [Aden](https://github.com/aden-hive) team for open-sourcing [Hive](https://github.com/aden-hive/hive). Hive is an enterprise-grade AI agent production framework, and its core concepts — conversational agent design, dynamic graph generation, adaptive evolution — have provided invaluable inspiration for our improvement roadmap.

**Key designs borrowed from Hive** (see [Deep Comparison Analysis](docs/DEEP_ANALYSIS_HIVE_VS_HIVEMIND.md) - Chinese):
1. **Conversational agent design workflow** (from Hive's Queen node)
2. **LLM-driven failure analysis and evolution** (from Hive's adaptive mechanism)
3. **Dynamic task graph generation** (from Hive's GraphExecutor)

### Phase 1: Core Capability Gap (2 weeks - MVP)

**Goal**: Enable real subagent creation and execution

- [x] Message bus and shared memory
- [ ] Bridge to nanobot `sessions_spawn` API
- [ ] Conversational design workflow in Mother node (3-6 turn requirements clarification)
- [ ] LLM-driven failure analysis in Librarian

**Reference**: Hive's `queen_lifecycle_tools.py` and `worker_memory.py`

### Phase 2: Simplified Graph System (2 weeks)

**Goal**: Support task decomposition into 3-5 sub-nodes

- [ ] `TaskGraph` data structure (simplified, no full dissolution mechanism)
- [ ] Task decomposition executor
- [ ] Inter-node data flow

**Reference**: Hive's `executor.py` and `NodeSpec` design

### Phase 3: Evolution Mechanism (2 weeks)

**Goal**: Truly learn from failures and improve

- [ ] Automatic failure diagnosis and improvement suggestions
- [ ] Knowledge A/B testing and promotion mechanism
- [ ] Dynamic strategy adjustment

**Reference**: Hive's `replan_agent()` and digest generation mechanism

### Phase 4: Observability (1 week)

- [ ] Health monitoring (stall/doom loop detection)
- [ ] Auto-generated run summaries
- [ ] EventBus enhancements

**Reference**: Hive's `HealthMonitor` and event system

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Example

```bash
# Basic example: Start HiveMind and demonstrate three-layer node collaboration
python examples/basic_hivemind.py
```

### Configuration

Edit `config/hivemind_config.json`:

```json
{
  "hivemind": {
    "enabled": true,
    "memory_path": "~/.nanobot/hivemind_memory.db",
    "nodes": {
      "wizard": {
        "reflection_interval": 300,
        "evolution_threshold": 10
      },
      "mother": {
        "max_swarm_size": 20
      },
      "librarian": {
        "extraction_interval": 600
      }
    }
  }
}
```

---

## 📚 Documentation

- [Technical Specification](docs/HIVEMIND_NANOBOT_TECH_SPEC.md) (Chinese) - Full architecture design
- [Deep Comparison Analysis](docs/DEEP_ANALYSIS_HIVE_VS_HIVEMIND.md) (Chinese) - Detailed comparison with aden-hive

---

## 🤝 Contributing

PRs and Issues are welcome!

### Current Priorities

1. Implement real subagent creation (bridge nanobot API)
2. LLM-driven Librarian analysis
3. Conversational agent design workflow

---

## 📝 License

MIT License

---

## 🙏 Acknowledgments

### Core Dependency

- **[nanobot](https://github.com/HKUDS/nanobot) by HKUDS** - Provides the lightweight (~4,000 lines), multi-channel (40+) agent foundation. Our three-layer mother node architecture is built on top of nanobot's message bus, subagent management, and channel integrations, fully leveraging its ClawHub Skill ecosystem.

### Design Inspiration

- **[Hive](https://github.com/aden-hive/hive) by Aden** - Enterprise-grade AI agent production framework. Its conversational agent design, dynamic graph generation, adaptive evolution, and Queen/Worker collaboration patterns have provided invaluable inspiration for our roadmap.

### Ecosystem Support

- **OpenClaw Community** - Provides agent development toolchain and best practices

---

## 📞 Contact

- Issues: [GitHub Issues](https://github.com/hongyuatcufe/hivemind-nanobot/issues)
- Discussions: [GitHub Discussions](https://github.com/hongyuatcufe/hivemind-nanobot/discussions)

---

**Project Status**: Early prototype stage — feedback and suggestions welcome 🌱
