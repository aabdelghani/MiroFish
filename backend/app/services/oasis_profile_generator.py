"""
OASIS Agent Profile生成器
将图谱中的实体转换为OASIS模拟平台所需的Agent Profile格式
支持 Zep Cloud 和 Graphiti 两种模式

优化改进：
1. 调用图谱检索功能二次丰富节点信息
2. 优化提示词生成非常详细的人设
3. 区分个人实体和抽象群体实体
OASIS Agent Profile generator: map Zep graph entities to OASIS simulation agent profiles.
Uses Zep retrieval to enrich context, detailed LLM persona generation, and distinguishes
individual vs group/organization entities.
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import _is_minimax, _clamp_temperature, _inject_json_instruction, parse_json_from_response
from .zep_entity_reader import EntityNode, ZepEntityReader
from .kg_adapter import get_knowledge_graph_adapter
from ..utils.error_messages import get_error_message
from .zep_entity_reader import EntityNode

logger = get_logger('mirofish.oasis_profile')


def _coerce_to_str(value: Any) -> str:
    """Coerce a value to a plain string.

    Handles dict, list, and other non-string types that may be returned
    by LLM JSON parsing.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ('text', 'value', 'description', 'content', 'summary', 'name'):
            if key in value and isinstance(value[key], str):
                return value[key]
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        str_items = [_coerce_to_str(item) for item in value]
        return ', '.join(str_items)
    return str(value)


def _coerce_to_str_list(value: Any) -> List[str]:
    """Coerce a value to a list of strings.

    Handles nested structures that may be returned by LLM JSON parsing.
    """
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(_coerce_to_str(item))
            else:
                result.append(str(item))
        return result
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [_coerce_to_str(value)]
    return []
# 语言指令（根据 locale 动态追加到 LLM 提示词）
LANGUAGE_INSTRUCTIONS = {
    'zh': "\n\n【语言要求】所有输出必须使用中文。",
    'en': "\n\n【Language requirement】All output MUST be in English.",
    'ko': "\n\n【언어 요구사항】모든 출력은 반드시 한국어로 작성해야 합니다.",
}

# 各语言对提示词中"使用中文"的替换映射
_LANG_LABEL = {
    'zh': '中文',
    'en': 'English',
    'ko': '한국어',
}


@dataclass
class OasisAgentProfile:
    """OASIS agent profile data structure."""
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    karma: int = 1000
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def __post_init__(self):
        """Normalize field types to guard against structured LLM outputs
        (e.g. dict/list instead of plain strings)."""
        self.bio = _coerce_to_str(self.bio)
        self.persona = _coerce_to_str(self.persona)
        self.country = _coerce_to_str(self.country) if self.country is not None else None
        self.profession = _coerce_to_str(self.profession) if self.profession is not None else None
        self.gender = _coerce_to_str(self.gender) if self.gender is not None else None
        self.interested_topics = _coerce_to_str_list(self.interested_topics)
    
    def to_reddit_format(self) -> Dict[str, Any]:
        """Convert to Reddit platform format (OASIS expects 'username')."""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_twitter_format(self) -> Dict[str, Any]:
        """Convert to Twitter platform format (OASIS expects 'username')."""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to full dict."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }


