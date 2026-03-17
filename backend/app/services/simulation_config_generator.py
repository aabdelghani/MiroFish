"""
Simulation config generator: uses LLM to generate simulation parameters from requirements, documents, and graph data (fully automated).

Stepwise generation: 1) time config, 2) event config, 3) agent configs in batches, 4) platform config.
"""

import json
import math
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import _is_minimax, _clamp_temperature, _inject_json_instruction, parse_json_from_response
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('mirofish.simulation_config')

# China timezone activity config (Beijing time): dead/morning/work/peak/night hours and multipliers
CHINA_TIMEZONE_CONFIG = {
    "dead_hours": [0, 1, 2, 3, 4, 5],
    "morning_hours": [6, 7, 8],
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "peak_hours": [19, 20, 21, 22],
    "night_hours": [23],
    "activity_multipliers": {
        "dead": 0.05,
        "morning": 0.4,
        "work": 0.7,
        "peak": 1.5,
        "night": 0.5
    }
}


@dataclass
class AgentActivityConfig:
    """Per-agent activity config."""
    agent_id: int
    entity_uuid: str
    entity_name: str
    entity_type: str
    activity_level: float = 0.5
    posts_per_hour: float = 1.0
    comments_per_hour: float = 2.0
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))
    response_delay_min: int = 5
    response_delay_max: int = 60
    sentiment_bias: float = 0.0
    stance: str = "neutral"  # supportive, opposing, neutral, observer
    influence_weight: float = 1.0


@dataclass
class TimeSimulationConfig:
    """Time simulation config (China timezone / activity patterns)."""
    total_simulation_hours: int = 72
    minutes_per_round: int = 60
    agents_per_hour_min: int = 5
    agents_per_hour_max: int = 20
    peak_hours: List[int] = field(default_factory=lambda: [19, 20, 21, 22])
    peak_activity_multiplier: float = 1.5
    off_peak_hours: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    off_peak_activity_multiplier: float = 0.05
    morning_hours: List[int] = field(default_factory=lambda: [6, 7, 8])
    morning_activity_multiplier: float = 0.4
    work_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
    work_activity_multiplier: float = 0.7


@dataclass
class EventConfig:
    """Event config: initial posts, scheduled events, hot topics, narrative direction."""
    initial_posts: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_events: List[Dict[str, Any]] = field(default_factory=list)
    hot_topics: List[str] = field(default_factory=list)
    narrative_direction: str = ""


@dataclass
class PlatformConfig:
    """Platform-specific config (twitter/reddit): recency/popularity/relevance weights, viral threshold, echo chamber."""
    platform: str
    recency_weight: float = 0.4
    popularity_weight: float = 0.3
    relevance_weight: float = 0.3
    viral_threshold: int = 10
    echo_chamber_strength: float = 0.5


