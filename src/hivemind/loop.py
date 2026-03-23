"""
HiveMind-nanobot 主循环
整合三层节点和消息总线
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import signal
import sys

from .nodes import (
    NodeType, NodeMessage, BaseNode,
    WizardNode, MotherNode, LibrarianNode
)
from .message_bus import NodeMessageBus
from .shared_memory import SharedMemory


class HiveMindLoop:
    """
    HiveMind 主循环
    
    整合三层母节点：
    - Wizard: 个体进化
    - Mother: 群体进化
    - Librarian: 知识进化
    
    通过 MessageBus 实现节点间通信
    通过 SharedMemory 实现状态共享
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 初始化共享记忆
        memory_path = self.config.get('memory_path', 'hivemind_memory.db')
        self.memory = SharedMemory(memory_path)
        
        # 初始化消息总线
        bus_config = self.config.get('message_bus', {})
        self.message_bus = NodeMessageBus(
            max_queue_size=bus_config.get('max_queue_size', 1000),
            message_timeout=bus_config.get('message_timeout', 30.0)
        )
        
        # 初始化三层节点
        self.nodes: Dict[NodeType, BaseNode] = {}
        self._init_nodes()
        
        # 运行状态
        self.running = False
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # 统计
        self.start_time: Optional[datetime] = None
        self.cycle_count = 0
    
    def _init_nodes(self):
        """初始化三层节点"""
        # Wizard 节点配置
        wizard_config = self.config.get('wizard', {})
        self.nodes[NodeType.WIZARD] = WizardNode(
            node_id=f"wizard_{datetime.now().strftime('%H%M%S')}",
            memory=self.memory,
            message_bus=self.message_bus,
            config=wizard_config
        )
        
        # Mother 节点配置
        mother_config = self.config.get('mother', {})
        self.nodes[NodeType.MOTHER] = MotherNode(
            node_id=f"mother_{datetime.now().strftime('%H%M%S')}",
            memory=self.memory,
            message_bus=self.message_bus,
            config=mother_config,
            spawn_fn=self._spawn_subagent
        )
        
        # Librarian 节点配置
        librarian_config = self.config.get('librarian', {})
        self.nodes[NodeType.LIBRARIAN] = LibrarianNode(
            node_id=f"librarian_{datetime.now().strftime('%H%M%S')}",
            memory=self.memory,
            message_bus=self.message_bus,
            config=librarian_config
        )
        
        # 注册节点处理器到消息总线
        for node_type, node in self.nodes.items():
            self.message_bus.register_handler(
                node_type,
                node.receive_message
            )
    
    async def _spawn_subagent(self, agent_type: str, 
                             agent_id: str,
                             capabilities: List[str]) -> bool:
        """
        创建子 Agent（复用 nanobot 的 subagent）
        
        这是 Mother 节点的回调函数
        """
        try:
            # 这里复用 nanobot 的 spawn_subagent
            # from nanobot.agent.subagent import spawn_subagent
            # await spawn_subagent(...)
            
            # 简化实现：打印日志
            print(f"[HiveMind] Spawning subagent: {agent_id} ({agent_type})")
            
            # 实际实现需要调用 nanobot 的 API
            return True
            
        except Exception as e:
            print(f"[HiveMind] Spawn failed: {e}")
            return False
    
    async def start(self):
        """启动 HiveMind"""
        print("=" * 50)
        print("HiveMind-nanobot Starting...")
        print("=" * 50)
        
        self.running = True
        self.start_time = datetime.now()
        
        # 启动消息总线
        await self.message_bus.start()
        
        # 启动所有节点
        for node_type, node in self.nodes.items():
            task = asyncio.create_task(node.run())
            self._tasks.append(task)
            print(f"[HiveMind] Started {node_type.value} node")
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 启动监控任务
        monitor_task = asyncio.create_task(self._monitor_loop())
        self._tasks.append(monitor_task)
        
        print("[HiveMind] All nodes started, entering main loop")
        print("=" * 50)
        
        # 等待关闭信号
        await self._shutdown_event.wait()
        
        # 执行关闭
        await self.stop()
    
    async def stop(self):
        """停止 HiveMind"""
        print("\n" + "=" * 50)
        print("HiveMind-nanobot Stopping...")
        print("=" * 50)
        
        self.running = False
        
        # 停止所有节点
        for node in self.nodes.values():
            node.running = False
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # 停止消息总线
        await self.message_bus.stop()
        
        # 打印统计
        await self._print_stats()
        
        print("[HiveMind] Stopped")
        print("=" * 50)
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(sig, frame):
            print(f"\n[HiveMind] Received signal {sig}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                if not self.running:
                    break
                
                self.cycle_count += 1
                
                # 打印健康状态
                if self.cycle_count % 5 == 0:  # 每5分钟
                    await self._print_health()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[HiveMind] Monitor error: {e}")
    
    async def _print_health(self):
        """打印健康状态"""
        print("\n" + "-" * 50)
        print(f"[HiveMind] Health Check #{self.cycle_count}")
        print("-" * 50)
        
        # 节点状态
        for node_type, node in self.nodes.items():
            health = node.get_health()
            print(f"  {node_type.value:12} | "
                  f"uptime: {health['uptime_seconds']:.0f}s | "
                  f"msgs: {health['messages_received']}/{health['messages_sent']}")
        
        # 消息总线状态
        bus_metrics = self.message_bus.get_metrics()
        print(f"  {'message_bus':12} | "
              f"routed: {bus_metrics['messages_routed']} | "
              f"dropped: {bus_metrics['messages_dropped']}")
        
        # 记忆状态
        memory_health = await self.memory.get_health()
        print(f"  {'memory':12} | "
              f"size: {memory_health['db_size_bytes'] / 1024:.1f}KB | "
              f"status: {memory_health['status']}")
        
        print("-" * 50)
    
    async def _print_stats(self):
        """打印最终统计"""
        if not self.start_time:
            return
        
        uptime = datetime.now() - self.start_time
        
        print("\n" + "=" * 50)
        print("HiveMind-nanobot Statistics")
        print("=" * 50)
        print(f"  Uptime: {uptime}")
        print(f"  Monitor cycles: {self.cycle_count}")
        
        # 各节点统计
        for node_type, node in self.nodes.items():
            health = node.get_health()
            print(f"\n  {node_type.value}:")
            print(f"    Messages received: {health['messages_received']}")
            print(f"    Messages sent: {health['messages_sent']}")
            print(f"    Errors: {health['errors']}")
        
        # 消息总线统计
        bus_metrics = self.message_bus.get_metrics()
        print(f"\n  Message Bus:")
        print(f"    Messages routed: {bus_metrics['messages_routed']}")
        print(f"    Messages dropped: {bus_metrics['messages_dropped']}")
        print(f"    Errors: {bus_metrics['errors']}")
        
        print("=" * 50)
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.start_time:
            return {'status': 'not_started'}
        
        uptime = datetime.now() - self.start_time
        
        return {
            'status': 'running' if self.running else 'stopped',
            'uptime_seconds': uptime.total_seconds(),
            'cycle_count': self.cycle_count,
            'nodes': {
                node_type.value: node.get_health()
                for node_type, node in self.nodes.items()
            },
            'message_bus': self.message_bus.get_metrics()
        }


# ==================== 入口函数 ====================

async def run_hivemind(config: Optional[Dict] = None):
    """
    运行 HiveMind
    
    使用示例：
        import asyncio
        from hivemind.loop import run_hivemind
        
        config = {
            'memory_path': 'hivemind.db',
            'wizard': {'reflection_interval': 300},
            'mother': {'max_swarm_size': 20},
            'librarian': {'extraction_interval': 600}
        }
        
        asyncio.run(run_hivemind(config))
    """
    hivemind = HiveMindLoop(config)
    await hivemind.start()


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HiveMind-nanobot')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--memory', '-m', default='hivemind.db', 
                       help='Memory database path')
    
    args = parser.parse_args()
    
    # 加载配置
    config = {
        'memory_path': args.memory
    }
    
    if args.config:
        import json
        with open(args.config) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    # 运行
    try:
        asyncio.run(run_hivemind(config))
    except KeyboardInterrupt:
        print("\n[HiveMind] Interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
