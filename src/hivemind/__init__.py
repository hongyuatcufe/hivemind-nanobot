"""
HiveMind-nanobot
基于 nanobot 的多 Agent 进化系统
"""

__version__ = "0.1.0"
__author__ = "HiveMind Team"

from .loop import HiveMindLoop, run_hivemind
from .nodes import (
    NodeType, NodeMessage, BaseNode,
    WizardNode, MotherNode, LibrarianNode
)
from .message_bus import NodeMessageBus
from .shared_memory import SharedMemory, Experience, Knowledge, Reflection

__all__ = [
    # 主循环
    'HiveMindLoop',
    'run_hivemind',
    
    # 节点
    'NodeType',
    'NodeMessage',
    'BaseNode',
    'WizardNode',
    'MotherNode',
    'LibrarianNode',
    
    # 消息总线
    'NodeMessageBus',
    
    # 共享记忆
    'SharedMemory',
    'Experience',
    'Knowledge',
    'Reflection'
]
