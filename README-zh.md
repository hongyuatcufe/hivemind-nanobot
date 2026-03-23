# HiveMind-nanobot

> 轻量级多 Agent 进化系统 - 基于 [nanobot](https://github.com/HKUDS/nanobot) 的三层母节点架构

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: Prototype](https://img.shields.io/badge/Status-Prototype-yellow.svg)]()

**语言版本**: [English](README.md) | [简体中文](README-zh.md)

---

## 📖 项目简介

HiveMind-nanobot 是一个轻量级的多 Agent 进化系统，**基于 [nanobot](https://github.com/HKUDS/nanobot) 框架**（~4,000行）构建。我们在保留 nanobot 的轻量特性、40+ 渠道集成和 ClawHub Skill 生态的基础上，引入**三层母节点协作架构**，实现 Agent 的自我进化与知识积累。

**设计理念**: 不是替代 nanobot，而是在其之上添加进化能力 —— 让 nanobot 从"单 Agent 框架"进化为"会自己设计和管理多 Agent 的系统"。

### 核心特性

- 🧠 **三层母节点**: Wizard（个体进化）、Mother（群体进化）、Librarian（知识进化）
- 🔄 **消息总线**: 节点间异步通信，解耦设计
- 💾 **共享记忆**: SQLite 持久化存储，支持经验积累与知识分级
- 🐝 **蜂群管理**: 动态创建与管理子 Agent
- 🌱 **进化机制**: 从失败中学习，持续优化策略

---

## 🏗️ 架构设计

### 三层母节点

```
┌─────────────────────────────────────────────────────────┐
│                    三层母节点层                           │
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │  Wizard  │◄──►│  Mother  │◄──►│ Librarian│        │
│   │  节点    │    │  节点    │    │  节点    │        │
│   │          │    │          │    │          │        │
│   │•自我反思  │    │•创生子体  │    │•经验提取  │        │
│   │•策略优化  │    │•蜂群管理  │    │•知识进化  │        │
│   │•能力进化  │    │•结构调整  │    │•模式识别  │        │
│   └────┬─────┘    └────┬─────┘    └──────────┘        │
│        │               │                               │
│        └───────────────┘                               │
│                  │                                      │
│           Message Bus                                  │
└──────────────────┴──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                    蜂群执行层                             │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│   │ Coder   │ │ Writer  │ │ Searcher│ │ Reviewer│     │
│   │Subagent │ │Subagent │ │Subagent │ │Subagent │     │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 节点职责

| 节点 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Wizard** | 个体进化：自我反思、策略优化 | 决策历史、Librarian知识 | 策略更新、复制请求 |
| **Mother** | 群体进化：蜂群管理、负载均衡 | 任务请求、Wizard请求 | Agent创建/终止指令 |
| **Librarian** | 知识进化：经验提炼、模式识别 | 蜂群执行记录 | 知识insights、优化建议 |

---

## 📊 当前状态

**阶段**: 概念验证原型（Prototype）

✅ **已完成**:
- 三层节点基础架构
- 消息总线通信机制
- 共享记忆（SQLite）
- 基础健康监控

⚠️ **原型局限**:
- ❌ 子 Agent 创建是空壳（未桥接 nanobot API）
- ❌ 进化机制缺少 LLM 驱动（仅简单计数）
- ❌ 无动态任务图生成能力
- ❌ 知识提炼无深度分析

详见: [技术方案文档](docs/HIVEMIND_NANOBOT_TECH_SPEC.md)

---

## 🎯 改进路线图

### 设计灵感来源

本项目站在两个优秀开源项目的肩膀上：

#### 基座框架：nanobot

> **致谢**: 特别感谢 [HKUDS](https://github.com/HKUDS) 团队开源的 [nanobot](https://github.com/HKUDS/nanobot) 框架。nanobot 提供了轻量级（~4,000行）、高可扩展的 Agent 基础设施，支持 40+ 通信渠道和丰富的 ClawHub Skill 生态。我们的三层母节点架构正是在 nanobot 的基础上扩展而来，复用了其消息总线、subagent 管理、渠道集成等核心能力。

**从 nanobot 继承的核心能力**：
- 40+ 渠道集成（Telegram, Discord, 飞书等）
- ClawHub Skill 生态（浏览器控制、文件操作、API 调用）
- 轻量级架构设计（易部署、低资源占用）
- Subagent 生命周期管理

#### 进化方向参考：Hive

> **致谢**: 特别感谢 [Aden](https://github.com/aden-hive) 团队开源的 [Hive](https://github.com/aden-hive/hive) 框架。Hive 是企业级的 AI Agent 生产框架，其对话式 Agent 设计、动态图生成、自适应进化等核心理念为我们的改进方向提供了宝贵的启发。

**借鉴 Hive 的核心设计**（详见 [深度对比分析](docs/DEEP_ANALYSIS_HIVE_VS_HIVEMIND.md)）：
1. **对话式 Agent 设计流程**（来自 Hive Queen 节点）
2. **LLM 驱动的失败分析与进化**（来自 Hive 自适应机制）
3. **动态任务图生成**（来自 Hive GraphExecutor）

### Phase 1: 核心能力补齐（2周 - MVP）

**目标**: 让系统能真正创建并运行 subagent

- [x] 实现消息总线与共享记忆
- [ ] 桥接 nanobot `sessions_spawn` API
- [ ] Mother 节点的对话式设计流程（3-6轮需求澄清）
- [ ] Librarian 的 LLM 驱动失败分析

**参考**: Hive 的 `queen_lifecycle_tools.py` 和 `worker_memory.py`

### Phase 2: 简化版 Graph 系统（2周）

**目标**: 支持任务拆解成 3-5 个子节点

- [ ] `TaskGraph` 数据结构（简化版，非完整溶解机制）
- [ ] 任务拆解执行器
- [ ] 节点间数据流传递

**参考**: Hive 的 `executor.py` 和 `NodeSpec` 设计

### Phase 3: 进化机制完善（2周）

**目标**: 从失败中真正学习并改进

- [ ] 失败自动诊断与改进建议
- [ ] 知识 A/B 测试与升级机制
- [ ] 策略动态调整

**参考**: Hive 的 `replan_agent()` 和 digest 生成机制

### Phase 4: 可观测性（1周）

- [ ] 健康监控（stall/doom loop detection）
- [ ] 运行摘要自动生成
- [ ] EventBus 增强

**参考**: Hive 的 `HealthMonitor` 和事件系统

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
# 基础示例：启动 HiveMind 并演示三层节点协作
python examples/basic_hivemind.py
```

### 配置

编辑 `config/hivemind_config.json`:

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

## 📚 文档

- [技术方案](docs/HIVEMIND_NANOBOT_TECH_SPEC.md) - 完整架构设计
- [深度对比分析](docs/DEEP_ANALYSIS_HIVE_VS_HIVEMIND.md) - 与 aden-hive 的详细对比

---

## 🤝 贡献

欢迎 PR 和 Issue！

### 当前优先级

1. 实现真实的 subagent 创建（桥接 nanobot API）
2. LLM 驱动的 Librarian 分析
3. 对话式 Agent 设计流程

---

## 📝 License

MIT License

---

## 🙏 致谢

### 核心依赖

- **[nanobot](https://github.com/HKUDS/nanobot) by HKUDS** - 提供轻量级（~4,000行）、多渠道（40+）的 Agent 基础框架。我们的三层母节点架构建立在 nanobot 的消息总线、subagent 管理和渠道集成之上，充分复用其 ClawHub Skill 生态。

### 设计灵感

- **[Hive](https://github.com/aden-hive/hive) by Aden** - 企业级 AI Agent 生产框架，其对话式 Agent 设计、动态图生成、自适应进化、Queen/Worker 协作模式等核心理念为我们的改进路线图提供了宝贵的启发。

### 生态支持

- **OpenClaw 社区** - 提供 Agent 开发工具链与最佳实践

---

## 📞 联系

- Issues: [GitHub Issues](https://github.com/hongyuatcufe/hivemind-nanobot/issues)
- Discussions: [GitHub Discussions](https://github.com/hongyuatcufe/hivemind-nanobot/discussions)

---

**项目状态**: 早期原型阶段，欢迎反馈与建议 🌱
