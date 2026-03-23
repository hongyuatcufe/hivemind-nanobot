# 深度代码分析：aden-hive vs hivemind-nanobot

**日期**: 2026-03-23  
**分析基础**: 完整源代码对比

---

## 一、代码规模对比

| 项目 | 核心代码行数 | 复杂度 | 定位 |
|-----|------------|--------|------|
| **aden-hive** | ~25,000行+ (core/framework/) | 高 | 企业级 Agent 生产框架 |
| **hivemind-nanobot** | ~500行 (src/hivemind/) | 低 | 轻量级三层进化原型 |
| **nanobot** | ~4,000行 | 中 | 轻量级单 Agent 框架 |

**结论**: aden-hive 是**重型框架**（约是 nanobot 的 6 倍），你们的 hivemind-nanobot 只是轻量级扩展层。

---

## 二、核心架构深度对比

### 2.1 Queen Agent（编码母节点）

#### aden-hive 实现：
```python
# core/framework/agents/queen/nodes/__init__.py (59,000 行!)
_queen_identity_planning = "你是经验丰富的解决方案架构师..."
_planning_knowledge = """
# 工具发现（强制）
list_agent_tools() → 逐步发现
  1. provider summary (第1步，强制)
  2. service breakdown (第2步)
  3. tool names (第3步)
  4. full detail (第4步，仅需要的服务)

# 设计流程图
- save_agent_draft() → 创建仅视觉的 ISO 5807 流程图
- decision nodes (黄色菱形) → 自动溶解到前置节点的 success_criteria
- GCU/browser nodes (深蓝六边形) → 自动溶解到父节点的 sub_agents 列表
- confirm_and_build() → 记录用户批准
- initialize_and_build_agent() → 生成代码并切换到 BUILDING 阶段
"""

_building_knowledge = """
# 实现
initialize_and_build_agent(agent_name, nodes) 生成：
- config.py, nodes/__init__.py, agent.py, __init__.py, __main__.py
- mcp_servers.json, tests/conftest.py
→ 结构完整，通过验证即可使用
"""

# 四阶段状态机
phase_state = QueenPhaseState(
    phase="planning",  # planning → building → staging → running
    draft_graph=None,
    build_confirmed=False
)
```

**关键特性**：
1. **对话式设计流程**: 3-6轮理解需求 → 工具发现 → 能力评估 → 设计流程图 → 获取批准
2. **流程图驱动代码生成**: `save_agent_draft()` 创建可视化 → `confirm_and_build()` 溶解决策节点 → `initialize_and_build_agent()` 生成完整代码
3. **四阶段生命周期**: planning (只读探索) → building (代码生成) → staging (配置验证) → running (监控执行)
4. **动态 system prompt**: 每个阶段有独立的 prompt、tools 和行为约束
5. **内置 LLM**: Queen 本身就是 event_loop_node，持续运行并处理用户消息

#### hivemind-nanobot 实现：
```python
# src/hivemind/nodes.py (~700行)
class WizardNode(BaseNode):
    async def _self_reflection(self):
        # 简单统计成功率
        success_rate = sum(1 for d in recent_decisions if d.get('success'))
        
        # 查询知识（无实际优化逻辑）
        await self.send_message(NodeType.LIBRARIAN, 'query', {...})

class MotherNode(BaseNode):
    async def _spawn_agent(self, parent_id, agent_type, capabilities):
        # 空壳实现
        print(f"Spawning subagent: {agent_id}")
        return True  # 未实际创建
```

**差距**：
- ❌ 无对话式设计流程
- ❌ 无代码生成能力
- ❌ 子 Agent 创建是伪代码
- ❌ 无阶段状态机
- ❌ 无 LLM 驱动的反思/优化

---

### 2.2 Graph 架构

#### aden-hive 的 Graph 系统：

