"""
向量存储后端包装器 - 支持多种向量数据库的统一接口

提供 Chroma、Qdrant、PgVector 等多种向量存储后端的统一包装，
实现混合检索（向量相似度 + 关键词匹配）。

Author: Qwen3.6-Plus
Version: 1.0.0-beta0.1
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


def _lazy_numpy():
    """延迟导入 numpy，如果不可用则返回 None"""
    try:
        import numpy as np
        return np
    except ImportError:
        return None


def _cosine_similarity_python(v1: List[float], v2: List[float]) -> float:
    """纯 Python 实现余弦相似度"""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 > 0 and norm2 > 0:
        return dot_product / (norm1 * norm2)
    return 0.0


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算余弦相似度（优先使用 numpy，否则使用纯 Python）"""
    np = _lazy_numpy()
    if np is not None:
        v1_np = np.array(v1)
        v2_np = np.array(v2)
        norm1 = np.linalg.norm(v1_np)
        norm2 = np.linalg.norm(v2_np)
        if norm1 > 0 and norm2 > 0:
            return float(np.dot(v1_np, v2_np) / (norm1 * norm2))
        return 0.0
    return _cosine_similarity_python(v1, v2)


class VectorBackendType(Enum):
    """向量存储后端类型"""
    IN_MEMORY = "in_memory"
    CHROMA = "chroma"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"


@dataclass
class VectorRecord:
    """向量记录"""
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    document: str = ""


@dataclass
class SearchResult:
    """向量检索结果"""
    id: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    document: str = ""


