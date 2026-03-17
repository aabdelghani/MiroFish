"""
LLM client wrapper.
Uses OpenAI-compatible API format.
LLM客户端封装
统一使用OpenAI格式调用，兼容 MiniMax 等 OpenAI 兼容 API

Provides a thin wrapper around the OpenAI-compatible chat API.
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


def _is_minimax(model: str, base_url: str) -> bool:
    """检测当前是否使用 MiniMax 模型"""
    model_lower = (model or "").lower()
    url_lower = (base_url or "").lower()
    return "minimax" in model_lower or "minimax" in url_lower


def _clamp_temperature(temperature: float, model: str, base_url: str) -> float:
    """MiniMax 要求 temperature 在 (0.0, 1.0] 之间，不能为 0"""
    if _is_minimax(model, base_url) and temperature <= 0:
        return 0.01
    return temperature


def parse_json_from_response(content: str) -> Any:
    """从 LLM 响应中解析 JSON，支持多种格式"""
    trimmed = content.strip()

    # 1. 直接解析
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        pass

    # 2. 提取 markdown code block
    code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', trimmed)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. 提取 { } 或 [ ]
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', trimmed)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"LLM返回的JSON格式无效: {trimmed}")


class LLMClient:
    """LLM client."""
    """Lightweight LLM client."""
    
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")
        
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    @property
    def is_minimax(self) -> bool:
        """检测当前是否使用 MiniMax 模型"""
        return _is_minimax(self.model, self.base_url)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数（默认使用配置中的 LLM_MAX_TOKENS）
            response_format: 响应格式（如JSON模式）
        Send a chat completion request.

        Args:
        Send a chat completion request.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens to generate.
            response_format: Optional OpenAI response_format (e.g. JSON mode).

        Returns:
            The model response text.
        """
        # 如果未指定 max_tokens，使用配置中的默认值
        effective_max_tokens = max_tokens if max_tokens is not None else Config.LLM_MAX_TOKENS

        """Send chat request. Args: messages, temperature, max_tokens, response_format. Returns response text."""
        temperature = _clamp_temperature(temperature, self.model, self.base_url)

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
        }

        # MiniMax 不支持 response_format，改用 prompt 引导 JSON 输出
        if response_format and self.is_minimax:
            messages = _inject_json_instruction(messages)
        elif response_format:
            kwargs["response_format"] = response_format
        
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # 如果是因为 response_format 导致的错误，尝试不使用 response_format 重试
            error_str = str(e).lower()
            if response_format and ("response_format" in error_str or 
                                    "json_object" in error_str or
                                    "unsupported" in error_str or
                                    "400" in error_str or
                                    "500" in error_str):
                # 移除 response_format 后重试
                kwargs.pop("response_format", None)
                response = self.client.chat.completions.create(**kwargs)
            else:
                raise
        

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # Some models (e.g. MiniMax M2.5) include <think>...</think> in content; strip it
        # Some models (e.g. MiniMax M2.5) include <think>...</think> content that should be stripped
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数（默认使用配置中的 LLM_MAX_TOKENS）
            max_tokens: 最大token数
        Send a chat completion request and parse the response as JSON.

        Args:
        Send a chat completion request and parse the response as JSON.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            Parsed JSON object.
        """
        try:
            # 首先尝试使用 response_format 参数（OpenAI 原生支持）
            response = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            # 如果失败，尝试不使用 response_format 重试
            error_str = str(e).lower()
            if ("response_format" in error_str or 
                "json_object" in error_str or
                "unsupported" in error_str or
                "400" in error_str or
                "500" in error_str):
                # 不使用 response_format，依赖系统提示词中的 JSON 格式要求
                response = self.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                raise
        
        # 清理markdown代码块标记
        """Send chat request and return parsed JSON. Args: messages, temperature, max_tokens."""
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Strip markdown code block markers
        # Strip optional surrounding Markdown code fences
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM返回的JSON格式无效: {cleaned_response}")
            raise ValueError(f"LLM returned invalid JSON: {cleaned_response}")
        return parse_json_from_response(response)


def _inject_json_instruction(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """在消息列表中注入 JSON 输出指令（用于不支持 response_format 的模型）"""
    json_hint = "\n\nYou must respond with valid JSON only. No markdown, no explanation, no extra text."
    messages = [msg.copy() for msg in messages]
    # 优先追加到 system 消息
    for msg in messages:
        if msg.get("role") == "system":
            msg["content"] = msg["content"] + json_hint
            return messages
    # 如果没有 system 消息，在开头插入一条
    messages.insert(0, {"role": "system", "content": json_hint.strip()})
    return messages
            raise ValueError(f"Invalid JSON returned by LLM: {cleaned_response}")

