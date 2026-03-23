"""
HiveMind-nanobot 消息总线
实现三层节点间的通信
"""

import asyncio
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from .nodes import NodeMessage, NodeType


@dataclass
class BusMetrics:
    """消息总线指标"""
    messages_routed: int = 0
    messages_dropped: int = 0
    errors: int = 0
    start_time: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


class NodeMessageBus:
    """
    节点间消息总线
    
    实现：
    - 点对点消息路由
    - 广播消息分发
    - 消息持久化（可选）
    - 死信队列
    """
    
    def __init__(self, max_queue_size: int = 1000, 
                 message_timeout: float = 30.0):
        self.max_queue_size = max_queue_size
        self.message_timeout = message_timeout
        
        # 节点注册表
        self._handlers: Dict[NodeType, List[Callable[[NodeMessage], None]]] = {
            NodeType.WIZARD: [],
            NodeType.MOTHER: [],
            NodeType.LIBRARIAN: []
        }
        
        # 消息队列（广播用）
        self._broadcast_queue: asyncio.Queue[NodeMessage] = asyncio.Queue(
            maxsize=max_queue_size
        )
        
        # 指标
        self.metrics = BusMetrics()
        
        # 运行状态
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """启动消息总线"""
        self._running = True
        
        # 启动广播分发任务
        task = asyncio.create_task(self._broadcast_dispatcher())
        self._tasks.append(task)
        
        print("[MessageBus] Started")
    
    async def stop(self):
        """停止消息总线"""
        self._running = False
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待清理
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        print("[MessageBus] Stopped")
    
    def register_handler(self, node_type: NodeType, 
                        handler: Callable[[NodeMessage], None]):
        """注册节点消息处理器"""
        if node_type not in self._handlers:
            self._handlers[node_type] = []
        
        self._handlers[node_type].append(handler)
        print(f"[MessageBus] Registered handler for {node_type.value}")
    
    def unregister_handler(self, node_type: NodeType,
                          handler: Callable[[NodeMessage], None]):
        """注销节点消息处理器"""
        if node_type in self._handlers:
            if handler in self._handlers[node_type]:
                self._handlers[node_type].remove(handler)
    
    async def send(self, message: NodeMessage) -> bool:
        """
        发送消息（点对点或广播）
        
        Args:
            message: 消息对象
            
        Returns:
            是否成功发送
        """
        try:
            if message.to_node is None:
                # 广播消息
                await self._broadcast_queue.put(message)
            else:
                # 点对点消息
                await self._route_direct(message)
            
            self.metrics.messages_routed += 1
            return True
            
        except asyncio.QueueFull:
            print(f"[MessageBus] Queue full, message dropped")
            self.metrics.messages_dropped += 1
            return False
            
        except Exception as e:
            print(f"[MessageBus] Send error: {e}")
            self.metrics.errors += 1
            return False
    
    async def _route_direct(self, message: NodeMessage):
        """直接路由消息到目标节点"""
        target_node = message.to_node
        
        if target_node not in self._handlers:
            print(f"[MessageBus] No handlers for {target_node.value}")
            return
        
        handlers = self._handlers[target_node]
        
        # 并发调用所有处理器
        if handlers:
            await asyncio.gather(*[
                self._safe_call_handler(handler, message)
                for handler in handlers
            ])
    
    async def _broadcast_dispatcher(self):
        """广播消息分发器"""
        while self._running:
            try:
                # 等待广播消息
                message = await asyncio.wait_for(
                    self._broadcast_queue.get(),
                    timeout=1.0
                )
                
                # 分发给所有节点（除发送者外）
                for node_type, handlers in self._handlers.items():
                    if node_type != message.from_node:
                        await asyncio.gather(*[
                            self._safe_call_handler(handler, message)
                            for handler in handlers
                        ])
                
                self._broadcast_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
                
            except Exception as e:
                print(f"[MessageBus] Broadcast error: {e}")
                self.metrics.errors += 1
    
    async def _safe_call_handler(self, handler: Callable, 
                                  message: NodeMessage):
        """安全调用处理器"""
        try:
            # 支持同步和异步处理器
            if asyncio.iscoroutinefunction(handler):
                await asyncio.wait_for(
                    handler(message),
                    timeout=self.message_timeout
                )
            else:
                handler(message)
                
        except asyncio.TimeoutError:
            print(f"[MessageBus] Handler timeout for message {message.message_id}")
            
        except Exception as e:
            print(f"[MessageBus] Handler error: {e}")
            self.metrics.errors += 1
    
    def get_metrics(self) -> Dict:
        """获取指标"""
        uptime = datetime.now() - self.metrics.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'messages_routed': self.metrics.messages_routed,
            'messages_dropped': self.metrics.messages_dropped,
            'errors': self.metrics.errors,
            'handlers': {
                node_type.value: len(handlers)
                for node_type, handlers in self._handlers.items()
            },
            'broadcast_queue_size': self._broadcast_queue.qsize()
        }


class PersistentMessageBus(NodeMessageBus):
    """
    持久化消息总线
    
    将消息持久化到存储，支持故障恢复
    """
    
    def __init__(self, storage_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_path = storage_path
        self._pending_messages: List[NodeMessage] = []
    
    async def send(self, message: NodeMessage) -> bool:
        """发送消息并持久化"""
        # 先持久化
        await self._persist_message(message)
        
        # 再发送
        result = await super().send(message)
        
        # 成功后删除
        if result:
            await self._remove_persisted(message)
        
        return result
    
    async def _persist_message(self, message: NodeMessage):
        """持久化消息"""
        # 简化实现：写入文件
        import json
        from pathlib import Path
        
        path = Path(self.storage_path) / "pending_messages.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'message_id': message.message_id,
            'from_node': message.from_node.value,
            'to_node': message.to_node.value if message.to_node else None,
            'message_type': message.message_type,
            'payload': message.payload,
            'timestamp': message.timestamp.isoformat()
        }
        
        # 追加写入
        with open(path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    async def _remove_persisted(self, message: NodeMessage):
        """移除已持久化的消息"""
        # 简化实现：实际应该使用更高效的存储
        pass
    
    async def recover(self) -> List[NodeMessage]:
        """恢复未处理的消息"""
        import json
        from pathlib import Path
        
        path = Path(self.storage_path) / "pending_messages.json"
        
        if not path.exists():
            return []
        
        messages = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    msg = NodeMessage(
                        from_node=NodeType(data['from_node']),
                        to_node=NodeType(data['to_node']) if data['to_node'] else None,
                        message_type=data['message_type'],
                        payload=data['payload'],
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        message_id=data['message_id']
                    )
                    messages.append(msg)
                except Exception as e:
                    print(f"[MessageBus] Recovery error: {e}")
        
        return messages