class OasisProfileGenerator:
    """
    OASIS profile generator: map Zep entities to agent profiles with Zep retrieval
    for richer context, detailed persona generation, and individual vs group handling.
    """
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]
    COUNTRIES = [
        "China", "US", "UK", "Japan", "Germany", "France",
        "Canada", "Australia", "Brazil", "India", "South Korea"
    ]
    INDIVIDUAL_ENTITY_TYPES = [
        "student", "alumni", "professor", "person", "publicfigure",
        "expert", "faculty", "official", "journalist", "activist"
    ]
    GROUP_ENTITY_TYPES = [
        "university", "governmentagency", "organization", "ngo", 
        "mediaoutlet", "company", "institution", "group", "community"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None,
        language: str = "zh"
    ):
        self.language = language
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")
            raise ValueError("LLM_API_KEY 未配置")

        # OpenRouter兼容：自动检测并添加推荐的额外请求头
        extra_kwargs = {}
        if self.base_url and 'openrouter.ai' in self.base_url:
            extra_kwargs['default_headers'] = {
                'HTTP-Referer': Config.OPENROUTER_REFERER,
                'X-Title': Config.OPENROUTER_TITLE,
            }

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            **extra_kwargs
        )

        # 图谱客户端用于检索丰富上下文
        self.graph_id = graph_id
        # 使用适配器
        try:
            self.kg = get_knowledge_graph_adapter()
        except Exception as e:
            logger.warning(f"图谱客户端初始化失败: {e}")
            self.kg = None
    
        
        self.zep_api_key = zep_api_key or Config.ZEP_API_KEY
        self.zep_client = None
        self.graph_id = graph_id
        if self.zep_api_key:
            try:
                self.zep_client = Zep(api_key=self.zep_api_key)
            except Exception as e:
                logger.warning(f"Zep client init failed: {e}")

    def generate_profile_from_entity(
        self,
        entity: EntityNode,
        user_id: int,
        use_llm: bool = True,
        locale: str = 'zh'
    ) -> OasisAgentProfile:
        """Generate OASIS agent profile from a Zep entity."""
        entity_type = entity.get_entity_type() or "Entity"
        name = entity.name
        user_name = self._generate_username(name)
        context = self._build_entity_context(entity)
        """
        从Zep实体生成OASIS Agent Profile

        Args:
            entity: Zep实体节点
            user_id: 用户ID（用于OASIS）
            use_llm: 是否使用LLM生成详细人设
            locale: 语言偏好 ('zh', 'en', 'ko')

        Returns:
            OasisAgentProfile
        """
        entity_type = entity.get_entity_type() or "Entity"

        # 基础信息
        name = entity.name
        user_name = self._generate_username(name)

        # 构建上下文信息
        context = self._build_entity_context(entity)

        if use_llm:
            profile_data = self._generate_profile_with_llm(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context,
                locale=locale
            )
        else:
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )
        
        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )
    
    def _generate_username(self, name: str) -> str:
        """Generate a username from entity name (sanitize + random suffix)."""
        username = name.lower().replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')
        suffix = random.randint(100, 999)
        return f"{username}_{suffix}"
    
    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """
        使用Zep图谱混合搜索功能获取实体相关的丰富信息

        Zep没有内置混合搜索接口，需要分别搜索edges和nodes然后合并结果。
        使用并行请求同时搜索，提高效率。

        Args:
            entity: 实体节点对象

        Returns:
            包含facts, node_summaries, context的字典
        """
        import concurrent.futures

        if not self.kg:
            return {"facts": [], "node_summaries": [], "context": ""}

        entity_name = entity.name

        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }

        # 必须有graph_id才能进行搜索
        Fetch rich context for an entity via Zep graph search (edges + nodes in parallel).
        Returns dict with facts, node_summaries, context.
        """
        import concurrent.futures
        if not self.zep_client:
            return {"facts": [], "node_summaries": [], "context": ""}
        entity_name = entity.name
        results = {"facts": [], "node_summaries": [], "context": ""}
        if not self.graph_id:
            logger.debug("Skipping Zep retrieval: graph_id not set")
            logger.debug("跳过Zep检索：未设置graph_id")
            return results

        # 使用实体名称作为查询，而不是复杂的中文描述
        # Zep Cloud search 对中文支持有限，尝试直接用实体名搜索
        comprehensive_query = entity_name

        comprehensive_query = f"All information, activities, events, relationships and background about {entity_name}"
        
        def search_edges():
            """Search edges (facts/relations) with retry."""
            max_retries = 3
            delay = 2.0

            for attempt in range(max_retries):
                try:
                    result = self.kg.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                    return result
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep edge search attempt {attempt + 1} failed: {str(e)[:80]}, retrying...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep edge search failed after {max_retries} attempts: {e}")
            return None

        def search_nodes():
            """Search nodes (entity summaries) with retry."""
            max_retries = 3
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.kg.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep node search attempt {attempt + 1} failed: {str(e)[:80]}, retrying...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep node search failed after {max_retries} attempts: {e}")
            return None
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                edge_future = executor.submit(search_edges)
                node_future = executor.submit(search_nodes)
                edge_result = edge_future.result(timeout=30)
                node_result = node_future.result(timeout=30)
            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)
            
            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"Related entity: {node.name}")
            results["node_summaries"] = list(all_summaries)
            context_parts = []
            if results["facts"]:
                context_parts.append("Facts:\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append("Related entities:\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)
            logger.info(f"Zep hybrid search done: {entity_name}, {len(results['facts'])} facts, {len(results['node_summaries'])} nodes")
            
            logger.info(f"Zep hybrid search complete: {entity_name}, got {len(results['facts'])} facts, {len(results['node_summaries'])} related nodes")
            
        except concurrent.futures.TimeoutError:
            logger.warning(f"Zep retrieval timeout ({entity_name})")
        except Exception as e:
            logger.warning(f"Zep retrieval failed ({entity_name}): {e}")
        
        return results
    
    def _build_entity_context(self, entity: EntityNode) -> str:
        """Build full context: entity attributes, related edges/nodes, and Zep retrieval results."""
        context_parts = []
        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### Entity attributes\n" + "\n".join(attrs))
        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")
                
                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> (related entity)")
                    else:
                        relationships.append(f"- (related entity) --[{edge_name}]--> {entity.name}")
            if relationships:
                context_parts.append("### Related facts and relationships\n" + "\n".join(relationships))
        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                
                # 过滤掉默认标签
                custom_labels = [label for label in node_labels if label not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""
                
                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")
            
            if related_info:
                context_parts.append("### Related entity info\n" + "\n".join(related_info))
        zep_results = self._search_zep_for_entity(entity)
        if zep_results.get("facts"):
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Facts from Zep retrieval\n" + "\n".join(f"- {f}" for f in new_facts[:15]))
        if zep_results.get("node_summaries"):
            context_parts.append("### Related nodes from Zep retrieval\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))
        
        return "\n\n".join(context_parts)
    
    def _is_individual_entity(self, entity_type: str) -> bool:
        """Whether this entity type is an individual (vs group/org)."""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES

    def _is_group_entity(self, entity_type: str) -> bool:
        """Whether this entity type is a group/organization."""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES

    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        locale: str = 'zh'
    ) -> Dict[str, Any]:
        """Generate detailed persona via LLM; individual vs group/org prompts."""
        """
        使用LLM生成非常详细的人设

        根据实体类型区分：
        - 个人实体：生成具体的人物设定
        - 群体/机构实体：生成代表性账号设定
        """

        is_individual = self._is_individual_entity(entity_type)

        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context, locale
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context, locale
            )

        max_attempts = 3
        last_error = None
        for attempt in range(max_attempts):
            try:
                kwargs = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt(is_individual)},

        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual, locale)},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7 - (attempt * 0.1)  # 每次重试降低温度
                    # 不设置max_tokens，让LLM自由发挥
                }
                
                # 尝试使用 response_format，如果不支持则回退
                try:
                    kwargs["response_format"] = {"type": "json_object"}
                    response = self.client.chat.completions.create(**kwargs)
                except Exception as api_error:
                    error_str = str(api_error).lower()
                    if ("response_format" in error_str or 
                        "json_object" in error_str or
                        "unsupported" in error_str or
                        "400" in error_str or
                        "500" in error_str):
                        # 移除 response_format 后重试
                        kwargs.pop("response_format", None)
                        response = self.client.chat.completions.create(**kwargs)
                    else:
                        raise
                
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)
                )
                content = response.choices[0].message.content
        use_minimax = _is_minimax(self.model_name, self.base_url)

        for attempt in range(max_attempts):
            try:
                import re as _re
                temperature = _clamp_temperature(0.7 - (attempt * 0.1), self.model_name, self.base_url)
                messages = [
                    {"role": "system", "content": self._get_system_prompt(is_individual)},
                    {"role": "user", "content": prompt}
                ]

                kwargs = {
                    "model": self.model_name,
                    "messages": _inject_json_instruction(messages) if use_minimax else messages,
                    "temperature": temperature,
                    # 不设置max_tokens，让LLM自由发挥
                }
                if not use_minimax:
                    kwargs["response_format"] = {"type": "json_object"}

                response = self.client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content
                # 移除 <think> 标签
                content = _re.sub(r'<think>[\s\S]*?</think>', '', content).strip()

                # 检查是否被截断（finish_reason不是'stop'）
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"LLM output truncated (attempt {attempt+1}), fixing...")
                    content = self._fix_truncated_json(content)
                try:
                    result = json.loads(content)
                    
                    # Normalize types from LLM output
                    for str_field in ('bio', 'persona', 'country', 'profession'):
                        if str_field in result and result[str_field] is not None:
                            result[str_field] = _coerce_to_str(result[str_field])
                    if 'interested_topics' in result:
                        result['interested_topics'] = _coerce_to_str_list(
                            result['interested_topics']
                        )
                    

                # 尝试解析JSON
                try:
                    result = parse_json_from_response(content)

                    # 验证必需字段
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name} is a {entity_type}."
                        result["persona"] = entity_summary or f"A {entity_type} named {entity_name}." if self.language == 'en' else f"{entity_name}是一个{entity_type}。"
                    
                    return result
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON parse failed (attempt {attempt+1}): {str(je)[:80]}")
                        result["persona"] = entity_summary or f"{entity_name}是一个{entity_type}。"

                    return result

                except (json.JSONDecodeError, ValueError) as je:
                    logger.warning(f"JSON解析失败 (attempt {attempt+1}): {str(je)[:80]}")

                    # 尝试修复JSON
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result
                    
                    last_error = je
                    
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(1 * (attempt + 1))
        logger.warning(f"LLM persona generation failed after {max_attempts} attempts: {last_error}, using rule-based")
        return self._generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )
    
    def _fix_truncated_json(self, content: str) -> str:
        """Try to close truncated JSON (e.g. cut by max_tokens)."""
        import re
        """修复被截断的JSON（输出被max_tokens限制截断）"""
        
        # 如果JSON被截断，尝试闭合它
        content = content.strip()
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        if content and content[-1] not in '",}]':
            content += '"'
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_json(self, content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
        """Try to repair malformed JSON and extract bio/persona."""
        import re
        content = self._fix_truncated_json(content)
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            def fix_string_newlines(match):
                s = match.group(0)
                s = s.replace('\n', ' ').replace('\r', ' ')
                s = re.sub(r'\s+', ' ', s)
                return s
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)
            try:
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except json.JSONDecodeError:
                # 5. 如果还是失败，尝试更激进的修复
                try:
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                    json_str = re.sub(r'\s+', ' ', json_str)
                    result = json.loads(json_str)
                    result["_fixed"] = True
                    return result
                except Exception:
                except:  # noqa: E722
                    pass
        bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
        persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)
        bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
        persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name} is a {entity_type}.")
        persona = persona_match.group(1) if persona_match else (entity_summary or (f"A {entity_type} named {entity_name}." if self.language == 'en' else f"{entity_name}是一个{entity_type}。"))
        
        # 如果提取到了有意义的内容，标记为已修复
        if bio_match or persona_match:
            logger.info("Extracted partial info from malformed JSON")
            return {"bio": bio, "persona": persona, "_fixed": True}
        logger.warning("JSON repair failed, returning fallback structure")
            logger.info("Extracted partial info from broken JSON")
            return {
                "bio": bio,
                "persona": persona,
                "_fixed": True
            }
        
        # 7. 完全失败，返回基础结构
        logger.warning("JSON修复失败，返回基础结构")
        return {
            "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} is a {entity_type}."
        }
    
    def _get_system_prompt(self, is_individual: bool) -> str:
        """System prompt for persona generation."""
        return (
            "You are an expert at generating detailed, realistic social media user personas "
            "for opinion simulation. Return valid JSON only; no unescaped newlines in string values. "
            "Respond in Chinese."
        )

        """获取系统提示词"""
        if self.language == 'en':
            base_prompt = "You are a social media persona generation expert. Generate detailed, realistic personas for opinion simulation, restoring existing real-world situations as closely as possible. You must return valid JSON format. All string values must not contain unescaped newlines. Use English."
        else:
            base_prompt = "你是社交媒体用户画像生成专家。生成详细、真实的人设用于舆论模拟,最大程度还原已有现实情况。必须返回有效的JSON格式，所有字符串值不能包含未转义的换行符。使用中文。"
        return base_prompt
    def _get_system_prompt(self, is_individual: bool, locale: str = 'zh') -> str:
        """获取系统提示词"""
        lang_label = _LANG_LABEL.get(locale, '中文')
        base_prompt = f"你是社交媒体用户画像生成专家。生成详细、真实的人设用于舆论模拟,最大程度还原已有现实情况。必须返回有效的JSON格式，所有字符串值不能包含未转义的换行符。使用{lang_label}。"
        lang_inst = LANGUAGE_INSTRUCTIONS.get(locale, LANGUAGE_INSTRUCTIONS['zh'])
        return base_prompt + lang_inst
    
    def _build_individual_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        locale: str = 'zh'
    ) -> str:
        """Build prompt for individual entity persona."""
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "None"
        context_str = context[:3000] if context else "No extra context"
        return f"""Generate a detailed social media user persona for this entity.
        """构建个人实体的详细人设提示词"""

        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
        context_str = context[:3000] if context else "无额外上下文"
        lang_label = _LANG_LABEL.get(locale, '中文')

        return f"""为实体生成详细的社交媒体用户人设,最大程度还原已有现实情况。

        if self.language == 'en':
            attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "None"
            context_str = context[:3000] if context else "No additional context"

            return f"""Generate a detailed social media persona for this entity, restoring real-world situations as closely as possible.

