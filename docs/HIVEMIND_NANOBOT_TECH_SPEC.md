# HiveMind-nanobot 技术方案

> 基于 nanobot 构建的多 Agent 进化系统  
> 版本：v1.0  
> 日期：2026-03-09

---

## 1. 项目概述

### 1.1 背景

nanobot 是一个超轻量级（~4,000行代码）的 AI Agent 框架，支持 40+ 渠道和 ClawHub Skill 生态。本项目将其改造为支持 **三层进化架构**（Wizard/Mother/Librarian）的 HiveMind 系统。

### 1.2 核心目标

- 保留 nanobot 的所有渠道和 Skill 生态
- 实现三层母节点的协作与进化
- 支持轻量级蜂群 Agent 的动态创建
- 建立共享记忆和知识进化机制

### 1.3 架构对比

| 特性 | 原生 nanobot | HiveMind-nanobot |
|------|-------------|------------------|
| 架构 | 单 Agent | 三层母节点 + 蜂群 |
| 代码量 | ~4,000行 | ~4,500行 |
| 渠道 | 40+ | 40+（保留）|
| Skill | ClawHub | ClawHub（保留）|
| 子 Agent | 简单 spawn | 进化式管理 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      HiveMind-nanobot                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  三层母节点层                             │   │
│  │                                                         │   │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐        │   │
│  │   │  Wizard  │◄──►│  Mother  │◄──►│ Librarian│        │   │
│  │   │  节点    │    │  节点    │    │  节点    │        │   │
│  │   │          │    │          │    │          │        │   │
│  │   │•自我反思  │    │•创生子体  │    │•经验提取  │        │   │
│  │   │•策略优化  │    │•蜂群管理  │    │•知识进化  │        │   │
│  │   │•能力进化  │    │•结构调整  │    │•模式识别  │        │   │
│  │   └────┬─────┘    └────┬─────┘    └──────────┘        │   │
│  │        │               │                               │   │
│  │        └───────────────┘                               │   │
│  │                  │                                      │   │
│  │           Message Bus                                  │   │
│  │        (nanobot bus/)                                  │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                           │
│  ┌──────────────────┴──────────────────────────────────────┐   │
│  │                    蜂群执行层                             │   │
│  │                                                         │   │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │   │
│  │   │ Coder   │ │ Writer  │ │ Searcher│ │ Reviewer│     │   │
│  │   │Subagent │ │Subagent │ │Subagent │ │Subagent │     │   │
│  │   └─────────┘ └─────────┘ └─────────┘ └─────────┘     │   │
│  │                                                         │   │
│  │   (复用 nanobot agent/subagent.py)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    基础设施层                             │   │
│  │                                                         │   │
│  │   • Memory: 复用 nanobot memory + 扩展知识图谱           │   │
│  │   • Channels: 复用 nanobot channels/ (40+)              │   │
│  │   • Skills: 复用 nanobot skills/ + ClawHub              │   │
│  │   • Cron: 复用 nanobot cron/                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
任务输入
    │
    ▼
┌─────────────┐
│   Mother    │ ◄── 决定使用哪些蜂群 Agent
│   调度决策   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   蜂群执行   │────►│  Librarian  │
│  (Subagent) │     │  记录经验   │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Wizard    │ ◄── 获取知识优化策略
                    │   自我反思   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Mother    │ ◄── 决定是否进化蜂群
                    │   群体调整   │
                    └─────────────┘
