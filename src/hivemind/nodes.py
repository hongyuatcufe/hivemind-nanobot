"""
HiveMind-nanobot 核心模块
基于 nanobot 改造的多 Agent 进化系统
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
import uuid


class NodeType(Enum):
    """节点类型"""
    WIZARD = "wizard"
    MOTHER = "mother"
    LIBRARIAN = "librarian"


@dataclass
class NodeMessage:
    """节点间消息"""
    from_node: NodeType
    to_node: Optional[NodeType]  # None = broadcast
    message_type: str  # query / response / command / event / broadcast
    payload: Dict[str, Any]
    timestamp: datetime = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())[:8]


class BaseNode(ABC):
    """
    母节点基类
    
    所有三层节点（Wizard/Mother/Librarian）的抽象基类
    """
    
    def __init__(
        self,
        node_id: str,
        memory: 'SharedMemory',
        message_bus: 'NodeMessageBus'
    ):
        self.node_id = node_id
        self.memory = memory
        self.message_bus = message_bus
        self.inbox: asyncio.Queue[NodeMessage] = asyncio.Queue()
        self.running = False
        self.metrics = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        """返回节点类型"""
        pass
    
    @abstractmethod
    async def run(self):
        """节点主循环 - 子类必须实现"""
        pass
    
    @abstractmethod
    async def process_cycle(self):
        """处理一个工作周期 - 子类必须实现"""
        pass
    
    async def receive_message(self, msg: NodeMessage):
        """接收消息"""
        await self.inbox.put(msg)
        self.metrics['messages_received'] += 1
    
    async def send_message(
        self,
        to: Optional[NodeType],
        msg_type: str,
        payload: Dict[str, Any]
    ) -> str:
        """发送消息"""
        msg = NodeMessage(
            from_node=self.node_type,
            to_node=to,
            message_type=msg_type,
            payload=payload
        )
        await self.message_bus.send(msg)
        self.metrics['messages_sent'] += 1
        return msg.message_id
    
    async def broadcast(self, msg_type: str, payload: Dict[str, Any]):
        """广播消息"""
        await self.send_message(None, msg_type, payload)
    
    async def handle_message(self, msg: NodeMessage):
        """处理收到的消息 - 可重写"""
        # 默认实现：记录日志
        print(f"[{self.node_type.value}] Received {msg.message_type} from {msg.from_node.value}")
    
    def get_health(self) -> Dict[str, Any]:
        """获取健康状态"""
        uptime = datetime.now() - self.metrics['start_time']
        return {
            'node_type': self.node_type.value,
            'node_id': self.node_id,
            'running': self.running,
            'uptime_seconds': uptime.total_seconds(),
            'messages_received': self.metrics['messages_received'],
            'messages_sent': self.metrics['messages_sent'],
            'errors': self.metrics['errors']
        }


class WizardNode(BaseNode):
    """
    Wizard 节点 - 个体进化层
    
    职责：
    - 自我反思：分析决策历史
    - 策略优化：应用 Librarian 知识
    - 能力进化：触发复制请求
    """
    
    def __init__(self, node_id: str, memory: 'SharedMemory', 
                 message_bus: 'NodeMessageBus', config: Dict = None):
        super().__init__(node_id, memory, message_bus)
        self.config = config or {}
        self.reflection_interval = self.config.get('reflection_interval', 300)  # 5分钟
        self.evolution_threshold = self.config.get('evolution_threshold', 10)
        
        # 状态
        self.decision_history: List[Dict] = []
        self.current_strategy: Dict = {}
        self.insights_applied: List[str] = []
        self.task_count = 0
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.WIZARD
    
    async def run(self):
        """Wizard 主循环"""
        self.running = True
        print(f"[Wizard] Node {self.node_id} started")
        
        while self.running:
            try:
                # 1. 处理消息（非阻塞）
                await self._process_messages()
                
                # 2. 执行工作周期
                await self.process_cycle()
                
                # 3. 等待下一个周期
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[Wizard] Error: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(5)
    
    async def _process_messages(self):
        """处理收件箱消息"""
        try:
            while not self.inbox.empty():
                msg = self.inbox.get_nowait()
                await self.handle_message(msg)
        except asyncio.QueueEmpty:
            pass
    
    async def process_cycle(self):
        """处理一个工作周期"""
        self.task_count += 1
        
        # 每 N 个任务执行一次反思
        if self.task_count % self.reflection_interval == 0:
            await self._self_reflection()
    
    async def handle_message(self, msg: NodeMessage):
        """处理消息"""
        await super().handle_message(msg)
        
        if msg.message_type == "response" and msg.from_node == NodeType.LIBRARIAN:
            # 处理 Librarian 返回的知识
            insights = msg.payload.get('insights', [])
            await self._apply_insights(insights)
            
        elif msg.message_type == "command" and msg.from_node == NodeType.MOTHER:
            # 执行 Mother 的命令
            cmd = msg.payload.get('action')
            if cmd == 'update_strategy':
                await self._update_strategy(msg.payload.get('strategy', {}))
    
    async def _self_reflection(self):
        """自我反思"""
        print(f"[Wizard] Performing self-reflection...")
        
        # 分析近期决策
        recent_decisions = self.decision_history[-50:]
        success_rate = sum(1 for d in recent_decisions if d.get('success')) / max(len(recent_decisions), 1)
        
        # 向 Librarian 查询相关知识
        await self.send_message(
            NodeType.LIBRARIAN,
            'query',
            {
                'query_type': 'strategy_optimization',
                'context': {
                    'success_rate': success_rate,
                    'decision_count': len(self.decision_history),
                    'current_strategy': self.current_strategy
                },
                'limit': 5
            }
        )
        
        # 记录反思
        reflection = {
            'timestamp': datetime.now().isoformat(),
            'task_count': self.task_count,
            'success_rate': success_rate,
            'insights_count': len(self.insights_applied)
        }
        
        await self.memory.store_reflection(self.node_id, reflection)
    
    async def _apply_insights(self, insights: List[Dict]):
        """应用知识 insights"""
        for insight in insights:
            insight_id = insight.get('id')
            if insight_id not in self.insights_applied:
                print(f"[Wizard] Applying insight: {insight.get('content', '')[:50]}...")
                
                # 更新策略
                strategy_update = insight.get('strategy_update', {})
                self.current_strategy.update(strategy_update)
                self.insights_applied.append(insight_id)
        
        # 如果积累了足够多的新 insights，通知 Mother 复制
        if len(self.insights_applied) >= self.evolution_threshold:
            await self._request_spawn()
    
    async def _request_spawn(self):
        """请求 Mother 创建子体"""
        print(f"[Wizard] Requesting spawn due to evolution threshold")
        
        await self.send_message(
            NodeType.MOTHER,
            'command',
            {
                'action': 'spawn',
                'parent_id': self.node_id,
                'parent_type': 'wizard',
                'reason': 'evolution_threshold',
                'capabilities': list(self.current_strategy.keys())
            }
        )
        
        # 重置计数
        self.insights_applied = []
    
    async def _update_strategy(self, strategy: Dict):
        """更新策略"""
        self.current_strategy.update(strategy)
        print(f"[Wizard] Strategy updated: {list(strategy.keys())}")
    
    def record_decision(self, decision: Dict):
        """记录决策（供外部调用）"""
        self.decision_history.append({
            **decision,
            'timestamp': datetime.now().isoformat()
        })
        
        # 限制历史长度
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]


class MotherNode(BaseNode):
    """
    Mother 节点 - 群体进化层
    
    职责：
    - 蜂群管理：创建、监控、终止子 Agent
    - 负载均衡：动态调整蜂群规模
    - 结构调整：优化协作流程
    """
    
    def __init__(self, node_id: str, memory: 'SharedMemory',
                 message_bus: 'NodeMessageBus', config: Dict = None,
                 spawn_fn: Optional[Callable] = None):
        super().__init__(node_id, memory, message_bus)
        self.config = config or {}
        self.spawn_fn = spawn_fn
        self.max_swarm_size = self.config.get('max_swarm_size', 20)
        self.load_balance_interval = self.config.get('load_balance_interval', 60)
        
        # 蜂群状态
        self.swarm: Dict[str, Dict] = {}
        self.pending_tasks: List[Dict] = []
        self.load_history: List[float] = []
        
        # 计数器
        self._agent_counter = 0
        self._cycle_count = 0
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.MOTHER
    
    async def run(self):
        """Mother 主循环"""
        self.running = True
        print(f"[Mother] Node {self.node_id} started")
        
        while self.running:
            try:
                # 1. 处理消息
                await self._process_messages()
                
                # 2. 执行工作周期
                await self.process_cycle()
                
                # 3. 等待
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[Mother] Error: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(5)
    
    async def _process_messages(self):
        """处理消息"""
        try:
            while not self.inbox.empty():
                msg = self.inbox.get_nowait()
                await self.handle_message(msg)
        except asyncio.QueueEmpty:
            pass
    
    async def process_cycle(self):
        """处理一个工作周期"""
        self._cycle_count += 1
        
        # 定期负载均衡
        if self._cycle_count % self.load_balance_interval == 0:
            await self._balance_load()
        
        # 定期健康检查
        if self._cycle_count % 30 == 0:
            await self._health_check()
    
    async def handle_message(self, msg: NodeMessage):
        """处理消息"""
        await super().handle_message(msg)
        
        if msg.message_type == "command":
            cmd = msg.payload.get('action')
            
            if cmd == 'spawn':
                # 创建子 Agent
                await self._spawn_agent(
                    parent_id=msg.payload.get('parent_id'),
                    agent_type=msg.payload.get('agent_type', 'coder'),
                    capabilities=msg.payload.get('capabilities', [])
                )
                
            elif cmd == 'terminate':
                # 终止 Agent
                agent_id = msg.payload.get('agent_id')
                await self._terminate_agent(agent_id)
                
            elif cmd == 'task_request':
                # 任务分配请求
                task = msg.payload.get('task')
                await self._assign_task(task)
    
    async def _spawn_agent(self, parent_id: Optional[str], 
                          agent_type: str,
                          capabilities: List[str]) -> Optional[str]:
        """创建子 Agent"""
        # 检查蜂群大小
        if len(self.swarm) >= self.max_swarm_size:
            print(f"[Mother] Swarm at capacity ({self.max_swarm_size}), cannot spawn")
            return None
        
        # 生成 Agent ID
        self._agent_counter += 1
        agent_id = f"{agent_type}_{self._agent_counter}_{datetime.now().strftime('%H%M%S')}"
        
        # 创建 Agent
        if self.spawn_fn:
            try:
                await self.spawn_fn(
                    agent_type=agent_type,
                    agent_id=agent_id,
                    capabilities=capabilities
                )
            except Exception as e:
                print(f"[Mother] Spawn failed: {e}")
                return None
        
        # 注册到蜂群
        self.swarm[agent_id] = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'parent_id': parent_id,
            'capabilities': capabilities,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'task_count': 0,
            'success_count': 0
        }
        
        # 注册到共享记忆
        await self.memory.register_agent(agent_id, self.swarm[agent_id])
        
        # 广播通知
        await self.broadcast('event', {
            'event_type': 'agent_spawned',
            'agent_id': agent_id,
            'agent_type': agent_type
        })
        
        print(f"[Mother] Spawned agent: {agent_id}")
        return agent_id
    
    async def _terminate_agent(self, agent_id: str):
        """终止 Agent"""
        if agent_id not in self.swarm:
            return
        
        # 更新状态
        self.swarm[agent_id]['status'] = 'terminated'
        
        # 更新共享记忆
        await self.memory.update_agent_status(agent_id, 'terminated')
        
        # 广播
        await self.broadcast('event', {
            'event_type': 'agent_terminated',
            'agent_id': agent_id
        })
        
        # 从活跃列表移除（保留历史）
        del self.swarm[agent_id]
        
        print(f"[Mother] Terminated agent: {agent_id}")
    
    async def _balance_load(self):
        """负载均衡"""
        # 统计各类型 Agent
        by_type: Dict[str, int] = {}
        for agent in self.swarm.values():
            t = agent['agent_type']
            by_type[t] = by_type.get(t, 0) + 1
        
        print(f"[Mother] Load balance check: {by_type}")
        
        # 简单策略：如果某类 Agent 不足，创建更多
        min_per_type = 2
        for agent_type, count in by_type.items():
            if count < min_per_type:
                needed = min_per_type - count
                for _ in range(needed):
                    await self._spawn_agent(None, agent_type, [agent_type])
    
    async def _health_check(self):
        """健康检查"""
        inactive = []
        for agent_id, agent in self.swarm.items():
            # 检查心跳（简化版）
            last_active = datetime.fromisoformat(agent.get('last_active', agent['created_at']))
            idle_time = (datetime.now() - last_active).total_seconds()
            
            # 如果空闲超过 10 分钟，标记为待回收
            if idle_time > 600:
                inactive.append(agent_id)
        
        # 终止不活跃的 Agent
        for agent_id in inactive[:5]:  # 每次最多终止 5 个
            await self._terminate_agent(agent_id)
    
    async def _assign_task(self, task: Dict):
        """分配任务"""
        task_type = task.get('type', 'general')
        
        # 找到合适的 Agent
        candidates = [
            aid for aid, a in self.swarm.items()
            if a['status'] == 'active' and task_type in a.get('capabilities', [])
        ]
        
        if not candidates:
            # 没有合适的，创建一个新的
            agent_id = await self._spawn_agent(None, task_type, [task_type])
            if agent_id:
                candidates = [agent_id]
        
        if candidates:
            # 简单轮询选择
            agent_id = candidates[0]
            # 实际分配...
            print(f"[Mother] Assigned task to {agent_id}")
    
    def get_swarm_status(self) -> Dict:
        """获取蜂群状态"""
        return {
            'total_agents': len(self.swarm),
            'by_type': self._count_by_type(),
            'agents': self.swarm
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for agent in self.swarm.values():
            t = agent['agent_type']
            counts[t] = counts.get(t, 0) + 1
        return counts


class LibrarianNode(BaseNode):
    """
    Librarian 节点 - 知识进化层
    
    职责：
    - 经验提取：从蜂群记录中提炼模式
    - 知识存储：分级管理知识
    - 知识供给：响应查询
    """
    
    def __init__(self, node_id: str, memory: 'SharedMemory',
                 message_bus: 'NodeMessageBus', config: Dict = None):
        super().__init__(node_id, memory, message_bus)
        self.config = config or {}
        self.extraction_interval = self.config.get('extraction_interval', 600)  # 10分钟
        
        # 知识库
        self.patterns: Dict[str, Dict] = {}
        self.insights: Dict[str, Dict] = {}
        
        # 统计
        self.extraction_count = 0
    
    @property
    def node_type(self) -> NodeType:
        return NodeType.LIBRARIAN
    
    async def run(self):
        """Librarian 主循环"""
        self.running = True
        print(f"[Librarian] Node {self.node_id} started")
        
        while self.running:
            try:
                # 1. 处理消息
                await self._process_messages()
                
                # 2. 执行工作周期
                await self.process_cycle()
                
                # 3. 等待
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[Librarian] Error: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(5)
    
    async def _process_messages(self):
        """处理消息"""
        try:
            while not self.inbox.empty():
                msg = self.inbox.get_nowait()
                await self.handle_message(msg)
        except asyncio.QueueEmpty:
            pass
    
    async def process_cycle(self):
        """处理一个工作周期"""
        self.extraction_count += 1
        
        # 定期提炼知识
        if self.extraction_count % self.extraction_interval == 0:
            await self._extract_patterns()
            await self._promote_knowledge()
    
    async def handle_message(self, msg: NodeMessage):
        """处理消息"""
        await super().handle_message(msg)
        
        if msg.message_type == "query":
            # 处理知识查询
            query_type = msg.payload.get('query_type')
            
            if query_type == 'strategy_optimization':
                insights = await self._query_for_strategy(
                    msg.payload.get('context', {})
                )
                
                # 回复
                await self.send_message(
                    msg.from_node,
                    'response',
                    {'insights': insights}
                )
                
            elif query_type == 'swarm_optimization':
                suggestions = await self._query_for_swarm(
                    msg.payload.get('context', {})
                )
                
                await self.send_message(
                    msg.from_node,
                    'response',
                    {'suggestions': suggestions}
                )
    
    async def _extract_patterns(self):
        """从经验中提炼模式"""
        print(f"[Librarian] Extracting patterns...")
        
        # 获取近期经验
        experiences = await self.memory.get_recent_experiences(limit=100)
        
        # 简单统计模式（实际可用 LLM）
        success_patterns = {}
        failure_patterns = {}
        
        for exp in experiences:
            task_type = exp.get('task_type', 'unknown')
            outcome = exp.get('outcome')
            
            if outcome == 'success':
                success_patterns[task_type] = success_patterns.get(task_type, 0) + 1
            else:
                failure_patterns[task_type] = failure_patterns.get(task_type, 0) + 1
        
        # 存储模式
        for task_type, count in success_patterns.items():
            if count >= 3:  # 至少3次成功
                pattern_id = f"success_{task_type}_{datetime.now().strftime('%Y%m%d')}"
                self.patterns[pattern_id] = {
                    'type': 'success',
                    'task_type': task_type,
                    'count': count,
                    'confidence': min(count / 10, 1.0),
                    'status': 'draft'
                }
                
                # 生成 insight
                insight_id = f"insight_{pattern_id}"
                self.insights[insight_id] = {
                    'id': insight_id,
                    'content': f"Successfully handled {count} {task_type} tasks",
                    'pattern_id': pattern_id,
                    'strategy_update': {task_type: 'use_proven_approach'},
                    'status': 'draft'
                }
        
        print(f"[Librarian] Extracted {len(self.patterns)} patterns")
    
    async def _promote_knowledge(self):
        """知识状态升级"""
        # 简单的自动升级策略
        for insight_id, insight in self.insights.items():
            if insight['status'] == 'draft':
                # 检查是否应该升级为 verified
                # 这里简化处理，实际应该基于验证结果
                insight['status'] = 'verified'
                print(f"[Librarian] Promoted {insight_id} to verified")
                
            elif insight['status'] == 'verified':
                # 一段时间后自动升级为 production
                insight['status'] = 'production'
                print(f"[Librarian] Promoted {insight_id} to production")
    
    async def _query_for_strategy(self, context: Dict) -> List[Dict]:
        """查询策略优化知识"""
        # 返回匹配的 production insights
        return [
            insight for insight in self.insights.values()
            if insight['status'] == 'production'
        ][:5]  # 最多返回5个
    
    async def _query_for_swarm(self, context: Dict) -> List[Dict]:
        """查询蜂群优化建议"""
        # 基于负载情况给出建议
        suggestions = []
        
        # 简化示例
        if context.get('coder_count', 0) < 2:
            suggestions.append({
                'type': 'increase_agents',
                'agent_type': 'coder',
                'reason': 'low_coder_count'
            })
        
        return suggestions
