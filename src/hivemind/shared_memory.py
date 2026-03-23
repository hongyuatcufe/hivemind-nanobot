"""
HiveMind-nanobot 共享记忆
实现三层节点间的共享存储
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import hashlib


@dataclass
class Experience:
    """经验记录"""
    agent_id: str
    task_id: str
    task_type: str
    decision_chain: List[Dict]
    outcome: str  # success / failure
    metadata: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Knowledge:
    """知识条目"""
    id: str
    content: str
    source: str
    category: str  # success_pattern / failure_pattern / optimization_tip
    confidence: float
    status: str  # draft / verified / production
    created_at: str = None
    verified_at: str = None
    access_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Reflection:
    """反思记录"""
    node_id: str
    node_type: str
    content: Dict
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class SharedMemory:
    """
    共享记忆
    
    使用 SQLite 实现持久化存储，支持：
    - 原始经验存储
    - 知识分级管理
    - 反思记录
    - 蜂群注册表
    """
    
    def __init__(self, db_path: str = "hivemind_memory.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with self._get_conn() as conn:
            # 经验表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_type TEXT,
                    decision_chain TEXT,  -- JSON
                    outcome TEXT,
                    metadata TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 知识表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT,
                    category TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # 反思表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    node_type TEXT,
                    content TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 蜂群注册表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS swarm_registry (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    parent_id TEXT,
                    capabilities TEXT,  -- JSON
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 消息日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT,
                    from_node TEXT,
                    to_node TEXT,
                    message_type TEXT,
                    payload TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exp_agent ON experiences(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exp_timestamp ON experiences(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_know_status ON knowledge(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_know_category ON knowledge(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_swarm_status ON swarm_registry(status)")
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    # ==================== 经验存储 ====================
    
    async def store_experience(self, experience: Experience) -> int:
        """存储经验"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO experiences 
                (agent_id, task_id, task_type, decision_chain, outcome, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                experience.agent_id,
                experience.task_id,
                experience.task_type,
                json.dumps(experience.decision_chain),
                experience.outcome,
                json.dumps(experience.metadata),
                experience.timestamp
            ))
            return cursor.lastrowid
    
    async def get_recent_experiences(self, limit: int = 100,
                                     agent_id: Optional[str] = None) -> List[Dict]:
        """获取近期经验"""
        with self._get_conn() as conn:
            if agent_id:
                cursor = conn.execute("""
                    SELECT * FROM experiences 
                    WHERE agent_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (agent_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM experiences 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    async def get_experience_stats(self) -> Dict:
        """获取经验统计"""
        with self._get_conn() as conn:
            # 总数
            cursor = conn.execute("SELECT COUNT(*) FROM experiences")
            total = cursor.fetchone()[0]
            
            # 成功率
            cursor = conn.execute("""
                SELECT outcome, COUNT(*) as count 
                FROM experiences 
                GROUP BY outcome
            """)
            by_outcome = {row['outcome']: row['count'] for row in cursor}
            
            # 按类型统计
            cursor = conn.execute("""
                SELECT task_type, COUNT(*) as count 
                FROM experiences 
                GROUP BY task_type
            """)
            by_type = {row['task_type']: row['count'] for row in cursor}
            
            return {
                'total': total,
                'by_outcome': by_outcome,
                'by_type': by_type
            }
    
    # ==================== 知识管理 ====================
    
    async def store_knowledge(self, knowledge: Knowledge) -> str:
        """存储知识"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge 
                (id, content, source, category, confidence, status, created_at, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                knowledge.id,
                knowledge.content,
                knowledge.source,
                knowledge.category,
                knowledge.confidence,
                knowledge.status,
                knowledge.created_at,
                knowledge.access_count
            ))
            return knowledge.id
    
    async def query_knowledge(self, 
                             query: Optional[str] = None,
                             category: Optional[str] = None,
                             status: str = "production",
                             min_confidence: float = 0.0,
                             limit: int = 10) -> List[Knowledge]:
        """查询知识"""
        with self._get_conn() as conn:
            sql = """
                SELECT * FROM knowledge 
                WHERE status = ? AND confidence >= ?
            """
            params = [status, min_confidence]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            if query:
                sql += " AND content LIKE ?"
                params.append(f"%{query}%")
            
            sql += " ORDER BY confidence DESC, access_count DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor:
                # 更新访问计数
                conn.execute("""
                    UPDATE knowledge 
                    SET access_count = access_count + 1 
                    WHERE id = ?
                """, (row['id'],))
                
                results.append(Knowledge(
                    id=row['id'],
                    content=row['content'],
                    source=row['source'],
                    category=row['category'],
                    confidence=row['confidence'],
                    status=row['status'],
                    created_at=row['created_at'],
                    verified_at=row['verified_at'],
                    access_count=row['access_count'] + 1
                ))
            
            return results
    
    async def promote_knowledge(self, knowledge_id: str, 
                                new_status: str) -> bool:
        """升级知识状态"""
        with self._get_conn() as conn:
            if new_status == "verified":
                conn.execute("""
                    UPDATE knowledge 
                    SET status = ?, verified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_status, knowledge_id))
            else:
                conn.execute("""
                    UPDATE knowledge 
                    SET status = ?
                    WHERE id = ?
                """, (new_status, knowledge_id))
            
            return conn.total_changes > 0
    
    async def get_knowledge_stats(self) -> Dict:
        """获取知识统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM knowledge 
                GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor}
            
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM knowledge 
                GROUP BY category
            """)
            by_category = {row['category']: row['count'] for row in cursor}
            
            return {
                'by_status': by_status,
                'by_category': by_category
            }
    
    # ==================== 反思记录 ====================
    
    async def store_reflection(self, node_id: str, content: Dict):
        """存储反思"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO reflections (node_id, node_type, content)
                VALUES (?, ?, ?)
            """, (
                node_id,
                content.get('node_type', 'unknown'),
                json.dumps(content)
            ))
    
    async def get_recent_reflections(self, node_id: Optional[str] = None,
                                     limit: int = 50) -> List[Dict]:
        """获取近期反思"""
        with self._get_conn() as conn:
            if node_id:
                cursor = conn.execute("""
                    SELECT * FROM reflections 
                    WHERE node_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (node_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM reflections 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== 蜂群注册表 ====================
    
    async def register_agent(self, agent_id: str, info: Dict):
        """注册 Agent"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO swarm_registry 
                (agent_id, agent_type, parent_id, capabilities, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                agent_id,
                info.get('agent_type'),
                info.get('parent_id'),
                json.dumps(info.get('capabilities', [])),
                info.get('status', 'active')
            ))
    
    async def update_agent_status(self, agent_id: str, status: str):
        """更新 Agent 状态"""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE swarm_registry 
                SET status = ?, last_active = CURRENT_TIMESTAMP
                WHERE agent_id = ?
            """, (status, agent_id))
    
    async def get_active_agents(self) -> List[Dict]:
        """获取活跃 Agents"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM swarm_registry 
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    async def get_swarm_stats(self) -> Dict:
        """获取蜂群统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT agent_type, status, COUNT(*) as count 
                FROM swarm_registry 
                GROUP BY agent_type, status
            """)
            
            stats = {}
            for row in cursor:
                t = row['agent_type']
                if t not in stats:
                    stats[t] = {}
                stats[t][row['status']] = row['count']
            
            return stats
    
    # ==================== 消息日志 ====================
    
    async def log_message(self, message_id: str, from_node: str,
                         to_node: Optional[str], message_type: str,
                         payload: Dict):
        """记录消息"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO message_log 
                (message_id, from_node, to_node, message_type, payload)
                VALUES (?, ?, ?, ?, ?)
            """, (
                message_id,
                from_node,
                to_node,
                message_type,
                json.dumps(payload)
            ))
    
    # ==================== 辅助方法 ====================
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """行转字典"""
        return {key: row[key] for key in row.keys()}
    
    async def get_health(self) -> Dict:
        """获取健康状态"""
        stats = {
            'experiences': await self.get_experience_stats(),
            'knowledge': await self.get_knowledge_stats(),
            'swarm': await self.get_swarm_stats()
        }
        
        return {
            'status': 'healthy',
            'db_path': str(self.db_path),
            'db_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0,
            'stats': stats
        }