```python
# core/framework/graph/node.py
class NodeSpec(BaseModel):
    """节点声明式定义"""
    id: str
    name: str
    description: str
    node_type: str  # "event_loop" | "gcu" | "basic"
    system_prompt: str
    tools: list[str]
    input_keys: list[str]
    output_keys: list[str]
    success_criteria: str  # LLM judge 评估
    sub_agents: list[str] = []  # GCU/browser 子节点溶解后存放这里

# core/framework/graph/edge.py
class EdgeSpec(BaseModel):
    """边定义"""
    source_node: str
    target_node: str
    condition: EdgeCondition  # on_success, on_failure, default
    label: str  # 用于决策节点的 "Yes"/"No"

# core/framework/graph/executor.py
class GraphExecutor:
    """图执行引擎"""
    async def execute(self, graph, goal, input_data):
        """
        执行流程：
        1. 初始化共享记忆 SharedMemory
        2. 按拓扑序执行节点
        3. 每个节点执行完后：
           - Level 0 judge: output_keys 是否都设置了
           - Level 2 judge (如果有 success_criteria): LLM 评估对话质量
        4. 根据 edge condition 选择下一个节点
        5. 支持并行分支 (fan-out)
        6. 记录所有决策到 Runtime
        """

# 并行执行支持
@dataclass
class ParallelExecutionConfig:
    on_branch_failure: str = "fail_all"  # "continue_others" | "wait_all"
    memory_conflict_strategy: str = "last_wins"
    branch_timeout_seconds: float = 300.0
```

**关键特性**：
1. **动态图生成**: Queen 从目标生成 NodeSpec + EdgeSpec
2. **自适应溶解**: 
   - Decision 节点 → 溶解到前置节点的 `success_criteria`
   - GCU/browser 节点 → 溶解到父节点的 `sub_agents` 列表
3. **双层 Judge**:
   - Level 0: 输出键完整性检查
   - Level 2: LLM 读对话评估质量（防止"打勾"而不干活）
4. **并行分支**: 支持 fan-out，可配置失败策略
5. **事件驱动**: 每个节点执行都发布事件到 EventBus

#### hivemind-nanobot 的架构：

```python
# 无 Graph 概念！
# 只有三个固定的母节点
nodes = {
    NodeType.WIZARD: WizardNode(...),
    NodeType.MOTHER: MotherNode(...),
    NodeType.LIBRARIAN: LibrarianNode(...)
}

# 节点间通过 MessageBus 通信
await message_bus.send(NodeMessage(
    from_node=NodeType.WIZARD,
    to_node=NodeType.LIBRARIAN,
    message_type='query',
    payload={...}
))
```

**差距**：
- ❌ 没有动态 Graph 生成
- ❌ 没有任务拆解成子节点的能力
- ❌ 没有 Judge 评估机制
- ❌ 没有并行执行
- ❌ 三个节点是硬编码的，无法适应不同任务

---

### 2.3 Worker Agent（蜂群执行层）

#### aden-hive 的 Worker 生命周期：

```python
# core/framework/runner/runner.py
class AgentRunner:
    """Worker agent 运行器"""
    async def run(self, input_data: dict):
        """
        1. 加载 agent.py 中的 GraphSpec
        2. 创建 GraphExecutor
        3. 执行 graph.execute()
        4. 监控健康状态（stall/doom_loop detection）
        5. 失败时自动重试（可配置策略）
        6. 写入 run diary (worker_memory.py)
        """

# core/framework/agents/worker_memory.py
def write_run_digest(agent_name: str, run_id: str, events: list):
    """
    Worker 每次运行结束后，LLM 自动生成 digest：
    - 任务是什么
    - 使用了哪些工具
    - 结果如何（成功/失败/部分）
    - 有哪些重试/escalation
    → 存储到 ~/.hive/agents/{name}/runs/{run_id}/digest.md
    """

# 监控与自愈
class HealthMonitor:
    async def check_stall(self, node_id: str):
        """
        检测 stall 模式：
        - 连续 N 个 retry 无进展
        - 同一工具重复调用（doom loop）
        - 超过 4 分钟无输出
        → 触发 escalation 到 Queen
        """
```

