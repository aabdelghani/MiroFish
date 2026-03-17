"""
图谱记忆更新服务
将模拟中的Agent活动动态更新到图谱中
支持 Zep Cloud 和 Graphiti 两种模式
Zep graph memory updater: push simulation agent activities into the Zep graph.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty

from ..config import Config
from ..utils.logger import get_logger
from .kg_adapter import get_knowledge_graph_adapter
from ..utils.error_messages import get_error_message

logger = get_logger('mirofish.zep_graph_memory_updater')

# Activity descriptions default locale (no Flask request context in background threads)
_ACTIVITY_LOCALE = 'zh'


@dataclass
class AgentActivity:
    """Single agent activity record."""
    platform: str
    agent_id: int
    agent_name: str
    action_type: str
    action_args: Dict[str, Any]
    round_num: int
    timestamp: str

    def to_episode_text(self) -> str:
        """Convert activity to natural-language text for Zep (entity/relation extraction). No simulation prefix."""
        action_descriptions = {
            "CREATE_POST": self._describe_create_post,
            "LIKE_POST": self._describe_like_post,
            "DISLIKE_POST": self._describe_dislike_post,
            "REPOST": self._describe_repost,
            "QUOTE_POST": self._describe_quote_post,
            "FOLLOW": self._describe_follow,
            "CREATE_COMMENT": self._describe_create_comment,
            "LIKE_COMMENT": self._describe_like_comment,
            "DISLIKE_COMMENT": self._describe_dislike_comment,
            "SEARCH_POSTS": self._describe_search,
            "SEARCH_USER": self._describe_search_user,
            "MUTE": self._describe_mute,
        }
        
        describe_func = action_descriptions.get(self.action_type, self._describe_generic)
        description = describe_func()
        return f"{self.agent_name}: {description}"

    def _describe_create_post(self) -> str:
        content = self.action_args.get("content", "")
        if content:
            return f"Posted: \"{content}\""
        return "Posted a post"
            return get_error_message('activity_create_post', _ACTIVITY_LOCALE).format(content=content)
        return get_error_message('activity_create_post_no_content', _ACTIVITY_LOCALE)

    def _describe_like_post(self) -> str:
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        if post_content and post_author:
            return f"Liked {post_author}'s post: \"{post_content}\""
        elif post_content:
            return f"Liked a post: \"{post_content}\""
        elif post_author:
            return f"Liked one of {post_author}'s posts"
        return "Liked a post"

        if post_content and post_author:
            return get_error_message('activity_like_post_full', _ACTIVITY_LOCALE).format(author=post_author, content=post_content)
        elif post_content:
            return get_error_message('activity_like_post_content', _ACTIVITY_LOCALE).format(content=post_content)
        elif post_author:
            return get_error_message('activity_like_post_author', _ACTIVITY_LOCALE).format(author=post_author)
        return get_error_message('activity_like_post', _ACTIVITY_LOCALE)

    def _describe_dislike_post(self) -> str:
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        if post_content and post_author:
            return f"Disliked {post_author}'s post: \"{post_content}\""
        elif post_content:
            return f"Disliked a post: \"{post_content}\""
        elif post_author:
            return f"Disliked one of {post_author}'s posts"
        return "Disliked a post"

        if post_content and post_author:
            return get_error_message('activity_dislike_post_full', _ACTIVITY_LOCALE).format(author=post_author, content=post_content)
        elif post_content:
            return get_error_message('activity_dislike_post_content', _ACTIVITY_LOCALE).format(content=post_content)
        elif post_author:
            return get_error_message('activity_dislike_post_author', _ACTIVITY_LOCALE).format(author=post_author)
        return get_error_message('activity_dislike_post', _ACTIVITY_LOCALE)

    def _describe_repost(self) -> str:
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        if original_content and original_author:
            return f"Reposted {original_author}'s post: \"{original_content}\""
        elif original_content:
            return f"Reposted a post: \"{original_content}\""
        elif original_author:
            return f"Reposted one of {original_author}'s posts"
        return "Reposted a post"

        if original_content and original_author:
            return get_error_message('activity_repost_full', _ACTIVITY_LOCALE).format(author=original_author, content=original_content)
        elif original_content:
            return get_error_message('activity_repost_content', _ACTIVITY_LOCALE).format(content=original_content)
        elif original_author:
            return get_error_message('activity_repost_author', _ACTIVITY_LOCALE).format(author=original_author)
        return get_error_message('activity_repost', _ACTIVITY_LOCALE)

    def _describe_quote_post(self) -> str:
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        quote_content = self.action_args.get("quote_content", "") or self.action_args.get("content", "")
        if original_content and original_author:
            base = f"Quoted {original_author}'s post \"{original_content}\""
        elif original_content:
            base = f"Quoted a post \"{original_content}\""
        elif original_author:
            base = f"Quoted one of {original_author}'s posts"
        else:
            base = "Quoted a post"
        if quote_content:
            base += f", commenting: \"{quote_content}\""

        if original_content and original_author:
            base = get_error_message('activity_quote_full', _ACTIVITY_LOCALE).format(author=original_author, content=original_content)
        elif original_content:
            base = get_error_message('activity_quote_content', _ACTIVITY_LOCALE).format(content=original_content)
        elif original_author:
            base = get_error_message('activity_quote_author', _ACTIVITY_LOCALE).format(author=original_author)
        else:
            base = get_error_message('activity_quote', _ACTIVITY_LOCALE)

        if quote_content:
            base += get_error_message('activity_quote_comment', _ACTIVITY_LOCALE).format(comment=quote_content)
        return base

    def _describe_follow(self) -> str:
        target_user_name = self.action_args.get("target_user_name", "")
        if target_user_name:
            return f"Followed user \"{target_user_name}\""
        return "Followed a user"

        if target_user_name:
            return get_error_message('activity_follow_user', _ACTIVITY_LOCALE).format(user=target_user_name)
        return get_error_message('activity_follow', _ACTIVITY_LOCALE)

    def _describe_create_comment(self) -> str:
        content = self.action_args.get("content", "")
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        if content:
            if post_content and post_author:
                return f"Commented on {post_author}'s post \"{post_content}\": \"{content}\""
            elif post_content:
                return f"Commented on post \"{post_content}\": \"{content}\""
            elif post_author:
                return f"Commented on {post_author}'s post: \"{content}\""
            return f"Commented: \"{content}\""
        return "Posted a comment"

        if content:
            if post_content and post_author:
                return get_error_message('activity_comment_full', _ACTIVITY_LOCALE).format(author=post_author, post=post_content, content=content)
            elif post_content:
                return get_error_message('activity_comment_post', _ACTIVITY_LOCALE).format(post=post_content, content=content)
            elif post_author:
                return get_error_message('activity_comment_author', _ACTIVITY_LOCALE).format(author=post_author, content=content)
            return get_error_message('activity_comment_only', _ACTIVITY_LOCALE).format(content=content)
        return get_error_message('activity_comment', _ACTIVITY_LOCALE)

    def _describe_like_comment(self) -> str:
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        if comment_content and comment_author:
            return f"Liked {comment_author}'s comment: \"{comment_content}\""
        elif comment_content:
            return f"Liked a comment: \"{comment_content}\""
        elif comment_author:
            return f"Liked one of {comment_author}'s comments"
        return "Liked a comment"

        if comment_content and comment_author:
            return get_error_message('activity_like_comment_full', _ACTIVITY_LOCALE).format(author=comment_author, content=comment_content)
        elif comment_content:
            return get_error_message('activity_like_comment_content', _ACTIVITY_LOCALE).format(content=comment_content)
        elif comment_author:
            return get_error_message('activity_like_comment_author', _ACTIVITY_LOCALE).format(author=comment_author)
        return get_error_message('activity_like_comment', _ACTIVITY_LOCALE)

    def _describe_dislike_comment(self) -> str:
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        if comment_content and comment_author:
            return f"Disliked {comment_author}'s comment: \"{comment_content}\""
        elif comment_content:
            return f"Disliked a comment: \"{comment_content}\""
        elif comment_author:
            return f"Disliked one of {comment_author}'s comments"
        return "Disliked a comment"

        if comment_content and comment_author:
            return get_error_message('activity_dislike_comment_full', _ACTIVITY_LOCALE).format(author=comment_author, content=comment_content)
        elif comment_content:
            return get_error_message('activity_dislike_comment_content', _ACTIVITY_LOCALE).format(content=comment_content)
        elif comment_author:
            return get_error_message('activity_dislike_comment_author', _ACTIVITY_LOCALE).format(author=comment_author)
        return get_error_message('activity_dislike_comment', _ACTIVITY_LOCALE)

    def _describe_search(self) -> str:
        query = self.action_args.get("query", "") or self.action_args.get("keyword", "")
        return f"Searched for \"{query}\"" if query else "Performed a search"
        if query:
            return get_error_message('activity_search', _ACTIVITY_LOCALE).format(query=query)
        return get_error_message('activity_search_generic', _ACTIVITY_LOCALE)

    def _describe_search_user(self) -> str:
        query = self.action_args.get("query", "") or self.action_args.get("username", "")
        return f"Searched for user \"{query}\"" if query else "Searched for users"
        if query:
            return get_error_message('activity_search_user', _ACTIVITY_LOCALE).format(query=query)
        return get_error_message('activity_search_user_generic', _ACTIVITY_LOCALE)

    def _describe_mute(self) -> str:
        target_user_name = self.action_args.get("target_user_name", "")
        if target_user_name:
            return f"Muted user \"{target_user_name}\""
        return "Muted a user"

    def _describe_generic(self) -> str:
        return f"Performed {self.action_type}"

        if target_user_name:
            return get_error_message('activity_mute_user', _ACTIVITY_LOCALE).format(user=target_user_name)
        return get_error_message('activity_mute', _ACTIVITY_LOCALE)

    def _describe_generic(self) -> str:
        # 对于未知的动作类型，生成通用描述
        return get_error_message('activity_generic', _ACTIVITY_LOCALE).format(action=self.action_type)


class ZepGraphMemoryUpdater:
    """
    图谱记忆更新器

    监控模拟的actions日志文件，将新的agent活动实时更新到图谱中。
    按平台分组，每累积BATCH_SIZE条活动后批量发送。

    所有有意义的行为都会被更新到图谱，action_args中会包含完整的上下文信息：
    - 点赞/踩的帖子原文
    - 转发/引用的帖子原文
    - 关注/屏蔽的用户名
    - 点赞/踩的评论原文
    """

    # 批量发送大小（每个平台累积多少条后发送）
    BATCH_SIZE = 5

    # 平台名称映射（用于控制台显示）
    Zep graph memory updater.

    Watches simulation action logs and pushes new agent activities into the Zep graph.
    Groups by platform; when a platform buffer reaches BATCH_SIZE, sends a batch to Zep.

    All meaningful actions are sent; action_args include full context (post/comment text,
    usernames for like/dislike, repost/quote, follow/mute, etc.).
    """

    BATCH_SIZE = 5
    PLATFORM_DISPLAY_NAMES = {
        "twitter": "World 1",
        "reddit": "World 2",
    }

    # 发送间隔（秒），避免请求过快
    SEND_INTERVAL = 0.5

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒

    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """
        初始化更新器

        Args:
            graph_id: 图谱ID
            api_key: 保留参数（兼容旧代码）
        """
        self.graph_id = graph_id
        self.api_key = api_key  # 保留参数兼容性

        # 使用适配器
        self.kg = get_knowledge_graph_adapter()
        
        # 活动队列
    SEND_INTERVAL = 0.5
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """
        Initialize the updater.

        Args:
            graph_id: Zep graph ID.
            api_key: Zep API key (optional; default from config).
        """
        self.graph_id = graph_id
        self.api_key = api_key or Config.ZEP_API_KEY

        if not self.api_key:
            raise ValueError("ZEP_API_KEY is not set")

        self.client = Zep(api_key=self.api_key)
        self._activity_queue: Queue = Queue()
        self._platform_buffers: Dict[str, List[AgentActivity]] = {
            "twitter": [],
            "reddit": [],
        }
        self._buffer_lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._total_activities = 0
        self._total_sent = 0
        self._total_items_sent = 0
        self._failed_count = 0
        self._skipped_count = 0

        logger.info(
            f"ZepGraphMemoryUpdater initialized: graph_id={graph_id}, batch_size={self.BATCH_SIZE}"
        )
        
        # 统计
        self._total_activities = 0  # 实际添加到队列的活动数
        self._total_sent = 0        # 成功发送到Zep的批次数
        self._total_items_sent = 0  # 成功发送到Zep的活动条数
        self._failed_count = 0      # 发送失败的批次数
        self._skipped_count = 0     # 被过滤跳过的活动数（DO_NOTHING）
        
        logger.info(f"ZepGraphMemoryUpdater initialized: graph_id={graph_id}, batch_size={self.BATCH_SIZE}")
    
    def _get_platform_display_name(self, platform: str) -> str:
        """Return display name for the platform."""
        return self.PLATFORM_DISPLAY_NAMES.get(platform.lower(), platform)

    def start(self):
        """Start the background worker thread."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"ZepMemoryUpdater-{self.graph_id[:8]}",
        )
        self._worker_thread.start()
        logger.info(f"ZepGraphMemoryUpdater started: graph_id={self.graph_id}")

    
    def stop(self):
        """Stop the background worker and flush remaining activities."""
        self._running = False
        self._flush_remaining()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        logger.info(
            f"ZepGraphMemoryUpdater stopped: graph_id={self.graph_id}, "
            f"total_activities={self._total_activities}, "
            f"batches_sent={self._total_sent}, "
            f"items_sent={self._total_items_sent}, "
            f"failed={self._failed_count}, "
            f"skipped={self._skipped_count}"
        )
        
        logger.info(f"ZepGraphMemoryUpdater stopped: graph_id={self.graph_id}, "
                   f"total_activities={self._total_activities}, "
                   f"batches_sent={self._total_sent}, "
                   f"items_sent={self._total_items_sent}, "
                   f"failed={self._failed_count}, "
                   f"skipped={self._skipped_count}")
    
    def add_activity(self, activity: AgentActivity):
        """
        Enqueue one agent activity.

        Meaningful actions (CREATE_POST, CREATE_COMMENT, QUOTE_POST, SEARCH_POSTS,
        SEARCH_USER, LIKE_POST/DISLIKE_POST, REPOST, FOLLOW, MUTE, LIKE_COMMENT/DISLIKE_COMMENT)
        are queued; action_args hold full context (post/comment text, usernames, etc.).

        Args:
            activity: AgentActivity instance.
        """
        if activity.action_type == "DO_NOTHING":
            self._skipped_count += 1
            return
        self._activity_queue.put(activity)
        self._total_activities += 1
        logger.debug(
            f"Added activity to Zep queue: {activity.agent_name} - {activity.action_type}"
        )

    def add_activity_from_dict(self, data: Dict[str, Any], platform: str):
        """
        Add activity from a dict (e.g. parsed from actions.jsonl).

        Args:
            data: Dict with agent_id, agent_name, action_type, action_args, round, timestamp.
            platform: twitter or reddit.
        """
        if "event_type" in data:
            return
        
        activity = AgentActivity(
            platform=platform,
            agent_id=data.get("agent_id", 0),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            action_args=data.get("action_args", {}),
            round_num=data.get("round", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
        
        self.add_activity(activity)
    
    def _worker_loop(self):
        """Background loop: drain queue, buffer by platform, send batches to Zep."""
        while self._running or not self._activity_queue.empty():
            try:
                try:
                    activity = self._activity_queue.get(timeout=1)
                    platform = activity.platform.lower()
                    with self._buffer_lock:
                        if platform not in self._platform_buffers:
                            self._platform_buffers[platform] = []
                        self._platform_buffers[platform].append(activity)
                        if len(self._platform_buffers[platform]) >= self.BATCH_SIZE:
                            batch = self._platform_buffers[platform][: self.BATCH_SIZE]
                            self._platform_buffers[platform] = self._platform_buffers[
                                platform
                            ][self.BATCH_SIZE :]
                            self._send_batch_activities(batch, platform)
                            time.sleep(self.SEND_INTERVAL)
                except Empty:
                    pass
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1)
    
    def _send_batch_activities(self, activities: List[AgentActivity], platform: str):
        """
        Send a batch of activities to the Zep graph as one combined text.

        Args:
            activities: List of AgentActivity.
            platform: Platform name (twitter/reddit).
        """
        if not activities:
            return
        episode_texts = [activity.to_episode_text() for activity in activities]
        combined_text = "\n".join(episode_texts)

        # 带重试的发送
        for attempt in range(self.MAX_RETRIES):
            try:
                self.kg.add_episode(
                    graph_id=self.graph_id,
                    text=combined_text
                )

                    type="text",
                    data=combined_text,
                )
                self._total_sent += 1
                self._total_items_sent += len(activities)
                display_name = self._get_platform_display_name(platform)
                logger.info(
                    f"Sent batch of {len(activities)} {display_name} activities to graph {self.graph_id}"
                )
                logger.debug(f"Batch preview: {combined_text[:200]}...")
                logger.info(get_error_message('zep_batch_sent', _ACTIVITY_LOCALE).format(count=len(activities), platform=display_name, graph_id=self.graph_id))
                logger.debug(f"批量内容预览: {combined_text[:200]}...")
                return

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"批量发送到图谱失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"批量发送到图谱失败，已重试{self.MAX_RETRIES}次: {e}")
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Zep batch send failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                    )
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(
                        f"Zep batch send failed after {self.MAX_RETRIES} retries: {e}"
                    )
                    self._failed_count += 1
    
    def _flush_remaining(self):
        """Flush queue into buffers, then send all remaining buffered activities."""
        while not self._activity_queue.empty():
            try:
                activity = self._activity_queue.get_nowait()
                platform = activity.platform.lower()
                with self._buffer_lock:
                    if platform not in self._platform_buffers:
                        self._platform_buffers[platform] = []
                    self._platform_buffers[platform].append(activity)
            except Empty:
                break
        with self._buffer_lock:
            for platform, buffer in self._platform_buffers.items():
                if buffer:
                    display_name = self._get_platform_display_name(platform)
                    logger.info(
                        f"Flushing {len(buffer)} remaining {display_name} activities"
                    )
                    logger.info(get_error_message('zep_flush_remaining', _ACTIVITY_LOCALE).format(platform=display_name, count=len(buffer)))
                    self._send_batch_activities(buffer, platform)
            for platform in self._platform_buffers:
                self._platform_buffers[platform] = []

    def get_stats(self) -> Dict[str, Any]:
        """Return updater statistics."""
        with self._buffer_lock:
            buffer_sizes = {p: len(b) for p, b in self._platform_buffers.items()}
        return {
            "graph_id": self.graph_id,
            "batch_size": self.BATCH_SIZE,
            "total_activities": self._total_activities,
            "batches_sent": self._total_sent,
            "items_sent": self._total_items_sent,
            "failed_count": self._failed_count,
            "skipped_count": self._skipped_count,
            "queue_size": self._activity_queue.qsize(),
            "buffer_sizes": buffer_sizes,
            "running": self._running,
        }


class ZepGraphMemoryManager:
    """
    Manages Zep graph memory updaters per simulation.

    Each simulation can have its own updater instance.
    """

    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}
    _lock = threading.Lock()

    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        """
        Create a graph memory updater for a simulation.

        Args:
            simulation_id: Simulation ID.
            graph_id: Zep graph ID.

        Returns:
            ZepGraphMemoryUpdater instance.
        """
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
            updater = ZepGraphMemoryUpdater(graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            logger.info(
                f"Created graph memory updater: simulation_id={simulation_id}, graph_id={graph_id}"
            )
            
            logger.info(f"Graph memory updater created: simulation_id={simulation_id}, graph_id={graph_id}")
            return updater

    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        """Return the updater for the given simulation, or None."""
        return cls._updaters.get(simulation_id)

    @classmethod
    def stop_updater(cls, simulation_id: str):
        """Stop and remove the updater for the given simulation."""
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f"Stopped graph memory updater: simulation_id={simulation_id}")

                logger.info(f"Graph memory updater stopped: simulation_id={simulation_id}")
    
    # 防止 stop_all 重复调用的标志
    _stop_all_done = False

    @classmethod
    def stop_all(cls):
        """Stop all updaters (idempotent)."""
        if cls._stop_all_done:
            return
        cls._stop_all_done = True
        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as e:
                        logger.error(
                            f"Failed to stop updater: simulation_id={simulation_id}, error={e}"
                        )
                cls._updaters.clear()
            logger.info("Stopped all graph memory updaters")

            logger.info("All graph memory updaters stopped")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Return stats for all updaters."""
        return {
            sim_id: updater.get_stats()
            for sim_id, updater in cls._updaters.items()
        }