Entity Name: {entity_name}
Entity Type: {entity_type}
Entity Summary: {entity_summary}
Entity Attributes: {attrs_str}

Context:
{context_str}

Generate JSON with the following fields:

1. bio: Social media bio, 200 words
2. persona: Detailed persona description (2000 words plain text), must include:
   - Basic info (age, profession, education, location)
   - Background (key experiences, connection to events, social relationships)
   - Personality traits (MBTI type, core personality, emotional expression)
   - Social media behavior (posting frequency, content preferences, interaction style, language characteristics)
   - Stance and views (attitudes on topics, content that triggers/moves them)
   - Unique features (catchphrases, special experiences, personal hobbies)
   - Personal memory (important part: describe this individual's connection to events, and their past actions and reactions)
3. age: Age as integer
4. gender: Must be English: "male" or "female"
5. mbti: MBTI type (e.g. INTJ, ENFP)
6. country: Country name in English
7. profession: Profession
8. interested_topics: Array of topics of interest

Important:
- All field values must be strings or numbers, no newlines
- persona must be a coherent text description
- Use English for all fields
- Content must be consistent with entity information
- age must be a valid integer, gender must be "male" or "female"
"""
        else:
            attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
            context_str = context[:3000] if context else "无额外上下文"

            return f"""为实体生成详细的社交媒体用户人设,最大程度还原已有现实情况。

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context:
{context_str}

Return JSON with these fields:
1. bio: short bio (about 200 chars)
2. persona: detailed persona text (~2000 chars) covering: basic info (age, job, education, location), background (key experiences, relation to events, social ties), personality (MBTI, traits, expression), social media behavior (posting frequency, content preferences, interaction style), stance and views, distinctive traits, personal memory (this individual's link to the event and past actions/reactions).
3. age: integer
4. gender: "male" or "female"
5. mbti: e.g. INTJ, ENFP
6. country: e.g. China (use Chinese for country name)
7. profession: string
8. interested_topics: array of strings

Rules: all values must be strings or numbers, no newlines; persona must be one coherent paragraph; use Chinese except gender must be "male"/"female"; age must be integer, gender must be "male" or "female".
1. bio: 社交媒体简介，200字
2. persona: 详细人设描述（2000字的纯文本），需包含:
   - 基本信息（年龄、职业、教育背景、所在地）
   - 人物背景（重要经历、与事件的关联、社会关系）
   - 性格特征（MBTI类型、核心性格、情绪表达方式）
   - 社交媒体行为（发帖频率、内容偏好、互动风格、语言特点）
   - 立场观点（对话题的态度、可能被激怒/感动的内容）
   - 独特特征（口头禅、特殊经历、个人爱好）
   - 个人记忆（人设的重要部分，要介绍这个个体与事件的关联，以及这个个体在事件中的已有动作与反应）
3. age: 年龄数字（必须是整数）
4. gender: 性别，必须是英文: "male" 或 "female"
5. mbti: MBTI类型（如INTJ、ENFP等）
6. country: 国家（使用{lang_label}）
7. profession: 职业
8. interested_topics: 感兴趣话题数组

重要:
- 所有字段值必须是字符串或数字，不要使用换行符
- persona必须是一段连贯的文字描述
- 使用{lang_label}（除了gender字段必须用英文male/female）
- 内容要与实体信息保持一致
- age必须是有效的整数，gender必须是"male"或"female"
"""

    def _build_group_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        locale: str = 'zh'
    ) -> str:
        """Build prompt for group/organization entity persona."""
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "None"
        context_str = context[:3000] if context else "No extra context"
        return f"""Generate a detailed social media account persona for this organization/group entity.
        """构建群体/机构实体的详细人设提示词"""

        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
        context_str = context[:3000] if context else "无额外上下文"
        lang_label = _LANG_LABEL.get(locale, '中文')

        return f"""为机构/群体实体生成详细的社交媒体账号设定,最大程度还原已有现实情况。

        if self.language == 'en':
            attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "None"
            context_str = context[:3000] if context else "No additional context"

            return f"""Generate a detailed social media account profile for this organization/group entity, restoring real-world situations as closely as possible.

Entity Name: {entity_name}
Entity Type: {entity_type}
Entity Summary: {entity_summary}
Entity Attributes: {attrs_str}

Context:
{context_str}

Generate JSON with the following fields:

1. bio: Official account bio, 200 words, professional and appropriate
2. persona: Detailed account description (2000 words plain text), must include:
   - Organization basic info (formal name, nature, founding background, main functions)
   - Account positioning (account type, target audience, core functionality)
   - Speaking style (language characteristics, common expressions, forbidden topics)
   - Publishing characteristics (content types, publishing frequency, active hours)
   - Stance and attitude (official positions on core topics, handling of controversies)
   - Special notes (represented group profile, operational habits)
   - Organization memory (important part: describe this organization's connection to events, and their past actions and reactions)
3. age: Fixed value 30 (virtual age for organizational accounts)
4. gender: Fixed value "other" (organizational accounts use "other")
5. mbti: MBTI type describing account style, e.g. ISTJ for rigorous and conservative
6. country: Country name in English
7. profession: Organization function description
8. interested_topics: Array of focus areas

Important:
- All field values must be strings or numbers, no null values
- persona must be a coherent text description, no newlines
- Use English for all fields
- age must be integer 30, gender must be string "other"
- Organization account speech must match its identity positioning"""
        else:
            attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
            context_str = context[:3000] if context else "无额外上下文"

            return f"""为机构/群体实体生成详细的社交媒体账号设定,最大程度还原已有现实情况。

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context:
{context_str}

Return JSON with: 1. bio: official account bio (~200 chars). 2. persona: detailed account persona (~2000 chars) covering: org basics (name, nature, founding, main functions), account positioning (type, audience, core role), tone and style, content and posting habits, stance and controversy handling, represented group, org memory (link to event and past actions/reactions). 3. age: 30. 4. gender: "other". 5. mbti: e.g. ISTJ for formal style. 6. country: use Chinese. 7. profession: org role. 8. interested_topics: array.

Rules: no nulls; persona one coherent paragraph, no newlines; use Chinese except gender="other"; age=30, gender="other"; tone must match org identity."""
1. bio: 官方账号简介，200字，专业得体
2. persona: 详细账号设定描述（2000字的纯文本），需包含:
   - 机构基本信息（正式名称、机构性质、成立背景、主要职能）
   - 账号定位（账号类型、目标受众、核心功能）
   - 发言风格（语言特点、常用表达、禁忌话题）
   - 发布内容特点（内容类型、发布频率、活跃时间段）
   - 立场态度（对核心话题的官方立场、面对争议的处理方式）
   - 特殊说明（代表的群体画像、运营习惯）
   - 机构记忆（机构人设的重要部分，要介绍这个机构与事件的关联，以及这个机构在事件中的已有动作与反应）
3. age: 固定填30（机构账号的虚拟年龄）
4. gender: 固定填"other"（机构账号使用other表示非个人）
5. mbti: MBTI类型，用于描述账号风格，如ISTJ代表严谨保守
6. country: 国家（使用{lang_label}）
7. profession: 机构职能描述
8. interested_topics: 关注领域数组

重要:
- 所有字段值必须是字符串或数字，不允许null值
- persona必须是一段连贯的文字描述，不要使用换行符
- 使用{lang_label}（除了gender字段必须用英文"other"）
- age必须是整数30，gender必须是字符串"other"
- 机构账号发言要符合其身份定位"""
    
    def _generate_profile_rule_based(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate basic persona by rules (no LLM)."""
        entity_type_lower = entity_type.lower()
        
        if entity_type_lower in ["student", "alumni"]:
            return {
                "bio": f"{entity_type} with interests in academics and social issues.",
                "persona": f"{entity_name} is a {entity_type.lower()} who is actively engaged in academic and social discussions. They enjoy sharing perspectives and connecting with peers.",
                "age": random.randint(18, 30),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": "Student",
                "interested_topics": ["Education", "Social Issues", "Technology"],
            }
        
        elif entity_type_lower in ["publicfigure", "expert", "faculty"]:
            return {
                "bio": "Expert and thought leader in their field.",
                "persona": f"{entity_name} is a recognized {entity_type.lower()} who shares insights and opinions on important matters. They are known for their expertise and influence in public discourse.",
                "age": random.randint(35, 60),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(["ENTJ", "INTJ", "ENTP", "INTP"]),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_attributes.get("occupation", "Expert"),
                "interested_topics": ["Politics", "Economics", "Culture & Society"],
            }
        
        elif entity_type_lower in ["mediaoutlet", "socialmediaplatform"]:
            return {
                "bio": f"Official account for {entity_name}. News and updates.",
                "persona": f"{entity_name} is a media entity that reports news and facilitates public discourse. The account shares timely updates and engages with the audience on current events.",
                "age": 30,
                "gender": "other",
                "mbti": "ISTJ",
                "country": "China",
                "profession": "Media",
                "interested_topics": ["General News", "Current Events", "Public Affairs"],
            }
        
        elif entity_type_lower in ["university", "governmentagency", "ngo", "organization"]:
            return {
                "bio": f"Official account of {entity_name}.",
                "persona": f"{entity_name} is an institutional entity that communicates official positions, announcements, and engages with stakeholders on relevant matters.",
                "age": 30,
                "gender": "other",
                "mbti": "ISTJ",
                "country": "China",
                "profession": entity_type,
                "interested_topics": ["Public Policy", "Community", "Official Announcements"],
            }
        else:
            return {
                "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
                "persona": entity_summary or f"{entity_name} is a {entity_type.lower()} participating in social discussions.",
                "age": random.randint(25, 50),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_type,
                "interested_topics": ["General", "Social Issues"],
            }
    
    def set_graph_id(self, graph_id: str):
        """Set graph ID for Zep retrieval."""
        self.graph_id = graph_id

    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit",
        locale: str = 'zh'
    ) -> List[OasisAgentProfile]:
        """Batch-generate agent profiles from entities (parallel); optional realtime file write."""
        """
        批量从实体生成Agent Profile（支持并行生成）

        Args:
            entities: 实体列表
            use_llm: 是否使用LLM生成详细人设
            progress_callback: 进度回调函数 (current, total, message)
            graph_id: 图谱ID，用于Zep检索获取更丰富上下文
            parallel_count: 并行生成数量，默认5
            realtime_output_path: 实时写入的文件路径（如果提供，每生成一个就写入一次）
            output_platform: 输出平台格式 ("reddit" 或 "twitter")
            locale: 语言偏好 ('zh', 'en', 'ko')

        Returns:
            Agent Profile列表
        """
        import concurrent.futures
        from threading import Lock
        if graph_id:
            self.graph_id = graph_id
        total = len(entities)
        profiles = [None] * total
        completed_count = [0]
        lock = Lock()

        def save_profiles_realtime():
            """Write currently generated profiles to file."""
            if not realtime_output_path:
                return
            with lock:
                existing_profiles = [p for p in profiles if p is not None]
                if not existing_profiles:
                    return
                
                try:
                    if output_platform == "reddit":
                        profiles_data = [p.to_reddit_format() for p in existing_profiles]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
                    else:
                        import csv
                        profiles_data = [p.to_twitter_format() for p in existing_profiles]
                        if profiles_data:
                            fieldnames = list(profiles_data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(profiles_data)
                except Exception as e:
                    logger.warning(f"Realtime save profiles failed: {e}")

        def generate_single_profile(idx: int, entity: EntityNode) -> tuple:
            """Worker: generate one profile for an entity."""
            entity_type = entity.get_entity_type() or "Entity"
            try:
                profile = self.generate_profile_from_entity(
                    entity=entity,
                    user_id=idx,
                    use_llm=use_llm,
                    locale=locale
                )
                self._print_generated_profile(entity.name, entity_type, profile)
                return idx, profile, None
            except Exception as e:
                logger.error(f"Profile generation failed for entity {entity.name}: {str(e)}")
                fallback_profile = OasisAgentProfile(
                    user_id=idx,
                    user_name=self._generate_username(entity.name),
                    name=entity.name,
                    bio=f"{entity_type}: {entity.name}",
                    persona=entity.summary or "A participant in social discussions.",
                    source_entity_uuid=entity.uuid,
                    source_entity_type=entity_type,
                )
                return idx, fallback_profile, str(e)
        
        logger.info(f"Starting parallel profile generation: {total} entities, workers={parallel_count}")
        print(f"\n{'='*60}")
        print(f"Generating agent profiles - {total} entities, parallel={parallel_count}")
        logger.info(get_error_message('log_profile_parallel_start', locale).format(total=total, parallel=parallel_count))
        print(f"\n{'='*60}")
        print(f"Starting agent profile generation - {total} entities, parallelism: {parallel_count}")
        print(f"{'='*60}\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            future_to_entity = {
                executor.submit(generate_single_profile, idx, entity): (idx, entity)
                for idx, entity in enumerate(entities)
            }
            
            for future in concurrent.futures.as_completed(future_to_entity):
                idx, entity = future_to_entity[future]
                entity_type = entity.get_entity_type() or "Entity"
                
                try:
                    result_idx, profile, error = future.result()
                    profiles[result_idx] = profile
                    
                    with lock:
                        completed_count[0] += 1
                        current = completed_count[0]
                    
                    save_profiles_realtime()
                    if progress_callback:
                        progress_callback(current, total, f"Done {current}/{total}: {entity.name} ({entity_type})")
                        progress_callback(
                            current, 
                            total, 
                            get_error_message('sim_profile_done_item', locale).format(
                                current=current, total=total, name=entity.name, type=entity_type
                            )
                        )
                    
                    if error:
                        logger.warning(f"[{current}/{total}] {entity.name} using fallback: {error}")
                    else:
                        logger.info(f"[{current}/{total}] Profile generated: {entity.name} ({entity_type})")
                        logger.info(get_error_message('log_profile_gen_ok', locale).format(current=current, total=total, name=entity.name, type=entity_type))
                        
                except Exception as e:
                    logger.error(f"Exception processing entity {entity.name}: {str(e)}")
                    with lock:
                        completed_count[0] += 1
                    profiles[idx] = OasisAgentProfile(
                        user_id=idx,
                        user_name=self._generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "A participant in social discussions.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )
                    save_profiles_realtime()
        print(f"\n{'='*60}")
        print(f"Profile generation done. Total: {len([p for p in profiles if p])} agents")
        print(f"{'='*60}\n")
        return profiles

    def _print_generated_profile(self, entity_name: str, entity_type: str, profile: OasisAgentProfile):
        """Print generated profile to console (full content)."""
        separator = "-" * 70
        topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else 'None'
        output_lines = [
            f"\n{separator}",
            f"[Generated] {entity_name} ({entity_type})",
            f"{separator}",
            f"Username: {profile.user_name}",
            f"",
            f"[Bio]",
            f"{profile.bio}",
            f"",
            f"[Persona]",
            f"{profile.persona}",
            f"",
            f"[Attributes]",
            f"Age: {profile.age} | Gender: {profile.gender} | MBTI: {profile.mbti}",
            f"Profession: {profile.profession} | Country: {profile.country}",
            f"Topics: {topics_str}",
            f"用户名: {profile.user_name}",
            "",
            "【简介】",
            f"{profile.bio}",
            "",
            "【详细人设】",
            f"{profile.persona}",
            "",
            "【基本属性】",
            f"年龄: {profile.age} | 性别: {profile.gender} | MBTI: {profile.mbti}",
            f"职业: {profile.profession} | 国家: {profile.country}",
            f"兴趣话题: {topics_str}",
            separator
        ]
        print("\n".join(output_lines))

    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """Save profiles to file. OASIS: Twitter=CSV, Reddit=JSON."""
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)
    
    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """Save Twitter profiles as CSV (OASIS: user_id, name, username, user_char, description)."""
        import csv
        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)
            for idx, profile in enumerate(profiles):
                # Defensive coercion in case __post_init__ was bypassed
                bio = _coerce_to_str(profile.bio) if profile.bio else profile.name
                persona = _coerce_to_str(profile.persona) if profile.persona else ''
                
                # user_char: 完整人设（bio + persona），用于LLM系统提示
                user_char = bio
                if persona and persona != bio:
                    user_char = f"{bio} {persona}"
                # 处理换行符（CSV中用空格替代）
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')
                
                # description: 简短简介，用于外部显示
                description = bio.replace('\n', ' ').replace('\r', ' ')
                
                row = [
                    idx,                    # user_id: 从0开始的顺序ID
                    profile.name,           # name: 真实姓名
                    profile.user_name,      # username: 用户名
                    user_char,              # user_char: 完整人设（内部LLM使用）
                    description             # description: 简短简介（外部显示）
                ]
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')
                description = profile.bio.replace('\n', ' ').replace('\r', ' ')
                row = [idx, profile.name, profile.user_name, user_char, description]
                writer.writerow(row)
        logger.info(f"Saved {len(profiles)} Twitter profiles to {file_path} (OASIS CSV)")

        
        logger.info(f"Saved {len(profiles)} Twitter profiles to {file_path} (OASIS CSV format)")
    
    def _normalize_gender(self, gender: Optional[str]) -> str:
        """Normalize gender to OASIS values: male, female, other (incl. Chinese mapping)."""
        if not gender:
            return "other"
        gender_lower = gender.lower().strip()
        gender_map = {
            "男": "male",
            "女": "female",
            "机构": "other",
            "其他": "other",
            "male": "male",
            "female": "female",
            "other": "other",
        }
        return gender_map.get(gender_lower, "other")

    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """Save Reddit profiles as JSON (same shape as to_reddit_format(); user_id required for OASIS)."""
        data = []
        for idx, profile in enumerate(profiles):
            # Defensive coercion in case __post_init__ was bypassed
            bio = _coerce_to_str(profile.bio) if profile.bio else f"{profile.name}"
            persona = _coerce_to_str(profile.persona) if profile.persona else (
                f"{profile.name} is a participant in social discussions."
            )
            country = _coerce_to_str(profile.country) if profile.country else "中国"
            profession = _coerce_to_str(profile.profession) if profile.profession else None
            interested_topics = (
                _coerce_to_str_list(profile.interested_topics)
                if profile.interested_topics
                else None
            )
            
            # 使用与 to_reddit_format() 一致的格式
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,
                "username": profile.user_name,
                "name": profile.name,
                "bio": bio[:150],
                "persona": persona,
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                "age": profile.age if profile.age else 30,
                "gender": self._normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": country,
            }
            
            # 可选字段
            if profession:
                item["profession"] = profession
            if interested_topics:
                item["interested_topics"] = interested_topics
            
                "country": profile.country if profile.country else "China",
            }
            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics
            data.append(item)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(profiles)} Reddit profiles to {file_path} (JSON with user_id)")

        
        logger.info(f"Saved {len(profiles)} Reddit profiles to {file_path} (JSON format with user_id)")
    
    # 保留旧方法名作为别名，保持向后兼容
    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[Deprecated] Use save_profiles() instead."""
        logger.warning("save_profiles_to_json is deprecated, use save_profiles")
        self.save_profiles(profiles, file_path, platform)