**Worker 特性**：
1. **独立进程**: 每个 Worker 是一个独立的 AgentRunner 实例
2. **运行日志**: 每次执行写 digest.md（LLM 生成的摘要）
3. **健康监控**: 自动检测 stall/doom loop
4. **escalation 机制**: 遇到问题自动上报 Queen
5. **Queen 可以注入消息**: 解除阻塞或提供指导

#### hivemind-nanobot 的蜂群：

```python
# src/hivemind/loop.py
async def _spawn_subagent(self, agent_type, agent_id, capabilities):
    # 空壳！只是打印日志
    print(f"Spawning subagent: {agent_id}")
    # 实际实现需要调用 nanobot 的 API
    return True
```

**差距**：
- ❌ 完全没实现
- ❌ 无运行日志
- ❌ 无健康监控
- ❌ 无 escalation 机制

---

### 2.4 Evolution（进化机制）

#### aden-hive 的自适应进化：

```python
# core/framework/tools/queen_lifecycle_tools.py

# 1. 失败捕获
async def stop_worker_and_plan():
    """
    Worker 失败后：
    1. Queen 切换到 PLANNING 阶段
    2. 加载失败的 checkpoints/sessions
    3. 分析根因（工具、逻辑、凭证）
    4. 提出修复方案
    5. 获取用户批准
    6. 切换到 BUILDING 并实施修复
    """

async def replan_agent():
    """
    用户要求重新设计时：
    1. 恢复原始 draft_graph（包含 decision/browser 节点）
    2. 让 Queen 与用户讨论修改
    3. 更新 save_agent_draft()
    4. 重新 confirm_and_build() → 重新生成代码
    """

# 2. 知识积累
def write_run_digest(agent_name, run_id, events):
    """
    每次运行都生成摘要 → 累积到 runs/ 目录
    Queen 查询时可以看到历史失败模式
    """

# 3. 流程图持久化
def save_flowchart_file(agent_name, draft_graph):
    """
    保存 flowchart.json → 包含：
    - 原始设计（decision nodes, browser nodes）
    - 溶解后的运行时版本
    - 可视化渲染元数据
    → 前端可以对比"设计时"和"运行时"的差异
    """
```

**进化路径**：
```
运行失败 → Queen 诊断 → 提出修复方案 → 用户批准 → 重新生成代码 → 部署
```

#### hivemind-nanobot 的进化：

```python
# src/hivemind/nodes.py - LibrarianNode
async def _extract_patterns(self):
    # 简单计数
    for exp in experiences:
        task_type = exp.get('task_type')
        if outcome == 'success':
            success_patterns[task_type] += 1

# src/hivemind/nodes.py - WizardNode
async def _apply_insights(self, insights):
    # 更新策略字典
    self.current_strategy.update(strategy_update)
```

**差距**：
- ❌ 没有失败分析
- ❌ 没有重新生成代码的能力
- ❌ 模式提炼只是计数，无 LLM 驱动
- ❌ 无流程图持久化

---

## 三、关键技术差异表