```

---

## 3. 核心组件设计

### 3.1 三层母节点

#### 3.1.1 Wizard 节点（个体进化）

**职责**：
- 自我反思：分析决策历史，识别改进点
- 策略优化：基于 Librarian 知识更新处理策略
- 能力进化：积累足够经验后通知 Mother 复制

**输入**：
- Librarian 提供的知识 insights
- 自身历史决策记录
- 任务执行反馈

**输出**：
- 更新的策略配置
- 复制请求（给 Mother）

#### 3.1.2 Mother 节点（群体进化）

**职责**：
- 蜂群管理：创建、监控、终止子 Agent
- 负载均衡：根据任务量动态调整蜂群规模
- 结构调整：增删 Agent 类型，优化协作流程

**输入**：
- 任务请求
- Wizard 的复制请求
- Librarian 的优化建议

**输出**：
- Subagent 创建/终止指令
- 蜂群结构配置

#### 3.1.3 Librarian 节点（知识进化）

**职责**：
- 经验提取：从蜂群执行记录中提炼模式
- 知识存储：分级管理（draft/verified/production）
- 知识供给：响应 Wizard/Mother 的查询

**输入**：
- 蜂群 Agent 的执行记录
- 知识查询请求

**输出**：
- 提炼的知识模式
- 优化建议

### 3.2 消息总线

复用 nanobot 的 `bus/` 模块，扩展为节点间通信：

```python
class NodeMessageBus:
    """节点间消息总线"""
    
    async def send(self, from_node: NodeType, to_node: NodeType, 
                   msg_type: str, payload: dict)
    
    async def broadcast(self, from_node: NodeType, 
                        msg_type: str, payload: dict)
    
    async def subscribe(self, node: NodeType, 
                        callback: Callable[[NodeMessage], None])
```

### 3.3 共享记忆

扩展 nanobot memory 为三层结构：

```
Memory/
├── raw_experiences/          # 原始经验（蜂群上报）
│   └── {agent_id}_{timestamp}.json
├── patterns/                 # 提炼模式（Librarian 生成）
│   ├── success_patterns/
│   └── failure_patterns/
├── knowledge/                # 生产知识
│   ├── draft/
│   ├── verified/
│   └── production/
└── swarm_registry/           # 蜂群注册表
    └── agents.json
```

---

## 4. 代码实现

### 4.1 目录结构

```
hivemind-nanobot/
├── src/
│   ├── hivemind/
│   │   ├── __init__.py
│   │   ├── loop.py              # 改造后的主循环
│   │   ├── nodes.py             # 三层节点实现
│   │   ├── message_bus.py       # 节点通信
│   │   ├── shared_memory.py     # 共享记忆
│   │   └── swarm_manager.py     # 蜂群管理
│   └── nanobot_patches/         # 对 nanobot 的补丁
│       ├── agent_loop_patch.py
│       └── memory_patch.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── examples/
│   ├── basic_hivemind.py
│   └── advanced_evolution.py
├── tests/
│   ├── test_nodes.py
│   └── test_integration.py
├── config/
│   └── hivemind_config.json
├── requirements.txt
└── README.md
```

### 4.2 核心类图

```
┌─────────────────────┐
│   HiveMindLoop      │
│   (主循环)           │
├─────────────────────┤
│ - nodes: Dict       │
│ - message_bus       │
│ - shared_memory     │
├─────────────────────┤
│ + run()             │
│ + route_message()   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌──────────┐
│BaseNode │  │SwarmAgent│
│(抽象基类)│  │(蜂群基类) │
└────┬────┘  └────┬─────┘
     │            │
  ┌──┴──┐      ┌──┴──┐
  ▼     ▼      ▼     ▼
┌───┐ ┌───┐ ┌───┐ ┌───┐
│ W │ │ M │ │ L │ │ C │
│ i │ │ o │ │ i │ │ o │
│ z │ │ t │ │ b │ │ d │
│ a │ │ h │ │ r │ │ e │
│ r │ │ e │ │ a │ │ r │
│ d │ │ r │ │ r │ │   │
└───┘ └───┘ └───┘ └───┘

W=Wizard  M=Mother  L=Librarian  C=Coder/Writer/Searcher...
```

### 4.3 关键接口

```python
# 节点接口
class BaseNode(ABC):
    @abstractmethod
    async def run(self): pass
    
    @abstractmethod
    async def handle_message(self, msg: NodeMessage): pass

# 蜂群接口
class SwarmAgent(ABC):
    @abstractmethod
    async def execute(self, task: Task) -> Result: pass
    
    @abstractmethod
    async def report_experience(self, experience: Experience): pass

# 记忆接口
class SharedMemory(ABC):
    @abstractmethod
    async def store_experience(self, exp: Experience): pass
    
    @abstractmethod
    async def query_knowledge(self, query: str) -> List[Knowledge]: pass
    
    @abstractmethod
    async def register_agent(self, agent_id: str, info: AgentInfo): pass
```

---

## 5. 进化机制

### 5.1 个体进化（Wizard）

```
执行 Task ──► 记录决策 ──► 反思复盘 ──► 查询 Librarian ──► 优化策略
    ▲                                                      │
    └──────────────────── 应用新策略 ────────────────────────┘

