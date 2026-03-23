"""
HiveMind-nanobot 基础示例

演示如何运行一个完整的 HiveMind 系统
"""

import asyncio
from pathlib import Path

from hivemind import (
    HiveMindLoop,
    NodeType,
    Experience,
    Knowledge
)


async def basic_example():
    """基础示例：启动 HiveMind 并演示三层节点协作"""
    
    print("=" * 60)
    print("HiveMind-nanobot Basic Example")
    print("=" * 60)
    
    # 配置
    config = {
        'memory_path': 'example_hivemind.db',
        'message_bus': {
            'max_queue_size': 500,
            'message_timeout': 30.0
        },
        'wizard': {
            'reflection_interval': 10,  # 10个任务反思一次（演示用）
            'evolution_threshold': 5    # 5个 insights 触发进化
        },
        'mother': {
            'max_swarm_size': 10,
            'load_balance_interval': 30
        },
        'librarian': {
            'extraction_interval': 20  # 20个周期提炼一次
        }
    }
    
    # 创建 HiveMind
    hivemind = HiveMindLoop(config)
    
    # 模拟一些初始数据
    print("\n[Example] Seeding initial data...")
    await seed_initial_data(hivemind)
    
    # 启动监控任务
    monitor_task = asyncio.create_task(monitor_status(hivemind))
    
    # 启动 HiveMind（运行60秒）
    print("\n[Example] Starting HiveMind (will run for 60 seconds)...")
    
    hivemind_task = asyncio.create_task(hivemind.start())
    
    # 等待60秒
    await asyncio.sleep(60)
    
    # 停止
    print("\n[Example] Stopping HiveMind...")
    hivemind._shutdown_event.set()
    
    # 等待任务完成
    await asyncio.gather(hivemind_task, monitor_task, return_exceptions=True)
    
    # 打印最终状态
    print("\n" + "=" * 60)
    print("Final Status:")
    print("=" * 60)
    status = hivemind.get_status()
    
    for node_name, node_health in status['nodes'].items():
        print(f"\n{node_name}:")
        print(f"  Messages received: {node_health['messages_received']}")
        print(f"  Messages sent: {node_health['messages_sent']}")
        print(f"  Errors: {node_health['errors']}")
    
    print("\nMessage Bus:")
    print(f"  Routed: {status['message_bus']['messages_routed']}")
    print(f"  Dropped: {status['message_bus']['messages_dropped']}")
    
    print("\n" + "=" * 60)


async def seed_initial_data(hivemind: HiveMindLoop):
    """播种初始数据"""
    
    # 添加一些模拟经验
    experiences = [
        Experience(
            agent_id="coder_1",
            task_id="task_001",
            task_type="code_review",
            decision_chain=[
                {"step": "analyze", "tool": "ast_parser"},
                {"step": "check_style", "tool": "pylint"}
            ],
            outcome="success",
            metadata={"duration": 12.5, "files": 3}
        ),
        Experience(
            agent_id="writer_1",
            task_id="task_002",
            task_type="documentation",
            decision_chain=[
                {"step": "outline", "tool": "llm"},
                {"step": "refine", "tool": "grammar_check"}
            ],
            outcome="success",
            metadata={"word_count": 500}
        )
    ]
    
    for exp in experiences:
        await hivemind.memory.store_experience(exp)
    
    print(f"  ✓ Seeded {len(experiences)} experiences")
    
    # 添加一些初始知识
    knowledge_items = [
        Knowledge(
            id="k001",
            content="Code reviews are most effective with AST analysis",
            source="experience",
            category="success_pattern",
            confidence=0.8,
            status="production"
        ),
        Knowledge(
            id="k002",
            content="Documentation benefits from outline-first approach",
            source="experience",
            category="success_pattern",
            confidence=0.7,
            status="verified"
        )
    ]
    
    for k in knowledge_items:
        await hivemind.memory.store_knowledge(k)
    
    print(f"  ✓ Seeded {len(knowledge_items)} knowledge items")


async def monitor_status(hivemind: HiveMindLoop):
    """监控状态（每10秒打印一次）"""
    try:
        for i in range(6):  # 60秒 / 10秒 = 6次
            await asyncio.sleep(10)
            
            status = hivemind.get_status()
            
            print(f"\n[Monitor] Status update #{i+1}")
            print(f"  Wizard: {status['nodes']['wizard']['messages_sent']} msgs sent")
            print(f"  Mother: {status['nodes']['mother']['messages_sent']} msgs sent")
            print(f"  Librarian: {status['nodes']['librarian']['messages_sent']} msgs sent")
            
    except asyncio.CancelledError:
        pass


async def advanced_example():
    """高级示例：演示子 Agent 创建和知识进化"""
    
    print("\n" + "=" * 60)
    print("Advanced Example: Agent Spawning and Knowledge Evolution")
    print("=" * 60)
    
    config = {
        'memory_path': 'advanced_hivemind.db',
        'wizard': {'reflection_interval': 5},
        'mother': {'max_swarm_size': 15},
        'librarian': {'extraction_interval': 10}
    }
    
    hivemind = HiveMindLoop(config)
    
    # 启动
    hivemind_task = asyncio.create_task(hivemind.start())
    
    # 模拟复杂交互
    await asyncio.sleep(3)
    
    # 手动触发 Mother 创建子 Agent
    mother_node = hivemind.nodes[NodeType.MOTHER]
    
    print("\n[Example] Manually spawning agents...")
    await mother_node._spawn_agent(None, 'coder', ['python', 'testing'])
    await mother_node._spawn_agent(None, 'writer', ['documentation'])
    
    # 检查蜂群状态
    await asyncio.sleep(2)
    swarm_status = mother_node.get_swarm_status()
    print(f"\n[Example] Swarm status: {swarm_status['total_agents']} agents")
    print(f"  By type: {swarm_status['by_type']}")
    
    # 运行一段时间
    await asyncio.sleep(30)
    
    # 查询知识
    librarian_node = hivemind.nodes[NodeType.LIBRARIAN]
    insights = await librarian_node._query_for_strategy({})
    print(f"\n[Example] Available insights: {len(insights)}")
    
    # 停止
    hivemind._shutdown_event.set()
    await hivemind_task
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'advanced':
        asyncio.run(advanced_example())
    else:
        asyncio.run(basic_example())


if __name__ == '__main__':
    main()