| 特性 | aden-hive | hivemind-nanobot | 建议 |
|------|-----------|-----------------|------|
| **Queen/母节点** |  |  |  |
| - 对话式设计 | ✅ 3-6轮需求澄清 | ❌ | 🔴 必须 |
| - 代码生成 | ✅ 完整包生成 | ❌ | 🔴 必须 |
| - 阶段状态机 | ✅ 4阶段 | ❌ | 🟡 可选 |
| - LLM 驱动 | ✅ event_loop_node | ❌ | 🔴 必须 |
| **Graph 系统** |  |  |  |
| - 动态图生成 | ✅ 从目标生成 | ❌ | 🔴 必须 |
| - 节点溶解 | ✅ decision/GCU → 运行时 | ❌ | 🟡 可选 |
| - Judge 评估 | ✅ 双层（输出+质量） | ❌ | 🟡 建议 |
| - 并行分支 | ✅ fan-out | ❌ | 🟢 可选 |
| **Worker 管理** |  |  |  |
| - 实际创建 | ✅ AgentRunner | ❌ 空壳 | 🔴 必须 |
| - 运行日志 | ✅ digest.md | ❌ | 🟡 建议 |
| - 健康监控 | ✅ stall/doom loop | ❌ | 🟡 建议 |
| - Escalation | ✅ 自动上报 | ❌ | 🟡 建议 |
| **进化机制** |  |  |  |
| - 失败分析 | ✅ LLM 诊断 | ❌ 计数 | 🔴 必须 |
| - 代码重生成 | ✅ replan → rebuild | ❌ | 🔴 必须 |
| - 知识积累 | ✅ digest 历史 | ⚠️ SQLite 记录 | 🟡 优化 |
| **工具生态** |  |  |  |
| - 工具发现 | ✅ MCP 逐步发现 | ❌ | 🟡 建议 |
| - 浏览器控制 | ✅ GCU (Playwright) | ⚠️ nanobot skill | 🟢 可选 |
| - 凭证管理 | ✅ 集中管理+验证 | ❌ | 🟡 建议 |
| **可观测性** |  |  |  |
| - EventBus | ✅ 完整事件流 | ⚠️ 基础 | 🟡 优化 |
| - 前端可视化 | ✅ React UI | ❌ | 🟢 可选 |
| - 流程图同步 | ✅ 实时更新 | ❌ | 🟡 建议 |

**图例**:
- 🔴 **必须**: 核心功能缺失
- 🟡 **建议**: 影响体验
- 🟢 **可选**: Nice to have

---

## 四、核心学习要点

### 4.1 必须借鉴的设计

#### (1) Queen 的对话式设计流程

**为什么重要**: 用户不需要学习编程，只需对话就能得到可运行的 agent。

**实现路径**:
```python
# Phase 1: 需求澄清（3-6轮）
async def clarify_requirements(user_input):
    """
    Queen 问题清单：
    1. 数据源在哪？
    2. 触发方式？（定时 / 手动 / 事件）
    3. 输出到哪？
    4. 需要人工审批吗？
    """
    
# Phase 2: 工具发现
async def discover_tools():
    """
    list_agent_tools() 逐步发现：
    - provider summary → 快速概览
    - service breakdown → 只展开相关的
    - tool names → 获取工具名（无描述）
    - full detail → 仅查看要用的工具
    """

# Phase 3: 生成流程图草稿
async def generate_draft_flowchart(requirements, available_tools):
    """
    用 LLM 从需求生成 NodeSpec 列表：
    - 每个节点的职责
    - 需要哪些工具
    - 输入/输出键
    - 成功标准（自然语言）
    """
    draft = await llm.complete(f"""
    根据以下需求设计 agent 流程：
    {requirements}
    
    可用工具：{available_tools}
    
    输出格式：
    nodes:
      - id: gather_data
        name: 收集数据
        tools: [google_sheets_read]
        success_criteria: 读取至少 10 条记录
    edges:
      - from: gather_data
        to: process_data
        condition: on_success
    """)
    return draft

# Phase 4: 代码生成
async def generate_agent_code(draft_flowchart):
    """
    从流程图生成实际代码：
    - config.py (Goal, SuccessCriteria, Constraints)
    - nodes/__init__.py (NodeSpec 定义)
    - agent.py (GraphSpec + 边定义)
    """
```

**你们的改进**:
```python
# hivemind/mother_node.py (新增)
class MotherNode:
    async def design_agent_with_user(self, initial_request: str):
        """交互式设计流程"""
        # 1. 理解需求
        requirements = await self._clarify_requirements(initial_request)
        
        # 2. 工具发现（简化版：从 nanobot skills 查询）
        available_skills = await self._discover_nanobot_skills()
        
        # 3. 生成流程图
        draft_graph = await self._generate_draft(requirements, available_skills)
        
        # 4. 展示并获取批准
        approved = await self._show_and_confirm(draft_graph)
        
        # 5. 生成 subagent 配置
        if approved:
            await self._spawn_agent_from_draft(draft_graph)
```