class VectorStoreBackend:
    """
    向量存储后端包装器 - 统一接口支持多种向量数据库
    
    提供统一的向量存储和检索接口，支持：
    - 内存向量索引（轻量级，适合测试和小规模）
    - Chroma 向量数据库（本地/服务器）
    - Qdrant 向量数据库（高性能）
    - PgVector PostgreSQL 扩展（关系数据库集成）
    """

    def __init__(
        self,
        backend_type: VectorBackendType = VectorBackendType.IN_MEMORY,
        collection_name: str = "memory_vectors",
        embedding_dim: int = 1536,
        connection_params: Optional[Dict[str, Any]] = None,
        hybrid_search: bool = True,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ):
        """
        初始化向量存储后端
        
        Args:
            backend_type: 后端类型
            collection_name: 集合/索引名称
            embedding_dim: 向量维度
            connection_params: 连接参数（不同后端需要不同参数）
            hybrid_search: 是否启用混合搜索
            keyword_weight: 关键词搜索权重
            vector_weight: 向量搜索权重
        """
        self.backend_type = backend_type
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.connection_params = connection_params or {}
        self.hybrid_search = hybrid_search
        self.keyword_weight = keyword_weight
        self.vector_weight = vector_weight
        
        # 内部状态
        self._initialized = False
        self._client = None
        self._id_to_vector: Dict[str, List[float]] = {}
        self._id_to_metadata: Dict[str, Dict[str, Any]] = {}
        self._id_to_document: Dict[str, str] = {}
        
        # 初始化后端
        self._initialize_backend()
    
    def _initialize_backend(self):
        """初始化选定的后端"""
        try:
            if self.backend_type == VectorBackendType.IN_MEMORY:
                self._init_in_memory()
            elif self.backend_type == VectorBackendType.CHROMA:
                self._init_chroma()
            elif self.backend_type == VectorBackendType.QDRANT:
                self._init_qdrant()
            elif self.backend_type == VectorBackendType.PGVECTOR:
                self._init_pgvector()
            else:
                raise ValueError(f"不支持的后端类型: {self.backend_type}")
            
            self._initialized = True
        except ImportError as e:
            print(f"警告: 缺少 {self.backend_type.value} 所需的依赖库: {e}")
            print("回退到内存模式")
            self.backend_type = VectorBackendType.IN_MEMORY
            self._init_in_memory()
            self._initialized = True
    
    def _init_in_memory(self):
        """初始化内存向量索引"""
        self._id_to_vector = {}
        self._id_to_metadata = {}
        self._id_to_document = {}
    
    def _init_chroma(self):
        """初始化 Chroma 向量数据库"""
        import chromadb
        from chromadb.config import Settings
        
        client_settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.connection_params.get("persist_directory", "./chroma_db"),
        )
        
        if self.connection_params.get("host"):
            self._client = chromadb.HttpClient(
                host=self.connection_params.get("host", "localhost"),
                port=self.connection_params.get("port", 8000),
            )
        else:
            self._client = chromadb.Client(client_settings)
        
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.connection_params.get("distance_metric", "cosine")}
        )
    
    def _init_qdrant(self):
        """初始化 Qdrant 向量数据库"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        host = self.connection_params.get("host", "localhost")
        port = self.connection_params.get("port", 6333)
        
        self._client = QdrantClient(host=host, port=port)
        
        # 创建集合（如果不存在）
        collections = [c.name for c in self._client.get_collections().collections]
        if self.collection_name not in collections:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
    
    def _init_pgvector(self):
        """初始化 PgVector PostgreSQL 扩展"""
        import psycopg2
        from psycopg2.extras import execute_values
        
        self._pg_conn = psycopg2.connect(
            host=self.connection_params.get("host", "localhost"),
            port=self.connection_params.get("port", 5432),
            dbname=self.connection_params.get("dbname", "memory_db"),
            user=self.connection_params.get("user", "postgres"),
            password=self.connection_params.get("password", ""),
        )
        
        # 启用 pgvector 扩展
        with self._pg_conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.collection_name} (
                    id TEXT PRIMARY KEY,
                    vector VECTOR({self.embedding_dim}),
                    metadata JSONB,
                    document TEXT
                );
            """)
            self._pg_conn.commit()
    
    async def add_vectors(
        self,
        vectors: List[VectorRecord],
        batch_size: int = 100
    ) -> int:
        """
        批量添加向量
        
        Args:
            vectors: 向量记录列表
            batch_size: 批次大小
            
        Returns:
            成功添加的向量数量
        """
        if not self._initialized:
            raise RuntimeError("后端未初始化")
        
        added_count = 0
        
        if self.backend_type == VectorBackendType.IN_MEMORY:
            added_count = await self._add_in_memory(vectors)
        elif self.backend_type == VectorBackendType.CHROMA:
            added_count = await self._add_chroma(vectors, batch_size)
        elif self.backend_type == VectorBackendType.QDRANT:
            added_count = await self._add_qdrant(vectors, batch_size)
        elif self.backend_type == VectorBackendType.PGVECTOR:
            added_count = await self._add_pgvector(vectors, batch_size)
        
        return added_count
    
    async def _add_in_memory(self, vectors: List[VectorRecord]) -> int:
        """内存模式添加向量"""
        for vec_record in vectors:
            self._id_to_vector[vec_record.id] = vec_record.vector
            self._id_to_metadata[vec_record.id] = vec_record.metadata
            self._id_to_document[vec_record.id] = vec_record.document
        return len(vectors)
    
    async def _add_chroma(self, vectors: List[VectorRecord], batch_size: int) -> int:
        """Chroma 模式添加向量"""
        ids = [v.id for v in vectors]
        embeddings = [v.vector for v in vectors]
        metadatas = [v.metadata for v in vectors]
        documents = [v.document for v in vectors]
        
        # 分批添加
        for i in range(0, len(vectors), batch_size):
            batch_end = min(i + batch_size, len(vectors))
            self._collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                documents=documents[i:batch_end]
            )
        
        return len(vectors)
    
    async def _add_qdrant(self, vectors: List[VectorRecord], batch_size: int) -> int:
        """Qdrant 模式添加向量"""
        from qdrant_client.models import PointStruct
        
        points = [
            PointStruct(
                id=v.id,
                vector=v.vector,
                payload={**v.metadata, "document": v.document}
            )
            for v in vectors
        ]
        
        # 分批添加
        for i in range(0, len(points), batch_size):
            batch_end = min(i + batch_size, len(points))
            self._client.upsert(
                collection_name=self.collection_name,
                points=points[i:batch_end]
            )
        
        return len(vectors)
    
    async def _add_pgvector(self, vectors: List[VectorRecord], batch_size: int) -> int:
        """PgVector 模式添加向量"""
        from psycopg2.extras import execute_values
        
        with self._pg_conn.cursor() as cur:
            # 使用 JSON 格式化向量
            for vec_record in vectors:
                vector_str = f"[{','.join(map(str, vec_record.vector))}]"
                cur.execute(
                    f"INSERT INTO {self.collection_name} (id, vector, metadata, document) "
                    f"VALUES (%s, %s::vector, %s::jsonb, %s) "
                    f"ON CONFLICT (id) DO UPDATE SET vector=EXCLUDED.vector, metadata=EXCLUDED.metadata, document=EXCLUDED.document;",
                    (vec_record.id, vector_str, str(vec_record.metadata), vec_record.document)
                )
            self._pg_conn.commit()
        
        return len(vectors)
    
    async def search(
        self,
        query_vector: List[float],
        query_text: Optional[str] = None,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索相似向量（支持混合搜索）
        
        Args:
            query_vector: 查询向量
            query_text: 查询文本（用于混合搜索）
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            搜索结果列表（按相关性排序）
        """
        if not self._initialized:
            raise RuntimeError("后端未初始化")
        
        vector_results = []
        keyword_results = []
        
        # 向量搜索
        if self.backend_type == VectorBackendType.IN_MEMORY:
            vector_results = self._search_in_memory(query_vector, top_k, filter_metadata)
        elif self.backend_type == VectorBackendType.CHROMA:
            vector_results = self._search_chroma(query_vector, top_k, filter_metadata)
        elif self.backend_type == VectorBackendType.QDRANT:
            vector_results = self._search_qdrant(query_vector, top_k, filter_metadata)
        elif self.backend_type == VectorBackendType.PGVECTOR:
            vector_results = self._search_pgvector(query_vector, top_k, filter_metadata)
        
        # 混合搜索：结合关键词匹配
        if self.hybrid_search and query_text:
            keyword_results = self._keyword_search(query_text, top_k, filter_metadata)
            return self._merge_results(vector_results, keyword_results, top_k)
        
        return vector_results[:top_k]
    
    def _search_in_memory(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """内存模式向量搜索"""
        scores = []
        for vec_id, vector in self._id_to_vector.items():
            # 应用元数据过滤
            if filter_metadata and not self._matches_filter(vec_id, filter_metadata):
                continue
            
            similarity = _cosine_similarity(query_vector, vector)
            
            scores.append(SearchResult(
                id=vec_id,
                score=float(similarity),
                metadata=self._id_to_metadata.get(vec_id, {}),
                document=self._id_to_document.get(vec_id, "")
            ))
        
        # 按分数排序
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k * 2]  # 返回更多结果用于混合搜索合并
    
    def _search_chroma(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Chroma 模式向量搜索"""
        where_filter = None
        if filter_metadata:
            # 构建 Chroma where 条件
            where_filter = {"$and": [
                {"$eq": [key, value]} for key, value in filter_metadata.items()
            ]}
        
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k * 2,
            where=where_filter,
            include=["distances", "metadatas", "documents"]
        )
        
        search_results = []
        for i, (vec_id, distance, metadata, document) in enumerate(zip(
            results["ids"][0],
            results["distances"][0],
            results["metadatas"][0],
            results["documents"][0]
        )):
            # Chroma 返回距离，转换为相似度
            similarity = 1.0 - distance
            search_results.append(SearchResult(
                id=vec_id,
                score=similarity,
                metadata=metadata or {},
                document=document or ""
            ))
        
        return search_results
    
    def _search_qdrant(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Qdrant 模式向量搜索"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        qdrant_filter = None
        if filter_metadata:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in filter_metadata.items()
                ]
            )
        
        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k * 2
        )
        
        return [
            SearchResult(
                id=str(hit.id),
                score=hit.score,
                metadata=hit.payload or {},
                document=hit.payload.get("document", "") if hit.payload else ""
            )
            for hit in results
        ]
    
    def _search_pgvector(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """PgVector 模式向量搜索"""
        vector_str = f"[{','.join(map(str, query_vector))}]"
        
        where_clause = ""
        where_params = []
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(f"metadata->>'{key}' = %s")
                where_params.append(str(value))
            where_clause = "WHERE " + " AND ".join(conditions)
        
        with self._pg_conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, vector, metadata, document,
                       1 - (vector <=> %s::vector) AS similarity
                FROM {self.collection_name}
                {where_clause}
                ORDER BY similarity DESC
                LIMIT %s;
            """, [vector_str] + where_params + [top_k * 2])
            
            results = cur.fetchall()
        
        return [
            SearchResult(
                id=row[0],
                score=float(row[4]),
                metadata=row[2] or {},
                document=row[3] or ""
            )
            for row in results
        ]
    
    def _keyword_search(
        self,
        query_text: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """关键词搜索"""
        # 简单实现：TF-IDF 风格的关键词匹配
        query_terms = set(query_text.lower().split())
        
        scores = []
        for vec_id, document in self._id_to_document.items():
            if filter_metadata and not self._matches_filter(vec_id, filter_metadata):
                continue
            
            if not document:
                continue
            
            # 计算关键词匹配度
            doc_terms = set(document.lower().split())
            matching_terms = query_terms.intersection(doc_terms)
            
            if matching_terms:
                # 简单匹配分数
                score = len(matching_terms) / len(query_terms)
                scores.append(SearchResult(
                    id=vec_id,
                    score=score,
                    metadata=self._id_to_metadata.get(vec_id, {}),
                    document=document
                ))
        
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k * 2]
    
    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """合并向量和关键词搜索结果"""
        # 创建结果映射
        all_results: Dict[str, SearchResult] = {}
        
        # 添加向量结果
        for result in vector_results:
            all_results[result.id] = SearchResult(
                id=result.id,
                score=result.score * self.vector_weight,
                metadata=result.metadata,
                document=result.document
            )
        
        # 合并关键词结果
        for result in keyword_results:
            if result.id in all_results:
                # 已存在，加权平均
                existing = all_results[result.id]
                existing.score = (
                    existing.score + result.score * self.keyword_weight
                )
            else:
                # 新结果
                all_results[result.id] = SearchResult(
                    id=result.id,
                    score=result.score * self.keyword_weight,
                    metadata=result.metadata,
                    document=result.document
                )
        
        # 排序并返回 top_k
        merged = list(all_results.values())
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:top_k]
    
    def _matches_filter(
        self,
        vec_id: str,
        filter_metadata: Dict[str, Any]
    ) -> bool:
        """检查向量是否匹配过滤条件"""
        metadata = self._id_to_metadata.get(vec_id, {})
        for key, value in filter_metadata.items():
            if metadata.get(key) != value:
                return False
        return True
    
    async def delete_vectors(self, ids: List[str]) -> int:
        """
        删除向量
        
        Args:
            ids: 要删除的向量 ID 列表
            
        Returns:
            成功删除的向量数量
        """
        if not self._initialized:
            raise RuntimeError("后端未初始化")
        
        deleted_count = 0
        
        if self.backend_type == VectorBackendType.IN_MEMORY:
            deleted_count = self._delete_in_memory(ids)
        elif self.backend_type == VectorBackendType.CHROMA:
            deleted_count = self._delete_chroma(ids)
        elif self.backend_type == VectorBackendType.QDRANT:
            deleted_count = self._delete_qdrant(ids)
        elif self.backend_type == VectorBackendType.PGVECTOR:
            deleted_count = self._delete_pgvector(ids)
        
        return deleted_count
    
    def _delete_in_memory(self, ids: List[str]) -> int:
        """内存模式删除向量"""
        deleted = 0
        for vec_id in ids:
            if vec_id in self._id_to_vector:
                del self._id_to_vector[vec_id]
                del self._id_to_metadata[vec_id]
                del self._id_to_document[vec_id]
                deleted += 1
        return deleted
    
    def _delete_chroma(self, ids: List[str]) -> int:
        """Chroma 模式删除向量"""
        self._collection.delete(ids=ids)
        return len(ids)
    
    def _delete_qdrant(self, ids: List[str]) -> int:
        """Qdrant 模式删除向量"""
        self._client.delete(
            collection_name=self.collection_name,
            points_selector={"points": ids}
        )
        return len(ids)
    
    def _delete_pgvector(self, ids: List[str]) -> int:
        """PgVector 模式删除向量"""
        with self._pg_conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"DELETE FROM {self.collection_name} WHERE id IN ({placeholders});",
                ids
            )
            self._pg_conn.commit()
            return cur.rowcount
    
    async def get_vector_count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        获取向量数量
        
        Args:
            filter_metadata: 元数据过滤条件
            
        Returns:
            向量数量
        """
        if self.backend_type == VectorBackendType.IN_MEMORY:
            if filter_metadata:
                return sum(
                    1 for vec_id in self._id_to_vector
                    if self._matches_filter(vec_id, filter_metadata)
                )
            return len(self._id_to_vector)
        
        elif self.backend_type == VectorBackendType.CHROMA:
            where_filter = None
            if filter_metadata:
                where_filter = {"$and": [
                    {"$eq": [key, value]} for key, value in filter_metadata.items()
                ]}
            return self._collection.count(where=where_filter)
        
        elif self.backend_type == VectorBackendType.QDRANT:
            return self._client.count(
                collection_name=self.collection_name
            ).count
        
        elif self.backend_type == VectorBackendType.PGVECTOR:
            with self._pg_conn.cursor() as cur:
                if filter_metadata:
                    conditions = " AND ".join([
                        f"metadata->>'{key}' = '{value}'"
                        for key, value in filter_metadata.items()
                    ])
                    cur.execute(f"SELECT COUNT(*) FROM {self.collection_name} WHERE {conditions};")
                else:
                    cur.execute(f"SELECT COUNT(*) FROM {self.collection_name};")
                return cur.fetchone()[0]
        
        return 0
    
    async def clear(self):
        """清空所有向量"""
        if self.backend_type == VectorBackendType.IN_MEMORY:
            self._id_to_vector.clear()
            self._id_to_metadata.clear()
            self._id_to_document.clear()
        elif self.backend_type == VectorBackendType.CHROMA:
            self._client.delete_collection(self.collection_name)
            self._init_chroma()
        elif self.backend_type == VectorBackendType.QDRANT:
            self._client.delete_collection(self.collection_name)
            self._init_qdrant()
        elif self.backend_type == VectorBackendType.PGVECTOR:
            with self._pg_conn.cursor() as cur:
                cur.execute(f"DELETE FROM {self.collection_name};")
                self._pg_conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取后端统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "backend_type": self.backend_type.value,
            "collection_name": self.collection_name,
            "embedding_dim": self.embedding_dim,
            "hybrid_search": self.hybrid_search,
            "initialized": self._initialized,
        }
        
        if self.backend_type == VectorBackendType.IN_MEMORY:
            stats["vector_count"] = len(self._id_to_vector)
        
        return stats
    
    async def close(self):
        """关闭后端连接"""
        if self.backend_type == VectorBackendType.PGVECTOR and hasattr(self, '_pg_conn'):
            self._pg_conn.close()
        elif self.backend_type == VectorBackendType.CHROMA and hasattr(self, '_client'):
            # Chroma 不需要显式关闭
            pass
        elif self.backend_type == VectorBackendType.QDRANT and hasattr(self, '_client'):
            # Qdrant 不需要显式关闭
            pass
