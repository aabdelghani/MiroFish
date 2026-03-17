"""
图谱实体读取与过滤服务
从图谱中读取节点，筛选出符合预定义实体类型的节点
支持 Zep Cloud 和 Graphiti 两种模式
Zep entity read and filter service.
Reads nodes from Zep graph and filters by predefined entity types.
"""

import time
from typing import Dict, Any, List, Optional, Set, Callable, TypeVar
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger
from .kg_adapter import get_knowledge_graph_adapter

logger = get_logger('mirofish.zep_entity_reader')

T = TypeVar('T')


@dataclass
class EntityNode:
    """Entity node data."""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }
    
    def get_entity_type(self) -> Optional[str]:
        """Get entity type (excluding default Entity/Node labels)."""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """Filtered entity set."""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    图谱实体读取与过滤服务

    主要功能：
    1. 从图谱读取所有节点
    2. 筛选出符合预定义实体类型的节点（Labels不只是Entity的节点）
    3. 获取每个实体的相关边和关联节点信息
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # 保留参数兼容性
        # 使用适配器
        self.kg = get_knowledge_graph_adapter()
    """Zep entity read and filter: fetch nodes, filter by predefined types, enrich with edges and related nodes."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY is not configured")
        
        self.client = Zep(api_key=self.api_key)
    
    def _call_with_retry(
        self, 
        func: Callable[[], T], 
        operation_name: str,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> T:
        """Call Zep API with retry. Args: func, operation_name, max_retries, initial_delay. Returns API result."""
        last_exception = None
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Zep {operation_name} attempt {attempt + 1} failed: {str(e)[:100]}, "
                        f"retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Zep {operation_name} failed after {max_retries} attempts: {str(e)}")
        
        raise last_exception
    
    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """Get all graph nodes (paginated). Args: graph_id. Returns list of nodes."""
        logger.info(f"Fetching all nodes for graph {graph_id}...")

        # 使用适配器获取节点
        nodes = self.kg.get_nodes(graph_id, limit=2000)

        nodes_data = []
        for node in nodes:
            if isinstance(node, dict):
                nodes_data.append({
                    "uuid": node.get('uuid_', '') or node.get('uuid', ''),
                    "name": node.get('name', ''),
                    "labels": node.get('labels', []),
                    "summary": node.get('summary', ''),
                    "attributes": node.get('attributes', {}),
                })
            else:
                nodes_data.append({
                    "uuid": getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                    "name": node.name or "",
                    "labels": node.labels or [],
                    "summary": node.summary or "",
                "attributes": node.attributes or {},
            })

        logger.info(f"Fetched {len(nodes_data)} nodes")
        return nodes_data

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """Get all graph edges (paginated). Args: graph_id. Returns list of edges."""
        logger.info(f"Fetching all edges for graph {graph_id}...")

        # 使用适配器获取边
        edges = self.kg.get_edges(graph_id, limit=2000)

        edges_data = []
        for edge in edges:
            if isinstance(edge, dict):
                edges_data.append({
                    "uuid": edge.get('uuid_', '') or edge.get('uuid', ''),
                    "name": edge.get('name', ''),
                    "fact": edge.get('fact', ''),
                    "source_node_uuid": edge.get('source_node_uuid', ''),
                    "target_node_uuid": edge.get('target_node_uuid', ''),
                    "attributes": edge.get('attributes', {}),
                })
            else:
                edges_data.append({
                    "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                    "name": edge.name or "",
                    "fact": edge.fact or "",
                    "source_node_uuid": edge.source_node_uuid,
                    "target_node_uuid": edge.target_node_uuid,
                    "attributes": edge.attributes or {},
                })

        logger.info(f"Fetched {len(edges_data)} edges")
        return edges_data
    
    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        """Get all edges for a node (with retry). Args: node_uuid. Returns list of edges."""
        try:
            # 使用重试机制调用图谱API
            edges = self._call_with_retry(
                func=lambda: self.kg.get_node_edges(node_uuid),
                operation_name=f"获取节点边(node={node_uuid[:8]}...)"
            edges = self._call_with_retry(
                func=lambda: self.client.graph.node.get_entity_edges(node_uuid=node_uuid),
                operation_name=f"get node edges (node={node_uuid[:8]}...)"
            )

            edges_data = []
            for edge in edges:
                if isinstance(edge, dict):
                    edges_data.append({
                        "uuid": edge.get('uuid_', '') or edge.get('uuid', ''),
                        "name": edge.get('name', ''),
                        "fact": edge.get('fact', ''),
                        "source_node_uuid": edge.get('source_node_uuid', ''),
                        "target_node_uuid": edge.get('target_node_uuid', ''),
                        "attributes": edge.get('attributes', {}),
                    })
                else:
                    edges_data.append({
                        "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                        "name": edge.name or "",
                        "fact": edge.fact or "",
                        "source_node_uuid": edge.source_node_uuid,
                        "target_node_uuid": edge.target_node_uuid,
                        "attributes": edge.attributes or {},
                    })

            return edges_data
        except Exception as e:
            logger.warning(f"Failed to get edges for node {node_uuid}: {str(e)}")
            return []
    
    def filter_defined_entities(
        self, 
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True
    ) -> FilteredEntities:
        """Filter nodes by predefined entity types (labels beyond Entity/Node). Returns FilteredEntities."""
        logger.info(f"Filtering entities for graph {graph_id}...")

        all_nodes = self.get_all_nodes(graph_id)
        total_count = len(all_nodes)
        all_edges = self.get_all_edges(graph_id) if enrich_with_edges else []
        node_map = {n["uuid"]: n for n in all_nodes}

        filtered_entities = []
        entity_types_found = set()
        
        for node in all_nodes:
            labels = node.get("labels", [])

            # 获取实体类型（优先从属性获取，其次从标签获取）
            entity_type = None
            if node.get("attributes"):
                entity_type = node["attributes"].get("entity_type")

            if not entity_type:
                # 筛选逻辑：Labels必须包含除"Entity"和"Node"之外的标签
                custom_labels = [l for l in labels if l not in ["Entity", "Node"]]
                if custom_labels:
                    entity_type = custom_labels[0]

            if not entity_type:
                # 没有实体类型，跳过
                continue

            # 如果指定了预定义类型，检查是否匹配
            
            custom_labels = [l for l in labels if l not in ["Entity", "Node"]]

            if not custom_labels:
                continue

            if defined_entity_types:
                if entity_type not in defined_entity_types:
                    continue

            entity_types_found.add(entity_type)

            entity = EntityNode(
                uuid=node["uuid"],
                name=node["name"],
                labels=labels,
                summary=node["summary"],
                attributes=node["attributes"],
            )

            if enrich_with_edges:
                related_edges = []
                related_node_uuids = set()
                
                for edge in all_edges:
                    if edge["source_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "outgoing",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "target_node_uuid": edge["target_node_uuid"],
                        })
                        related_node_uuids.add(edge["target_node_uuid"])
                    elif edge["target_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "incoming",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "source_node_uuid": edge["source_node_uuid"],
                        })
                        related_node_uuids.add(edge["source_node_uuid"])
                
                entity.related_edges = related_edges

                related_nodes = []
                for related_uuid in related_node_uuids:
                    if related_uuid in node_map:
                        related_node = node_map[related_uuid]
                        related_nodes.append({
                            "uuid": related_node["uuid"],
                            "name": related_node["name"],
                            "labels": related_node["labels"],
                            "summary": related_node.get("summary", ""),
                        })
                
                entity.related_nodes = related_nodes
            
            filtered_entities.append(entity)

        logger.info(f"Filter done: total nodes {total_count}, matched {len(filtered_entities)}, types: {entity_types_found}")
        
        return FilteredEntities(
            entities=filtered_entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(filtered_entities),
        )
    
    def get_entity_with_context(
        self, 
        graph_id: str, 
        entity_uuid: str
    ) -> Optional[EntityNode]:
        """
        获取单个实体及其完整上下文（边和关联节点，带重试机制）
        
        Args:
            graph_id: 图谱ID
            entity_uuid: 实体UUID

        Returns:
            EntityNode或None
        """
        """Get single entity with full context (edges and related nodes). Args: graph_id, entity_uuid. Returns EntityNode or None."""
        try:
            node = self._call_with_retry(
                func=lambda: self.kg.get_node(entity_uuid),
                operation_name=f"获取节点详情(uuid={entity_uuid[:8]}...)"
                func=lambda: self.client.graph.node.get(uuid_=entity_uuid),
                operation_name=f"get node (uuid={entity_uuid[:8]}...)"
            )

            if not node:
                return None

            # 获取节点的边
            edges = self.get_node_edges(entity_uuid)

            # 获取所有节点用于关联查找
            all_nodes = self.get_all_nodes(graph_id)
            node_map = {n["uuid"]: n for n in all_nodes}

            # 处理相关边和节点
            edges = self.get_node_edges(entity_uuid)
            all_nodes = self.get_all_nodes(graph_id)
            node_map = {n["uuid"]: n for n in all_nodes}
            related_edges = []
            related_node_uuids = set()
            
            for edge in edges:
                if edge["source_node_uuid"] == entity_uuid:
                    related_edges.append({
                        "direction": "outgoing",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "target_node_uuid": edge["target_node_uuid"],
                    })
                    related_node_uuids.add(edge["target_node_uuid"])
                else:
                    related_edges.append({
                        "direction": "incoming",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "source_node_uuid": edge["source_node_uuid"],
                    })
                    related_node_uuids.add(edge["source_node_uuid"])

            related_nodes = []
            for related_uuid in related_node_uuids:
                if related_uuid in node_map:
                    related_node = node_map[related_uuid]
                    related_nodes.append({
                        "uuid": related_node["uuid"],
                        "name": related_node["name"],
                        "labels": related_node["labels"],
                        "summary": related_node.get("summary", ""),
                    })
            
            return EntityNode(
                uuid=getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {},
                related_edges=related_edges,
                related_nodes=related_nodes,
            )
            
        except Exception as e:
            logger.error(f"Get entity {entity_uuid} failed: {str(e)}")
            return None
    
    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        """Get all entities of given type. Args: graph_id, entity_type, enrich_with_edges. Returns list of EntityNode."""
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges
        )
        return result.entities