---

#### (2) Graph 的动态生成与溶解

**为什么重要**: 用户看到的流程图（有决策节点）和实际运行的图（溶解后）不同，但保持一致性。

**实现路径**:
```python
# hivemind/graph.py (新增)
@dataclass
class SimpleTaskGraph:
    """简化版任务图"""
    nodes: List[TaskNode]  # 节点列表
    edges: List[TaskEdge]  # 边列表
    
    def dissolve_decision_nodes(self):
        """溶解决策节点到前置节点的条件"""
        for node in self.nodes:
            if node.type == "decision":
                # 找到前置节点
                predecessors = [e.source for e in self.edges if e.target == node.id]
                for pred_id in predecessors:
                    pred_node = self.get_node(pred_id)
                    pred_node.success_criteria = node.decision_clause
                    
                    # 重新连接边
                    yes_edge = next(e for e in self.edges 
                                   if e.source == node.id and e.label == "Yes")
                    no_edge = next(e for e in self.edges 
                                  if e.source == node.id and e.label == "No")
                    
                    pred_node.on_success = yes_edge.target
                    pred_node.on_failure = no_edge.target
                
                # 移除决策节点
                self.nodes.remove(node)
```

---

#### (3) LLM 驱动的失败分析

**为什么重要**: 不是简单重试，而是理解为什么失败并调整策略。

**实现路径**:
```python
# hivemind/librarian_node.py (增强)
class LibrarianNode:
    async def analyze_failure_with_llm(self, failure_records: List[Dict]):
        """用 LLM 分析失败模式"""
        prompt = f"""
        分析以下失败案例：
        
        {json.dumps(failure_records, indent=2)}
        
        请提供：
        1. 根因分析（为什么失败）
        2. 共性模式（是否系统性问题）
        3. 具体改进建议（代码、配置、逻辑）
        """
        
        insights = await self.llm.complete(prompt)
        
        # 提取可执行的改进
        improvements = self._extract_actionable_improvements(insights)
        
        # 存储到知识库
        await self.memory.store_knowledge(Knowledge(
            id=f"failure_insight_{timestamp}",
            content=insights,
            category="failure_pattern",
            improvements=improvements,
            status="verified"
        ))
        
        return improvements
```

---

### 4.2 可选但有价值的设计

#### (1) 双层 Judge 评估

```python
# Level 0: 输出键完整性
def check_output_keys(node: TaskNode, memory: SharedMemory):
    for key in node.output_keys:
        if key not in memory:
            return False, f"Missing output key: {key}"
    return True, ""

# Level 2: 质量评估（可选，但提升质量）
async def check_quality(node: TaskNode, conversation: List[Dict]):
    """LLM 读对话评估是否真正完成"""
    prompt = f"""
    节点目标: {node.success_criteria}
    最近对话: {conversation[-10:]}
    
    问题: 该节点是否真正完成了目标？（不是只填了表单）
    回答: ACCEPT / RETRY
    原因: ...
    """
    verdict = await llm.complete(prompt)
    return verdict
```

#### (2) EventBus 实时监控

```python
# hivemind/event_bus.py (增强)
class EnhancedEventBus(NodeMessageBus):
    """扩展事件总线"""
    
    async def publish(self, event: Event):
        """发布事件到所有订阅者 + 持久化"""
        # 1. 实时分发
        await super().send(event)
        
        # 2. 写入事件日志
        await self._persist_event(event)
        
        # 3. 触发告警（如果是严重事件）
        if event.severity == "critical":
            await self._trigger_alert(event)
```

---

## 五、具体改进路线图（优先级排序）

### Phase 1: 核心能力补齐（2周，MVP）

**目标**: 让 hivemind-nanobot 能真正创建并运行 subagent