触发条件：
- 完成 N 个任务
- 发现系统性偏差
- 累积经验达到阈值
```

### 5.2 群体进化（Mother）

```
监控蜂群 ──► 识别瓶颈 ──► 咨询 Librarian ──► 获取方案 ──► 调整结构
    ▲                                                      │
    └──────────────── 观察效果 ──► 沉淀经验 ─────────────────┘

触发条件：
- 任务成功率低于阈值
- 新领域需求出现
- 系统负载不均衡
```

### 5.3 知识进化（Librarian）

```
收集原始经验 ──► 清洗分类 ──► 提炼模式 ──► 分级存储 ──► 供给 insights
       ▲                                              │
       └────────── 持续接收反馈 ────────────────────────┘

知识分级：
- draft: 新提炼，待验证
- verified: 小流量验证通过
- production: 全量可用
```

---

## 6. 部署方案

### 6.1 单节点部署

适合开发和测试：

```bash
# 1. 克隆 nanobot
git clone https://github.com/HKUDS/nanobot.git
cd nanobot

# 2. 应用 HiveMind 补丁
cp -r ../hivemind-nanobot/src/hivemind nanobot/
cp ../hivemind-nanobot/src/nanobot_patches/* nanobot/agent/

# 3. 安装依赖
pip install -e .

# 4. 配置
nanobot onboard --config ~/.nanobot/hivemind_config.json

# 5. 启动
nanobot gateway --config ~/.nanobot/hivemind_config.json
```

### 6.2 多实例部署

适合生产环境：

```bash
# 启动三个母节点实例（使用不同配置）
nanobot gateway --config ~/.nanobot/wizard_config.json --port 18790
nanobot gateway --config ~/.nanobot/mother_config.json --port 18791
nanobot gateway --config ~/.nanobot/librarian_config.json --port 18792
```

### 6.3 Docker 部署

```yaml
# docker-compose.yml
version: '3'
services:
  wizard:
    build: .
    command: nanobot gateway --config /config/wizard.json
    volumes:
      - ./config:/config
      - hivemind-memory:/memory
    
  mother:
    build: .
    command: nanobot gateway --config /config/mother.json
    volumes:
      - ./config:/config
      - hivemind-memory:/memory
      
  librarian:
    build: .
    command: nanobot gateway --config /config/librarian.json
    volumes:
      - ./config:/config
      - hivemind-memory:/memory

volumes:
  hivemind-memory:
```

---

## 7. 开发路线图

### Phase 1: 基础框架 (2 周)
- [ ] 改造 nanobot loop 支持多节点
- [ ] 实现 MessageBus
- [ ] 实现基础的三层节点
- [ ] 扩展 memory 支持共享存储

### Phase 2: 蜂群系统 (2 周)
- [ ] 复用 nanobot subagent
- [ ] 实现 SwarmManager
- [ ] 实现动态创建/终止
- [ ] 实现负载均衡

### Phase 3: 进化机制 (2 周)
- [ ] 实现经验收集
- [ ] 实现模式提炼
- [ ] 实现知识分级
- [ ] 实现灰度发布

### Phase 4: 监控与治理 (2 周)
- [ ] 实现健康监控
- [ ] 实现熔断机制
- [ ] 实现一键回滚
- [ ] 实现审计日志

### Phase 5: 优化与生态 (持续)
- [ ] 性能优化
- [ ] 更多渠道适配
- [ ] ClawHub Skill 适配
- [ ] 可视化面板

---

## 8. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| nanobot 版本不兼容 | 中 | 高 | 锁定版本，定期同步 |
| 性能瓶颈 | 中 | 中 | 基准测试，逐步优化 |
| 数据竞争 | 低 | 高 | SQLite WAL，锁机制 |
| 无限循环 | 低 | 高 | LoopGuard，熔断 |

---

## 9. 参考资料

- [nanobot GitHub](https://github.com/HKUDS/nanobot)
- [OpenClaw 文档](https://docs.openclaw.ai)
- [HiveMind 架构设计](/docs/hivemind-architecture-design.md)

---

**作者**: HiveMind Team  
**License**: MIT (同 nanobot)
