"""
Dynamic Model Client - Provider-agnostic AI model client
Supports multiple AI providers with minimal configuration
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion synchronously."""
        pass

    @abstractmethod
    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion asynchronously."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        pass

class DynamicModelClient:
    """
    Dynamic model client that automatically detects and uses the appropriate provider
    based on MODEL_AI configuration.
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        # Use config values if not provided
        self.model = model or getattr(settings, 'MODEL_AI', 'gemini-1.5-flash')
        self.api_key = api_key or getattr(settings, 'MODEL_AI_KEY', '')
        self.base_url = base_url or getattr(settings, 'MODEL_AI_URL', '')

        # Detect provider and initialize
        self.provider_type = self._detect_provider()
        self.provider = self._create_provider()

        logger.info(f"Initialized {self.provider_type} provider for model {self.model}")

    def _detect_provider(self) -> str:
        """Detect provider based on model name and configuration."""
        model_lower = self.model.lower()

        # OpenAI models
        if model_lower.startswith(('gpt-', 'chatgpt')):
            return 'openai'

        # Gemini models
        elif model_lower.startswith('gemini'):
            return 'gemini'

        # Local/Ollama models (contain colon)
        elif ':' in model_lower:
            return 'ollama'

        # Anthropic Claude models
        elif model_lower.startswith('claude'):
            return 'anthropic'

        # Cerebras models
        elif model_lower.startswith(('qwen', 'llama', 'mistral', 'gpt-oss')):
            return 'cerebras'

        # Default to generic API if URL is provided
        elif self.base_url and self.base_url != 'use if URL model AI':
            return 'generic_api'

        # Default fallback
        else:
            return 'gemini'

    def _create_provider(self) -> ModelProvider:
        """Create the appropriate provider instance."""
        if self.provider_type == 'openai':
            return OpenAIProvider(self.api_key, self.model, self.base_url)
        elif self.provider_type == 'gemini':
            return GeminiProvider(self.api_key, self.model)
        elif self.provider_type == 'ollama':
            return OllamaProvider(self.model, self.base_url)
        elif self.provider_type == 'anthropic':
            return AnthropicProvider(self.api_key, self.model)
        elif self.provider_type == 'cerebras':
            return CerebrasProvider(self.api_key, self.model)
        elif self.provider_type == 'generic_api':
            return GenericAPIProvider(self.api_key, self.model, self.base_url)
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion synchronously."""
        return self.provider.generate(messages, **kwargs)

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion asynchronously."""
        return await self.provider.generate_async(messages, **kwargs)

    def generate_with_retry(self, messages: List[Dict[str, str]],
                           max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """Generate with retry logic."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.generate(messages, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Generation failed after {max_retries} attempts: {e}")
        raise last_error

    async def generate_with_retry_async(self, messages: List[Dict[str, str]],
                                       max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """Generate with retry logic asynchronously."""
        import asyncio
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.generate_async(messages, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Async generation attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Async generation failed after {max_retries} attempts: {e}")
        raise last_error

    def generate_json(self, messages: Optional[List[Dict[str, str]]] = None,
                     prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate JSON response."""
        if messages is None and prompt is not None:
            messages = [{"role": "user", "content": prompt}]
        elif messages is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided")

        # Add JSON instruction
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += "\n\nRespond with valid JSON only."

        response = self.generate_with_retry(messages, **kwargs)
        content = response.get("content", "").strip()

        try:
            # Try parsing directly first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            extracted_json = self._extract_json_from_markdown(content)
            if extracted_json:
                try:
                    return json.loads(extracted_json)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted JSON: {e}")
            else:
                logger.error(f"Failed to parse JSON: content not in expected format")
            return {"error": "Invalid JSON response", "raw_content": content}

    async def generate_json_async(self, messages: Optional[List[Dict[str, str]]] = None,
                                 prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate JSON response asynchronously."""
        if messages is None and prompt is not None:
            messages = [{"role": "user", "content": prompt}]
        elif messages is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided")

        # Add JSON instruction
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += "\n\nRespond with valid JSON only."

        response = await self.generate_with_retry_async(messages, **kwargs)
        content = response.get("content", "").strip()

        try:
            # Try parsing directly first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            extracted_json = self._extract_json_from_markdown(content)
            if extracted_json:
                try:
                    return json.loads(extracted_json)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted JSON: {e}")
            else:
                logger.error(f"Failed to parse JSON: content not in expected format")
            return {"error": "Invalid JSON response", "raw_content": content}

    def _extract_json_from_markdown(self, content: str) -> Optional[str]:
        """Extract JSON content from markdown code blocks."""
        import re
        
        # Pattern to match ```json...``` or ```...``` code blocks
        patterns = [
            r'```json\s*\n([\s\S]*?)\n```',  # ```json ... ```
            r'```\s*\n([\s\S]*?)\n```',      # ``` ... ```
            r'`([^`]+)`',                    # `...` single backticks
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                # Try each match to see if it's valid JSON
                for match in matches:
                    cleaned = match.strip()
                    if cleaned.startswith('{') and cleaned.endswith('}'):
                        return cleaned
        
        # If no code blocks found, check if the content itself looks like JSON
        cleaned_content = content.strip()
        if cleaned_content.startswith('{') and cleaned_content.endswith('}'):
            return cleaned_content
            
        return None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return self.provider.get_model_info()

    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content from a simple prompt (compatibility method)."""
        messages = [{"role": "user", "content": prompt}]
        response = await self.generate_async(messages, **kwargs)
        return response.get("content", "")

class OpenAIProvider(ModelProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        self.model = model

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        response = self.client.chat.completions.create(**params)
        end_time = time.time()

        message = response.choices[0].message
        return {
            "content": message.content,
            "role": message.role,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        response = await self.async_client.chat.completions.create(**params)
        end_time = time.time()

        message = response.choices[0].message
        return {
            "content": message.content,
            "role": message.role,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.model,
            "max_tokens": 128000,
            "supports_functions": True,
            "supports_streaming": True
        }

class GeminiProvider(ModelProvider):
    """Google Gemini provider implementation."""

    def __init__(self, api_key: str, model: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name=model)
        except ImportError:
            raise ImportError("Google Generative AI library not available. Install with: pip install google-generativeai")
        self.model = model

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert messages to Gemini format."""
        system_instruction = ""
        chat_messages = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                chat_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                chat_messages.append({"role": "model", "parts": [content]})

        return system_instruction, chat_messages

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        import google.generativeai as genai

        start_time = time.time()
        system_instruction, chat_messages = self._convert_messages(messages)

        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.1),
            max_output_tokens=kwargs.get("max_tokens", 2000),
        )

        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction
            )
        else:
            model = genai.GenerativeModel(model_name=self.model)

        if len(chat_messages) == 1 and chat_messages[0]["role"] == "user":
            response = model.generate_content(
                chat_messages[0]["parts"][0],
                generation_config=generation_config
            )
        else:
            chat = model.start_chat(history=chat_messages[:-1])
            response = chat.send_message(
                chat_messages[-1]["parts"][0],
                generation_config=generation_config
            )

        end_time = time.time()

        return {
            "content": response.text,
            "role": "assistant",
            "model": self.model,
            "usage": {
                "prompt_tokens": getattr(response, 'usage_metadata', {}).prompt_token_count or 0,
                "completion_tokens": getattr(response, 'usage_metadata', {}).candidates_token_count or 0,
                "total_tokens": getattr(response, 'usage_metadata', {}).total_token_count or 0
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        import google.generativeai as genai

        start_time = time.time()
        system_instruction, chat_messages = self._convert_messages(messages)

        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.1),
            max_output_tokens=kwargs.get("max_tokens", 2000),
        )

        # logger.info(f'system_instruction: {system_instruction}')
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction
            )
        else:
            model = genai.GenerativeModel(model_name=self.model)

        logger.info("🤖 Starting chat session")
        logger.info(f"🤖 Model: {model.model_name}")
        # logger.info(f"💬 User message: {chat_messages[-1]['parts'][0]}")
        # logger.info(f"🤖 Chat history: {chat_messages[:-1]}")
        # logger.info(f"⚙️ Generation config: {generation_config}")
        if len(chat_messages) == 1 and chat_messages[0]["role"] == "user":
            response = await model.generate_content_async(
                chat_messages[0]["parts"][0],
                generation_config=generation_config
            )
        else:
            chat = model.start_chat(history=chat_messages[:-1])
            response = await chat.send_message_async(
                chat_messages[-1]["parts"][0],
                generation_config=generation_config
            )

        # logger.info(f"🤖 Model response: {response.text}")
        logger.info("🤖 Chat session completed")

        end_time = time.time()

        return {
            "content": response.text,
            "role": "assistant",
            "model": self.model,
            "usage": {
                "prompt_tokens": getattr(response, 'usage_metadata', {}).prompt_token_count or 0,
                "completion_tokens": getattr(response, 'usage_metadata', {}).candidates_token_count or 0,
                "total_tokens": getattr(response, 'usage_metadata', {}).total_token_count or 0
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model,
            "max_tokens": 8192,
            "supports_functions": True,
            "supports_streaming": True
        }

class OllamaProvider(ModelProvider):
    """Ollama/Local model provider implementation."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        try:
            import httpx
            self.client = httpx.Client(timeout=60.0)
            self.async_client = httpx.AsyncClient(timeout=60.0)
        except ImportError:
            raise ImportError("httpx library not available. Install with: pip install httpx")
        self.model = model
        self.base_url = base_url or "http://localhost:11434"

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": kwargs.get("temperature", 0.1),
                "num_predict": kwargs.get("max_tokens", 2000),
            },
            "stream": False
        }

        response = self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        response_data = response.json()

        end_time = time.time()

        message = response_data.get("message", {})
        content = message.get("content", "")

        return {
            "content": content,
            "role": message.get("role", "assistant"),
            "model": self.model,
            "usage": {
                "prompt_tokens": response_data.get("prompt_eval_count", len(str(messages)) // 4),
                "completion_tokens": response_data.get("eval_count", len(content) // 4),
                "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": kwargs.get("temperature", 0.1),
                "num_predict": kwargs.get("max_tokens", 2000),
            },
            "stream": False
        }

        response = await self.async_client.post(
            f"{self.base_url}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        response_data = response.json()

        end_time = time.time()

        message = response_data.get("message", {})
        content = message.get("content", "")

        return {
            "content": content,
            "role": message.get("role", "assistant"),
            "model": self.model,
            "usage": {
                "prompt_tokens": response_data.get("prompt_eval_count", len(str(messages)) // 4),
                "completion_tokens": response_data.get("eval_count", len(content) // 4),
                "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "max_tokens": 8192,
            "supports_functions": False,
            "supports_streaming": True,
            "is_local": True
        }

class AnthropicProvider(ModelProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str, model: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")
        self.model = model

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                system_message = content
            else:
                # Anthropic uses 'assistant' instead of 'ai'
                role = "assistant" if role == "assistant" else "user"
                anthropic_messages.append({"role": role, "content": content})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.1),
            system=system_message,
            messages=anthropic_messages
        )

        end_time = time.time()

        return {
            "content": response.content[0].text,
            "role": "assistant",
            "model": self.model,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        import asyncio
        # Run sync method in thread pool for async support
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, messages, kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": self.model,
            "max_tokens": 4096,
            "supports_functions": True,
            "supports_streaming": True
        }

class LLMProviderError(Exception):
    """Exception raised by LLM providers."""
    pass

class CerebrasProvider(ModelProvider):
    """Cerebras provider implementation (OpenAI-compatible API)."""

    def __init__(self, api_key: str = None, model: str = "qwen-3-coder-480b"):
        # Use environment variable if no API key provided
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("Cerebras API key is required. Set CEREBRAS_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        try:
            from cerebras.cloud.sdk import Cerebras
            self.client = Cerebras(api_key=self.api_key)
        except ImportError:
            raise ImportError("Cerebras library not available. Install with: pip install cerebras-cloud-sdk")
        
        # Model-specific configurations for Cerebras models
        self.model_configs = {
            "gpt-oss-120b": {"max_tokens": 65536, "supports_functions": False, "context_length": 65536},
            "llama3.1-8b": {"max_tokens": 8192, "supports_functions": False, "context_length": 128000},
            "llama3.1-70b": {"max_tokens": 8192, "supports_functions": False, "context_length": 128000},
            "llama3.1-8b-instruct": {"max_tokens": 8192, "supports_functions": False, "context_length": 128000},
            "llama3.1-70b-instruct": {"max_tokens": 8192, "supports_functions": False, "context_length": 128000},
            "qwen-3-coder-480b": {"max_tokens": 1000000, "supports_functions": True, "context_length": 128000},
        }

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion using Cerebras API."""
        try:
            start_time = time.time()
            
            # Prepare request parameters
            model_config = self.model_configs.get(self.model, {"max_tokens": 65536})
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": min(kwargs.get("max_tokens", model_config["max_tokens"]), model_config["max_tokens"]),
                "top_p": kwargs.get("top_p", 1.0),
            }

            # Add optional parameters if provided
            if "seed" in kwargs:
                params["seed"] = kwargs["seed"]
            
            # Handle Cerebras-specific parameters
            if "reasoning_effort" in kwargs:
                params["reasoning_effort"] = kwargs["reasoning_effort"]  # low, medium, high
            
            # Handle streaming
            if kwargs.get("stream", False):
                params["stream"] = True
            
            # Handle JSON mode - Cerebras doesn't support response_format yet
            # Instead, we'll add JSON instruction to the system message
            if kwargs.get("response_format") == "json":
                logger.info("Cerebras doesn't support response_format parameter, JSON mode handled via system prompt")
            
            # Cerebras doesn't support function calling yet, but we handle it gracefully
            if "functions" in kwargs:
                logger.warning("Cerebras doesn't support function calling, ignoring functions parameter")
            
            response = self.client.chat.completions.create(**params)
            end_time = time.time()
            
            # Parse response
            message = response.choices[0].message
            result = {
                "content": message.content,
                "role": message.role,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "processing_time_ms": int((end_time - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            raise LLMProviderError(f"Cerebras generation failed: {str(e)}")

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate completion asynchronously using Cerebras API."""
        try:
            start_time = time.time()
            
            # Prepare request parameters  
            model_config = self.model_configs.get(self.model, {"max_tokens": 65536})
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": min(kwargs.get("max_tokens", model_config["max_tokens"]), model_config["max_tokens"]),
                "top_p": kwargs.get("top_p", 1.0),
            }

            # Add optional parameters if provided
            if "seed" in kwargs:
                params["seed"] = kwargs["seed"]

            # Handle Cerebras-specific parameters
            if "reasoning_effort" in kwargs:
                params["reasoning_effort"] = kwargs["reasoning_effort"]  # low, medium, high
            
            # Handle streaming
            if kwargs.get("stream", False):
                params["stream"] = True
            
            # Handle JSON mode - Cerebras doesn't support response_format yet
            # Instead, we'll add JSON instruction to the system message
            if kwargs.get("response_format") == "json":
                logger.info("Cerebras doesn't support response_format parameter, JSON mode handled via system prompt")
            
            # Cerebras doesn't support function calling yet, but we handle it gracefully
            if "functions" in kwargs:
                logger.warning("Cerebras doesn't support function calling, ignoring functions parameter")
            
            # Note: Cerebras SDK doesn't have async client yet, using sync client
            response = self.client.chat.completions.create(**params)
            
            end_time = time.time()
            
            # Parse response (same as sync)
            message = response.choices[0].message
            result = {
                "content": message.content,
                "role": message.role,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "processing_time_ms": int((end_time - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Cerebras API error (async): {e}")
            raise LLMProviderError(f"Cerebras async generation failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get Cerebras model information."""
        config = self.model_configs.get(self.model, {"max_tokens": 8192, "supports_functions": False, "context_length": 128000})
        return {
            "provider": "cerebras",
            "model": self.model,
            "max_tokens": config["max_tokens"],
            "context_length": config.get("context_length", 128000),
            "supports_functions": config["supports_functions"],
            "supports_streaming": True,
            "supports_json_mode": False,  # Not via response_format parameter
            "supports_reasoning_effort": True
        }

class GenericAPIProvider(ModelProvider):
    """Generic API provider for custom endpoints."""

    def __init__(self, api_key: str, model: str, base_url: str):
        try:
            import httpx
            self.client = httpx.Client(timeout=30.0)
            self.async_client = httpx.AsyncClient(timeout=30.0)
        except ImportError:
            raise ImportError("httpx library not available. Install with: pip install httpx")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        response_data = response.json()

        end_time = time.time()

        message = response_data["choices"][0]["message"]
        usage = response_data.get("usage", {})

        return {
            "content": message.get("content", ""),
            "role": message.get("role", "assistant"),
            "model": response_data.get("model", self.model),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_async(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = await self.async_client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        response_data = response.json()

        end_time = time.time()

        message = response_data["choices"][0]["message"]
        usage = response_data.get("usage", {})

        return {
            "content": message.get("content", ""),
            "role": message.get("role", "assistant"),
            "model": response_data.get("model", self.model),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "processing_time_ms": int((end_time - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "generic_api",
            "model": self.model,
            "max_tokens": 4096,
            "supports_functions": False,
            "supports_streaming": False
        }

class ModelClientError(Exception):
    """Exception raised by model client."""
    pass

# Singleton instance
_model_client = None

def get_model_client(**kwargs) -> DynamicModelClient:
    """Get singleton model client instance."""
    global _model_client
    if _model_client is None:
        _model_client = DynamicModelClient(**kwargs)
    return _model_client

# Backward compatibility
def get_llm_client(**kwargs) -> DynamicModelClient:
    """Backward compatibility function."""
    return get_model_client(**kwargs)