#### Week 1: 桥接 nanobot subagent
```python
# 1.1 实现真正的 spawn
async def _spawn_subagent(self, agent_type, agent_id, capabilities):
    # 调用 nanobot 的 sessions_spawn
    result = await self._call_nanobot_spawn(
        runtime="subagent",
        task=f"你是 {agent_type} agent，能力：{capabilities}",
        label=agent_id
    )
    
    # 订阅 subagent 输出
    await self._subscribe_to_subagent_events(agent_id)
    
    return result

# 1.2 简化版 Mother 设计对话
async def design_simple_agent(self, user_request):
    """3步骤简化流程"""
    # Step 1: 问清楚要做什么
    requirements = await self._ask_requirements(user_request)
    
    # Step 2: 从 nanobot skills 匹配能力
    skills = self._match_skills(requirements)
    
    # Step 3: 生成配置并创建
    config = self._generate_config(requirements, skills)
    agent_id = await self._spawn_with_config(config)
    
    return agent_id
```

#### Week 2: LLM 驱动的 Librarian
```python
# 2.1 用 LLM 分析经验
async def _extract_patterns_with_llm(self, experiences):
    prompt = f"""
    从以下经验中提取成功/失败模式：
    {experiences}
    
    输出：
    - 成功共性
    - 失败原因
    - 可复用策略
    """
    insights = await self.llm.complete(prompt)
    return self._parse_insights(insights)

# 2.2 知识供给优化
async def _query_for_strategy(self, context):
    # 不只是返回 production insights
    # 而是根据 context 动态生成建议
    relevant_knowledge = await self.memory.query_knowledge(
        category="success_pattern",
        context=context
    )
    
    recommendations = await self.llm.complete(f"""
    基于以下知识：{relevant_knowledge}
    针对场景：{context}
    给出 3 条策略建议
    """)
    
    return recommendations
```

---

### Phase 2: 简化版 Graph 系统（2周）

**目标**: 支持任务拆解成子节点，但不做完整的动态生成

```python
# hivemind/simple_graph.py (新增)
@dataclass
class TaskNode:
    """任务节点"""
    id: str
    name: str
    agent_type: str  # "coder" | "writer" | "searcher"
    description: str
    tools: List[str]
    success_criteria: str
    on_success: Optional[str] = None  # 下一个节点
    on_failure: Optional[str] = None

@dataclass
class TaskGraph:
    """任务图"""
    nodes: List[TaskNode]
    entry_node: str
    
    async def execute(self, mother_node: MotherNode, input_data: Dict):
        """执行图"""
        current = self.entry_node
        memory = {}  # 共享记忆
        
        while current:
            node = self.get_node(current)
            
            # 创建 subagent 执行节点
            agent_id = await mother_node._spawn_agent_for_node(node)
            result = await mother_node._wait_for_completion(agent_id)
            
            # 更新记忆
            memory.update(result.output)
            
            # 决定下一步
            if result.success:
                current = node.on_success
            else:
                current = node.on_failure
        
        return memory
```

---

### Phase 3: 进化机制完善（2周）

```python
# 3.1 失败后的自动改进
async def handle_failure(self, agent_id: str, error: Dict):
    """失败处理"""
    # 1. 收集失败上下文
    context = await self._collect_failure_context(agent_id, error)
    
    # 2. LLM 分析
    analysis = await self.librarian._analyze_failure_with_llm([context])
    
    # 3. 生成改进方案
    improvements = analysis['improvements']
    
    # 4. 询问用户是否应用
    approved = await self._confirm_improvements(improvements)
    
    # 5. 应用改进（修改 agent 配置）
    if approved:
        await self._apply_improvements(agent_id, improvements)
        
        # 6. 重新运行
        await self._retry_with_improvements(agent_id)

# 3.2 知识进化（A/B测试）
async def evolve_knowledge(self, knowledge_id: str):
    """知识验证与升级"""
    knowledge = await self.memory.get_knowledge(knowledge_id)
    
    # 小流量验证（10% 的任务）
    success_rate = await self._ab_test(knowledge, traffic_ratio=0.1)
    
    if success_rate > 0.8:
        # 升级到 production
        await self.memory.promote_knowledge(knowledge_id, "production")
    else:
        # 降级或删除
        await self.memory.demote_knowledge(knowledge_id)
```