@dataclass
class SimulationParameters:
    """Full simulation parameters: ids, time_config, agent_configs, event_config, platform configs, LLM, metadata."""
    simulation_id: str
    project_id: str
    graph_id: str
    simulation_requirement: str
    time_config: TimeSimulationConfig = field(default_factory=TimeSimulationConfig)
    agent_configs: List[AgentActivityConfig] = field(default_factory=list)
    event_config: EventConfig = field(default_factory=EventConfig)
    twitter_config: Optional[PlatformConfig] = None
    reddit_config: Optional[PlatformConfig] = None
    llm_model: str = ""
    llm_base_url: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        time_dict = asdict(self.time_config)
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "time_config": time_dict,
            "agent_configs": [asdict(a) for a in self.agent_configs],
            "event_config": asdict(self.event_config),
            "twitter_config": asdict(self.twitter_config) if self.twitter_config else None,
            "reddit_config": asdict(self.reddit_config) if self.reddit_config else None,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "generated_at": self.generated_at,
            "generation_reasoning": self.generation_reasoning,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class SimulationConfigGenerator:
    """LLM-based simulation config generator: time + event + batched agent configs + platform config."""
    MAX_CONTEXT_LENGTH = 50000
    AGENTS_PER_BATCH = 15
    TIME_CONFIG_CONTEXT_LENGTH = 10000
    EVENT_CONFIG_CONTEXT_LENGTH = 8000
    ENTITY_SUMMARY_LENGTH = 300
    AGENT_SUMMARY_LENGTH = 300
    ENTITIES_PER_TYPE_DISPLAY = 20

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        language: str = "zh"
    ):
        self.language = language
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_config(
        self,
        simulation_id: str,
        project_id: str,
        graph_id: str,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode],
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> SimulationParameters:
        """Generate full simulation config stepwise (time -> events -> batched agents -> platform)."""
        logger.info(f"Starting simulation config generation: simulation_id={simulation_id}, entities={len(entities)}")
        num_batches = math.ceil(len(entities) / self.AGENTS_PER_BATCH)
        total_steps = 3 + num_batches
        current_step = 0
        
        def report_progress(step: int, message: str):
            nonlocal current_step
            current_step = step
            if progress_callback:
                progress_callback(step, total_steps, message)
            logger.info(f"[{step}/{total_steps}] {message}")
        
        context = self._build_context(
            simulation_requirement=simulation_requirement,
            document_text=document_text,
            entities=entities
        )
        
        reasoning_parts = []
        
        report_progress(1, "Generating time config...")
        num_entities = len(entities)
        time_config_result = self._generate_time_config(context, num_entities)
        time_config = self._parse_time_config(time_config_result, num_entities)
        reasoning_parts.append(f"Time config: {time_config_result.get('reasoning', 'OK')}")
        report_progress(2, "Generating event config and hot topics...")
        event_config_result = self._generate_event_config(context, simulation_requirement, entities)
        event_config = self._parse_event_config(event_config_result)
        reasoning_parts.append(f"Event config: {event_config_result.get('reasoning', 'OK')}")
        all_agent_configs = []
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.AGENTS_PER_BATCH
            end_idx = min(start_idx + self.AGENTS_PER_BATCH, len(entities))
            batch_entities = entities[start_idx:end_idx]
            
            report_progress(
                3 + batch_idx,
                f"Generating agent configs ({start_idx + 1}-{end_idx}/{len(entities)})..."
            )
            
            batch_configs = self._generate_agent_configs_batch(
                context=context,
                entities=batch_entities,
                start_idx=start_idx,
                simulation_requirement=simulation_requirement
            )
            all_agent_configs.extend(batch_configs)
        
        reasoning_parts.append(f"Agent configs: {len(all_agent_configs)} generated")
        logger.info("Assigning poster agents to initial posts...")
        event_config = self._assign_initial_post_agents(event_config, all_agent_configs)
        assigned_count = len([p for p in event_config.initial_posts if p.get("poster_agent_id") is not None])
        reasoning_parts.append(f"Initial posts: {assigned_count} assigned poster")
        report_progress(total_steps, "Generating platform config...")
        twitter_config = None
        reddit_config = None
        
        if enable_twitter:
            twitter_config = PlatformConfig(
                platform="twitter",
                recency_weight=0.4,
                popularity_weight=0.3,
                relevance_weight=0.3,
                viral_threshold=10,
                echo_chamber_strength=0.5
            )
        
        if enable_reddit:
            reddit_config = PlatformConfig(
                platform="reddit",
                recency_weight=0.3,
                popularity_weight=0.4,
                relevance_weight=0.3,
                viral_threshold=15,
                echo_chamber_strength=0.6
            )
        
        params = SimulationParameters(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            simulation_requirement=simulation_requirement,
            time_config=time_config,
            agent_configs=all_agent_configs,
            event_config=event_config,
            twitter_config=twitter_config,
            reddit_config=reddit_config,
            llm_model=self.model_name,
            llm_base_url=self.base_url,
            generation_reasoning=" | ".join(reasoning_parts)
        )
        
        logger.info(f"Simulation config done: {len(params.agent_configs)} agent configs")
        return params

    def _build_context(
        self,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode]
    ) -> str:
        """Build LLM context, truncated to max length."""
        entity_summary = self._summarize_entities(entities)
        context_parts = [
            f"## Simulation requirement\n{simulation_requirement}",
            f"\n## Entity info ({len(entities)})\n{entity_summary}",
        ]
        current_length = sum(len(p) for p in context_parts)
        remaining_length = self.MAX_CONTEXT_LENGTH - current_length - 500
        if remaining_length > 0 and document_text:
            doc_text = document_text[:remaining_length]
            if len(document_text) > remaining_length:
                doc_text += "\n...(document truncated)"
            context_parts.append(f"\n## Document content\n{doc_text}")
        
        return "\n".join(context_parts)
    
    def _summarize_entities(self, entities: List[EntityNode]) -> str:
        """Build entity summary by type."""
        lines = []
        by_type: Dict[str, List[EntityNode]] = {}
        for e in entities:
            t = e.get_entity_type() or "Unknown"
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(e)
        for entity_type, type_entities in by_type.items():
            lines.append(f"\n### {entity_type} ({len(type_entities)})")
            display_count = self.ENTITIES_PER_TYPE_DISPLAY
            summary_len = self.ENTITY_SUMMARY_LENGTH
            for e in type_entities[:display_count]:
                summary_preview = (e.summary[:summary_len] + "...") if len(e.summary) > summary_len else e.summary
                lines.append(f"- {e.name}: {summary_preview}")
            if len(type_entities) > display_count:
                lines.append(f"  ... and {len(type_entities) - display_count} more")
        
        return "\n".join(lines)
    
    def _call_llm_with_retry(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """LLM call with retry and JSON repair."""
        max_attempts = 3
        last_error = None
        for attempt in range(max_attempts):
            try:
                kwargs = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
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
        """带重试的LLM调用，包含JSON修复逻辑"""
        import re

        max_attempts = 3
        last_error = None
        use_minimax = _is_minimax(self.model_name, self.base_url)

        for attempt in range(max_attempts):
            try:
                temperature = _clamp_temperature(0.7 - (attempt * 0.1), self.model_name, self.base_url)
                messages = [
                    {"role": "system", "content": system_prompt},
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
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                finish_reason = response.choices[0].finish_reason

                # 检查是否被截断
                if finish_reason == 'length':
                    logger.warning(f"LLM output truncated (attempt {attempt+1})")
                    content = self._fix_truncated_json(content)
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse failed (attempt {attempt+1}): {str(e)[:80]}")
                    fixed = self._try_fix_config_json(content)
                    if fixed:
                        return fixed

                # 尝试解析JSON
                try:
                    return parse_json_from_response(content)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"JSON解析失败 (attempt {attempt+1}): {str(e)[:80]}")

                    # 尝试修复JSON
                    fixed = self._try_fix_config_json(content)
                    if fixed:
                        return fixed

                    last_error = e
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(2 * (attempt + 1))
        raise last_error or Exception("LLM call failed")

    def _fix_truncated_json(self, content: str) -> str:
        """Close truncated JSON (braces/brackets and trailing string)."""
        content = content.strip()
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        if content and content[-1] not in '",}]':
            content += '"'
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_config_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Try to repair config JSON (truncation + extract object)."""
        import re
        content = self._fix_truncated_json(content)
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            def fix_string(match):
                s = match.group(0)
                s = s.replace('\n', ' ').replace('\r', ' ')
                s = re.sub(r'\s+', ' ', s)
                return s
            
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string, json_str)
            
            try:
                return json.loads(json_str)
            except Exception:
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                json_str = re.sub(r'\s+', ' ', json_str)
                try:
                    return json.loads(json_str)
                except Exception:
                    pass
        
        return None
    
    def _generate_time_config(self, context: str, num_entities: int) -> Dict[str, Any]:
        """Generate time config via LLM (China timezone / activity patterns)."""
        context_truncated = context[:self.TIME_CONFIG_CONTEXT_LENGTH]
        max_agents_allowed = max(1, int(num_entities * 0.9))
        prompt = f"""Generate time simulation config from the simulation requirement below.
        
        if self.language == 'en':
            prompt = f"""Based on the following simulation requirements, generate time simulation configuration.

{context_truncated}

## Task
Generate time configuration JSON.

### Basic Principles (for reference, adjust based on specific events and participant groups):
- Adjust activity patterns based on the target population's timezone and habits
- Late night 0-5am: minimal activity (activity coefficient 0.05)
- Morning 6-8am: gradually increasing (activity coefficient 0.4)
- Work hours 9-18: moderate activity (activity coefficient 0.7)
- Evening 19-22: peak hours (activity coefficient 1.5)
- After 23: declining activity (activity coefficient 0.5)
- **Important**: Adjust time periods based on event nature and participant characteristics
  - E.g.: Student groups may peak at 21-23; media active all day; official institutions only during work hours

### Return JSON format (no markdown)

Example:
{{
    "total_simulation_hours": 72,
    "minutes_per_round": 60,
    "agents_per_hour_min": 5,
    "agents_per_hour_max": 50,
    "peak_hours": [19, 20, 21, 22],
    "off_peak_hours": [0, 1, 2, 3, 4, 5],
    "morning_hours": [6, 7, 8],
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "reasoning": "Time configuration explanation for this event"
}}

Field descriptions:
- total_simulation_hours (int): Total simulation duration, 24-168 hours
- minutes_per_round (int): Duration per round, 30-120 minutes, recommended 60
- agents_per_hour_min (int): Min agents activated per hour (range: 1-{max_agents_allowed})
- agents_per_hour_max (int): Max agents activated per hour (range: 1-{max_agents_allowed})
- peak_hours (int array): Peak hours, adjust based on participant groups
- off_peak_hours (int array): Off-peak hours, typically late night
- morning_hours (int array): Morning hours
- work_hours (int array): Work hours
- reasoning (string): Brief explanation of configuration"""

            system_prompt = "You are a social media simulation expert. Return pure JSON format."
        else:
            prompt = f"""基于以下模拟需求，生成时间模拟配置。

{context_truncated}

## Task
Output time config as JSON only (no markdown).

### Guidelines (adjust to event and audience):
- Audience: China timezone (Beijing). 0-5 low activity (0.05), 6-8 morning ramp (0.4), 9-18 work (0.7), 19-22 peak (1.5), 23+ decline (0.5).
- Adjust by audience: e.g. students peak 21-23; media all-day; officials work hours only; breaking news may shorten off_peak_hours.

### JSON format
{{
    "total_simulation_hours": 72,
    "minutes_per_round": 60,
    "agents_per_hour_min": 5,
    "agents_per_hour_max": 50,
    "peak_hours": [19, 20, 21, 22],
    "off_peak_hours": [0, 1, 2, 3, 4, 5],
    "morning_hours": [6, 7, 8],
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "reasoning": "brief explanation"
}}

Fields: total_simulation_hours (24-168), minutes_per_round (30-120, suggest 60), agents_per_hour_min/max (1-{max_agents_allowed}), peak_hours, off_peak_hours, morning_hours, work_hours, reasoning."""

        system_prompt = "You are a social simulation expert. Return pure JSON; time config should follow China timezone activity patterns."
            system_prompt = "你是社交媒体模拟专家。返回纯JSON格式，时间配置需符合中国人作息习惯。"
        
        try:
            return self._call_llm_with_retry(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Time config LLM failed: {e}, using default")
            return self._get_default_time_config(num_entities)

    def _get_default_time_config(self, num_entities: int) -> Dict[str, Any]:
        """Default time config (China timezone)."""
        return {
            "total_simulation_hours": 72,
            "minutes_per_round": 60,
            "agents_per_hour_min": max(1, num_entities // 15),
            "agents_per_hour_max": max(5, num_entities // 5),
            "peak_hours": [19, 20, 21, 22],
            "off_peak_hours": [0, 1, 2, 3, 4, 5],
            "morning_hours": [6, 7, 8],
            "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            "reasoning": "Default China timezone (1 hour per round)"
        }

    def _parse_time_config(self, result: Dict[str, Any], num_entities: int) -> TimeSimulationConfig:
        """Parse time config and clamp agents_per_hour to total agent count."""
        agents_per_hour_min = result.get("agents_per_hour_min", max(1, num_entities // 15))
        agents_per_hour_max = result.get("agents_per_hour_max", max(5, num_entities // 5))
        if agents_per_hour_min > num_entities:
            logger.warning(f"agents_per_hour_min ({agents_per_hour_min}) > total agents ({num_entities}), clamped")
            agents_per_hour_min = max(1, num_entities // 10)
        if agents_per_hour_max > num_entities:
            logger.warning(f"agents_per_hour_max ({agents_per_hour_max}) > total agents ({num_entities}), clamped")
            agents_per_hour_max = max(agents_per_hour_min + 1, num_entities // 2)
        if agents_per_hour_min >= agents_per_hour_max:
            agents_per_hour_min = max(1, agents_per_hour_max // 2)
            logger.warning(f"agents_per_hour_min >= max, set to {agents_per_hour_min}")
        return TimeSimulationConfig(
            total_simulation_hours=result.get("total_simulation_hours", 72),
            minutes_per_round=result.get("minutes_per_round", 60),
            agents_per_hour_min=agents_per_hour_min,
            agents_per_hour_max=agents_per_hour_max,
            peak_hours=result.get("peak_hours", [19, 20, 21, 22]),
            off_peak_hours=result.get("off_peak_hours", [0, 1, 2, 3, 4, 5]),
            off_peak_activity_multiplier=0.05,
            morning_hours=result.get("morning_hours", [6, 7, 8]),
            morning_activity_multiplier=0.4,
            work_hours=result.get("work_hours", list(range(9, 19))),
            work_activity_multiplier=0.7,
            peak_activity_multiplier=1.5
        )
    
    def _generate_event_config(
        self,
        context: str,
        simulation_requirement: str,
        entities: List[EntityNode]
    ) -> Dict[str, Any]:
        """Generate event config (hot topics, narrative, initial posts with poster_type)."""
        entity_types_available = list(set(e.get_entity_type() or "Unknown" for e in entities))
        type_examples = {}
        for e in entities:
            etype = e.get_entity_type() or "Unknown"
            if etype not in type_examples:
                type_examples[etype] = []
            if len(type_examples[etype]) < 3:
                type_examples[etype].append(e.name)
        type_info = "\n".join([f"- {t}: {', '.join(examples)}" for t, examples in type_examples.items()])
        context_truncated = context[:self.EVENT_CONFIG_CONTEXT_LENGTH]
        prompt = f"""Generate event config from the simulation requirement below.
        
        if self.language == 'en':
            prompt = f"""Based on the following simulation requirements, generate event configuration.

Simulation Requirement: {simulation_requirement}

{context_truncated}

## Available Entity Types and Examples
{type_info}

## Task
Generate event configuration JSON:
- Extract hot topic keywords
- Describe the direction of public opinion development
- Design initial post content, **each post must specify poster_type**

**Important**: poster_type must be selected from the "Available Entity Types" above, so initial posts can be assigned to appropriate Agents.
For example: official statements should be published by Official/University types, news by MediaOutlet, student opinions by Student.

Return JSON format (no markdown):
{{
    "hot_topics": ["keyword1", "keyword2", ...],
    "narrative_direction": "<description of public opinion development direction>",
    "initial_posts": [
        {{"content": "post content", "poster_type": "entity type (must be from available types)"}},
        ...
    ],
    "reasoning": "<brief explanation>"
}}"""

            system_prompt = "You are a public opinion analysis expert. Return pure JSON format. poster_type must exactly match available entity types."
        else:
            prompt = f"""基于以下模拟需求，生成事件配置。

Simulation requirement: {simulation_requirement}

{context_truncated}

## Available entity types and examples
{type_info}

## Task
Output event config JSON:
- hot_topics: list of hot-topic keywords
- narrative_direction: short description of narrative direction
- initial_posts: list of {{"content": "...", "poster_type": "<entity type>"}} — poster_type MUST be one of the available entity types above (e.g. Official/University for official statements, MediaOutlet for news, Student for student views)

Return JSON only (no markdown):
{{
    "hot_topics": ["keyword1", "keyword2", ...],
    "narrative_direction": "<short description>",
    "initial_posts": [
        {{"content": "post content", "poster_type": "entity type from available list"}},
        ...
    ],
    "reasoning": "<brief explanation>"
}}"""

        system_prompt = "You are a narrative/opinion analysis expert. Return pure JSON. poster_type must exactly match an available entity type."
            system_prompt = "你是舆论分析专家。返回纯JSON格式。注意 poster_type 必须精确匹配可用实体类型。"
        
        try:
            return self._call_llm_with_retry(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Event config LLM failed: {e}, using default")
            return {
                "hot_topics": [],
                "narrative_direction": "",
                "initial_posts": [],
                "reasoning": "Default config"
            }

    def _parse_event_config(self, result: Dict[str, Any]) -> EventConfig:
        """Parse event config result into EventConfig."""
        return EventConfig(
            initial_posts=result.get("initial_posts", []),
            scheduled_events=[],
            hot_topics=result.get("hot_topics", []),
            narrative_direction=result.get("narrative_direction", "")
        )
    
    def _assign_initial_post_agents(
        self,
        event_config: EventConfig,
        agent_configs: List[AgentActivityConfig]
    ) -> EventConfig:
        """Assign poster agents to initial posts by matching poster_type to agent entity_type."""
        if not event_config.initial_posts:
            return event_config
        
        agents_by_type: Dict[str, List[AgentActivityConfig]] = {}
        for agent in agent_configs:
            etype = agent.entity_type.lower()
            if etype not in agents_by_type:
                agents_by_type[etype] = []
            agents_by_type[etype].append(agent)
        type_aliases = {
            "official": ["official", "university", "governmentagency", "government"],
            "university": ["university", "official"],
            "mediaoutlet": ["mediaoutlet", "media"],
            "student": ["student", "person"],
            "professor": ["professor", "expert", "teacher"],
            "alumni": ["alumni", "person"],
            "organization": ["organization", "ngo", "company", "group"],
            "person": ["person", "student", "alumni"],
        }
        used_indices: Dict[str, int] = {}
        updated_posts = []
        for post in event_config.initial_posts:
            poster_type = post.get("poster_type", "").lower()
            content = post.get("content", "")
            matched_agent_id = None
            if poster_type in agents_by_type:
                agents = agents_by_type[poster_type]
                idx = used_indices.get(poster_type, 0) % len(agents)
                matched_agent_id = agents[idx].agent_id
                used_indices[poster_type] = idx + 1
            else:
                for alias_key, aliases in type_aliases.items():
                    if poster_type in aliases or alias_key == poster_type:
                        for alias in aliases:
                            if alias in agents_by_type:
                                agents = agents_by_type[alias]
                                idx = used_indices.get(alias, 0) % len(agents)
                                matched_agent_id = agents[idx].agent_id
                                used_indices[alias] = idx + 1
                                break
                    if matched_agent_id is not None:
                        break
            if matched_agent_id is None:
                logger.warning(f"No agent for poster_type '{poster_type}', using highest influence")
                if agent_configs:
                    sorted_agents = sorted(agent_configs, key=lambda a: a.influence_weight, reverse=True)
                    matched_agent_id = sorted_agents[0].agent_id
                else:
                    matched_agent_id = 0
            
            updated_posts.append({
                "content": content,
                "poster_type": post.get("poster_type", "Unknown"),
                "poster_agent_id": matched_agent_id
            })
            
            logger.info(f"Initial post assigned: poster_type='{poster_type}' -> agent_id={matched_agent_id}")
        
        event_config.initial_posts = updated_posts
        return event_config
    
    def _generate_agent_configs_batch(
        self,
        context: str,
        entities: List[EntityNode],
        start_idx: int,
        simulation_requirement: str
    ) -> List[AgentActivityConfig]:
        """Generate agent configs for a batch of entities (LLM or rule-based fallback)."""
        entity_list = []
        summary_len = self.AGENT_SUMMARY_LENGTH
        for i, e in enumerate(entities):
            entity_list.append({
                "agent_id": start_idx + i,
                "entity_name": e.name,
                "entity_type": e.get_entity_type() or "Unknown",
                "summary": e.summary[:summary_len] if e.summary else ""
            })
        
        prompt = f"""Generate social media activity config for each entity below.
        if self.language == 'en':
            prompt = f"""Based on the following information, generate social media activity configuration for each entity.

Simulation Requirement: {simulation_requirement}

## Entity List
```json
{json.dumps(entity_list, ensure_ascii=False, indent=2)}
```

## Task
Generate activity configuration for each entity. Guidelines:
- **Adjust timing to match the target population's daily patterns**
- **Official institutions** (University/GovernmentAgency): Low activity (0.1-0.3), work hours (9-17), slow response (60-240 min), high influence (2.5-3.0)
- **Media** (MediaOutlet): Medium activity (0.4-0.6), all day (8-23), fast response (5-30 min), high influence (2.0-2.5)
- **Individuals** (Student/Person/Alumni): High activity (0.6-0.9), mainly evening (18-23), fast response (1-15 min), low influence (0.8-1.2)
- **Public figures/Experts**: Medium activity (0.4-0.6), medium-high influence (1.5-2.0)

Return JSON format (no markdown):
{{
    "agent_configs": [
        {{
            "agent_id": <must match input>,
            "activity_level": <0.0-1.0>,
            "posts_per_hour": <posting frequency>,
            "comments_per_hour": <comment frequency>,
            "active_hours": [<list of active hours>],
            "response_delay_min": <min response delay in minutes>,
            "response_delay_max": <max response delay in minutes>,
            "sentiment_bias": <-1.0 to 1.0>,
            "stance": "<supportive/opposing/neutral/observer>",
            "influence_weight": <influence weight>
        }},
        ...
    ]
}}"""

            system_prompt = "You are a social media behavior analysis expert. Return pure JSON."
        else:
            prompt = f"""基于以下信息，为每个实体生成社交媒体活动配置。

Simulation requirement: {simulation_requirement}

## Entity list
```json
{json.dumps(entity_list, ensure_ascii=False, indent=2)}
```

## Task
For each entity output an activity config. Guidelines (China timezone):
- 0-5 low activity, 19-22 peak.
- Official (University/GovernmentAgency): low activity (0.1-0.3), work hours (9-17), slow response (60-240 min), high influence (2.5-3.0).
- Media (MediaOutlet): medium (0.4-0.6), all-day (8-23), fast response (5-30 min), high influence (2.0-2.5).
- Individuals (Student/Person/Alumni): high (0.6-0.9), evening (18-23), fast (1-15 min), low influence (0.8-1.2).
- Public figures/experts: medium (0.4-0.6), influence (1.5-2.0).

Return JSON only (no markdown):
{{
    "agent_configs": [
        {{
            "agent_id": <must match input>,
            "activity_level": <0.0-1.0>,
            "posts_per_hour": <float>,
            "comments_per_hour": <float>,
            "active_hours": [<hour list>],
            "response_delay_min": <int>,
            "response_delay_max": <int>,
            "sentiment_bias": <-1.0 to 1.0>,
            "stance": "supportive|opposing|neutral|observer",
            "influence_weight": <float>
        }},
        ...
    ]
}}"""

        system_prompt = "You are a social media behavior expert. Return pure JSON; configs should follow China timezone activity patterns."
            system_prompt = "你是社交媒体行为分析专家。返回纯JSON，配置需符合中国人作息习惯。"
        
        try:
            result = self._call_llm_with_retry(prompt, system_prompt)
            llm_configs = {cfg["agent_id"]: cfg for cfg in result.get("agent_configs", [])}
        except Exception as e:
            logger.warning(f"Agent batch LLM failed: {e}, using rule-based generation")
            llm_configs = {}
        configs = []
        for i, entity in enumerate(entities):
            agent_id = start_idx + i
            cfg = llm_configs.get(agent_id, {})
            if not cfg:
                cfg = self._generate_agent_config_by_rule(entity)
            
            config = AgentActivityConfig(
                agent_id=agent_id,
                entity_uuid=entity.uuid,
                entity_name=entity.name,
                entity_type=entity.get_entity_type() or "Unknown",
                activity_level=cfg.get("activity_level", 0.5),
                posts_per_hour=cfg.get("posts_per_hour", 0.5),
                comments_per_hour=cfg.get("comments_per_hour", 1.0),
                active_hours=cfg.get("active_hours", list(range(9, 23))),
                response_delay_min=cfg.get("response_delay_min", 5),
                response_delay_max=cfg.get("response_delay_max", 60),
                sentiment_bias=cfg.get("sentiment_bias", 0.0),
                stance=cfg.get("stance", "neutral"),
                influence_weight=cfg.get("influence_weight", 1.0)
            )
            configs.append(config)
        
        return configs
    
    def _generate_agent_config_by_rule(self, entity: EntityNode) -> Dict[str, Any]:
        """Rule-based fallback for a single agent config (China timezone)."""
        entity_type = (entity.get_entity_type() or "Unknown").lower()
        if entity_type in ["university", "governmentagency", "ngo"]:
            return {
                "activity_level": 0.2,
                "posts_per_hour": 0.1,
                "comments_per_hour": 0.05,
                "active_hours": list(range(9, 18)),  # 9:00-17:59
                "response_delay_min": 60,
                "response_delay_max": 240,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 3.0
            }
        elif entity_type in ["mediaoutlet"]:
            return {
                "activity_level": 0.5,
                "posts_per_hour": 0.8,
                "comments_per_hour": 0.3,
                "active_hours": list(range(7, 24)),  # 7:00-23:59
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "observer",
                "influence_weight": 2.5
            }
        elif entity_type in ["professor", "expert", "official"]:
            return {
                "activity_level": 0.4,
                "posts_per_hour": 0.3,
                "comments_per_hour": 0.5,
                "active_hours": list(range(8, 22)),  # 8:00-21:59
                "response_delay_min": 15,
                "response_delay_max": 90,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 2.0
            }
        elif entity_type in ["student"]:
            return {
                "activity_level": 0.8,
                "posts_per_hour": 0.6,
                "comments_per_hour": 1.5,
                "active_hours": [8, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],
                "response_delay_min": 1,
                "response_delay_max": 15,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 0.8
            }
        elif entity_type in ["alumni"]:
            return {
                "activity_level": 0.6,
                "posts_per_hour": 0.4,
                "comments_per_hour": 0.8,
                "active_hours": [12, 13, 19, 20, 21, 22, 23],
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
        else:
            return {
                "activity_level": 0.7,
                "posts_per_hour": 0.5,
                "comments_per_hour": 1.2,
                "active_hours": [9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],
                "response_delay_min": 2,
                "response_delay_max": 20,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
    