---

### Phase 4: 可观测性与监控（1周）

```python
# 4.1 健康监控
class HealthMonitor:
    async def monitor_agent(self, agent_id: str):
        """持续监控 agent 健康"""
        while True:
            status = await self._check_status(agent_id)
            
            # 检测 stall
            if status.no_progress_for > 4 * 60:  # 4分钟无进展
                await self._escalate_to_mother(agent_id, "stall")
            
            # 检测 doom loop
            if status.same_tool_count > 5:
                await self._escalate_to_mother(agent_id, "doom_loop")
            
            await asyncio.sleep(30)

# 4.2 运行摘要
async def generate_run_digest(agent_id: str, events: List[Dict]):
    """每次运行后生成摘要"""
    prompt = f"""
    总结以下 agent 运行：
    
    事件：{events}
    
    格式：
    - 任务：...
    - 方法：...
    - 结果：成功/失败
    - 问题：...
    """
    
    digest = await llm.complete(prompt)
    
    # 存储
    await self.memory.store_experience(Experience(
        agent_id=agent_id,
        digest=digest,
        events=events
    ))
```

---

## 六、总结建议

### 你们的优势
1. ✅ **轻量级**: 基于 nanobot，部署简单
2. ✅ **架构清晰**: 三层职责分离明确
3. ✅ **扩展性好**: 基于 nanobot 的 40+ 渠道和技能生态

### 核心差距
1. ❌ **无代码生成**: Queen 不能从对话生成 agent
2. ❌ **无动态图**: 任务不能拆解成子节点
3. ❌ **进化是空壳**: LLM 分析缺失，无法真正改进

### 优先级建议

#### 🔴 **必须做（P0）**
1. **实现 Mother 的对话式设计**: 3-6轮需求澄清 → 生成 subagent 配置
2. **桥接 nanobot subagent API**: 让 spawn 真正能创建 agent
3. **LLM 驱动的 Librarian**: 用 LLM 分析失败，而不是简单计数

#### 🟡 **建议做（P1）**
4. **简化版 TaskGraph**: 支持 3-5 个节点的简单拆解
5. **失败自动改进**: 失败后 LLM 提出修复方案
6. **运行摘要**: 每次执行后生成 digest

#### 🟢 **可选（P2）**
7. **双层 Judge**: 质量评估
8. **并行分支**: Fan-out 执行
9. **Web UI**: 可视化监控

---

## 七、实施策略

### 不要完全模仿 aden-hive
- ❌ 不要做 4 阶段状态机（太复杂）
- ❌ 不要做完整的 Graph 溶解（你们用不到 decision nodes）
- ❌ 不要自己实现浏览器控制（用 nanobot 的 skill）

### 充分利用 nanobot 生态
- ✅ Mother 生成的是"nanobot subagent 配置"，不是完整 Python 包
- ✅ 工具发现用 nanobot 的 skill 体系，不需要 MCP
- ✅ 渠道复用 nanobot 的 40+ 集成

### 快速验证路径
**Week 1-2**: 实现 Mother 对话式设计 + 真实 spawn  
**Week 3-4**: LLM 驱动的 Librarian 分析  
**Week 5-6**: 简化版 TaskGraph  
**Demo**: 用户说"我要一个每天抓取 Hacker News 的 agent" → Mother 对话设计 → 自动创建并运行

---

**最后**: aden-hive 是企业级重型框架（25k+ 行），你们做轻量级扩展层（目标 2-3k 行）即可。**专注核心价值**：让 nanobot 从"单 agent"变成"会自己设计和管理多 agent 的系统"。
