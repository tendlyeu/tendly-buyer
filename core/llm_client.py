"""
Unified LLM Client for Tendly
Centralizes all LLM provider integrations (Together AI/Kimi, Google Gemini, xAI Grok)
Provides a consistent interface for different use cases across the application.

Usage Examples:
--------------
# Basic chat completion
from scripts.utils.llm_client import LLMClient, LLMProvider

client = LLMClient(provider=LLMProvider.TOGETHER_AI)
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7
)

# Switch provider easily
client = LLMClient(provider=LLMProvider.GEMINI)

# Use async for non-blocking calls
response = await client.chat_completion_async(messages=[...])

# Extract JSON from response
data = client.extract_json(response_text)

Environment Variables Required:
------------------------------
- TOGETHER_API_KEY: For Together AI (Kimi) access
- GEMINI_API_KEY: For Google Gemini access
- XAI_API_KEY: For xAI Grok access
"""

import os
import re
import json
import asyncio
import requests
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass


class LLMProvider(Enum):
    """Supported LLM providers"""
    TOGETHER_AI = "together_ai"  # Kimi model
    GEMINI = "gemini"  # Google Gemini
    XAI_GROK = "xai_grok"  # xAI Grok


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None  # None means no limit (use model's default)
    timeout: int = 300


# Default configurations for each provider
# max_tokens is not set by default - models will use their natural limits
DEFAULT_CONFIGS = {
    LLMProvider.TOGETHER_AI: {
        "model": "moonshotai/Kimi-K2-Instruct-0905",
        "temperature": 0.7,
        "timeout": 120
    },
    LLMProvider.GEMINI: {
        "model": "gemini-2.5-flash-lite",  # Gemini 2.5 Flash Lite - fast and cost-effective
        "temperature": 0.7,
        "timeout": 300
    },
    LLMProvider.XAI_GROK: {
        "model": "grok-4-fast-reasoning",
        "temperature": 0.1,  # Low temperature for precision
        "timeout": 300
    }
}


class LLMClient:
    """
    Unified LLM Client that supports multiple providers.

    This class provides a consistent interface for:
    - Together AI (Kimi model) - Used for matching, chat, company descriptions, CPV classification
    - Google Gemini - Used for document review and analysis
    - xAI Grok - Used for document generation (DOCX placeholders)
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.TOGETHER_AI,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize the LLM client.

        Args:
            provider: The LLM provider to use
            api_key: API key (defaults to environment variable)
            model: Model name (defaults to provider's default)
            temperature: Temperature setting (defaults to provider's default)
            max_tokens: Max tokens (defaults to provider's default)
            timeout: Request timeout in seconds
        """
        self.provider = provider
        self._config = self._build_config(
            provider, api_key, model, temperature, max_tokens, timeout
        )
        self._client = None
        self._initialize_client()

    def _build_config(
        self,
        provider: LLMProvider,
        api_key: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        timeout: Optional[int]
    ) -> LLMConfig:
        """Build configuration from provided values and defaults"""
        defaults = DEFAULT_CONFIGS[provider]

        # Get API key from environment if not provided
        if api_key is None:
            api_key = self._get_api_key_from_env(provider)

        return LLMConfig(
            provider=provider,
            model=model or defaults["model"],
            api_key=api_key,
            temperature=temperature if temperature is not None else defaults["temperature"],
            max_tokens=max_tokens,  # None means no limit
            timeout=timeout or defaults["timeout"]
        )

    def _get_api_key_from_env(self, provider: LLMProvider) -> str:
        """Get API key from environment variable based on provider"""
        env_vars = {
            LLMProvider.TOGETHER_AI: "TOGETHER_API_KEY",
            LLMProvider.GEMINI: "GEMINI_API_KEY",
            LLMProvider.XAI_GROK: "XAI_API_KEY"
        }
        env_var = env_vars[provider]
        api_key = os.environ.get(env_var, "")

        if not api_key:
            print(f"Warning: {env_var} environment variable not set")

        return api_key

    def _initialize_client(self):
        """Initialize the underlying client based on provider"""
        if not self._config.api_key:
            print(f"Warning: No API key available for {self.provider.value}")
            return

        try:
            if self.provider == LLMProvider.TOGETHER_AI:
                from together import Together
                self._client = Together(api_key=self._config.api_key)

            elif self.provider == LLMProvider.GEMINI:
                from google import genai
                self._client = genai.Client(api_key=self._config.api_key)

            elif self.provider == LLMProvider.XAI_GROK:
                # Grok uses REST API, no client initialization needed
                self._client = {
                    "api_url": "https://api.x.ai/v1/chat/completions",
                    "headers": {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._config.api_key}"
                    }
                }
        except ImportError as e:
            print(f"Error: Could not import client for {self.provider.value}: {e}")
            self._client = None
        except Exception as e:
            print(f"Error initializing {self.provider.value} client: {e}")
            self._client = None

    @property
    def raw_client(self):
        """Access the underlying genai.Client for advanced features like caching and batch API."""
        if self._client is None:
            self._initialize_client()
        return self._client

    @property
    def is_available(self) -> bool:
        """Check if the client is properly initialized and available"""
        return self._client is not None and bool(self._config.api_key)

    @property
    def model(self) -> str:
        """Get the current model name"""
        return self._config.model

    @property
    def config(self) -> LLMConfig:
        """Get the current configuration"""
        return self._config

    def create_cache(self, system_instruction: str, display_name: str, ttl_seconds: int = 3600) -> Optional[str]:
        """Create a Gemini context cache for a system instruction. Returns cache name."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            from google.genai import types
            cache = self.raw_client.caches.create(
                model=self._config.model,
                config=types.CreateCachedContentConfig(
                    display_name=display_name,
                    system_instruction=system_instruction,
                    ttl=f"{ttl_seconds}s",
                )
            )
            logger.info(f"Created Gemini cache '{display_name}': {cache.name} (TTL: {ttl_seconds}s)")
            return cache.name
        except Exception as e:
            logger.warning(f"Failed to create Gemini cache '{display_name}': {e}")
            return None

    def delete_cache(self, cache_name: str):
        """Delete a Gemini context cache."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            self.raw_client.caches.delete(name=cache_name)
            logger.info(f"Deleted Gemini cache: {cache_name}")
        except Exception as e:
            logger.warning(f"Failed to delete Gemini cache {cache_name}: {e}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (prepended to messages)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice specification
            cached_content: Optional Gemini cache name (skips system_instruction when set)

        Returns:
            Dict with 'success', 'content', 'usage', and optionally 'tool_calls'
        """
        if not self.is_available:
            return {
                "success": False,
                "error": f"{self.provider.value} client not available",
                "content": None
            }

        # Build messages with optional system prompt
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        temp = temperature if temperature is not None else self._config.temperature
        tokens = max_tokens if max_tokens is not None else self._config.max_tokens

        try:
            if self.provider == LLMProvider.TOGETHER_AI:
                return self._together_ai_completion(full_messages, temp, tokens, tools, tool_choice)
            elif self.provider == LLMProvider.GEMINI:
                return self._gemini_completion(full_messages, temp, tokens, tools, tool_choice, cached_content=cached_content)
            elif self.provider == LLMProvider.XAI_GROK:
                return self._grok_completion(full_messages, temp, tokens)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an async chat completion request.
        Useful for non-blocking calls in async contexts.

        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens
            cached_content: Optional Gemini cache name (skips system_instruction when set)

        Returns:
            Dict with response data
        """
        # Run the synchronous method in a thread to avoid blocking
        return await asyncio.to_thread(
            self.chat_completion,
            messages,
            system_prompt,
            temperature,
            max_tokens,
            cached_content=cached_content
        )

    def _together_ai_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Together AI (Kimi) completion"""
        try:
            kwargs = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature
            }

            # Only include max_tokens if explicitly set
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens

            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

            response = self._client.chat.completions.create(**kwargs)

            message = response.choices[0].message
            result = {
                "success": True,
                "content": message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
            }

            # Include tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["tool_calls"] = message.tool_calls

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def _gemini_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        cached_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Google Gemini completion with function calling support"""
        try:
            from google.genai import types

            # Convert messages to Gemini format (simple concatenation for now)
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Skip system messages when using cached_content (system prompt is in the cache)
                if role == "system" and cached_content:
                    continue
                elif role == "system":
                    prompt_parts.append(f"Instructions: {content}")
                else:
                    prompt_parts.append(content)

            prompt = "\n\n".join(prompt_parts)

            # Build config with optional max_tokens
            config_kwargs = {"temperature": temperature}
            # Disable thinking when no tools are provided for faster responses;
            # keep thinking enabled for tool/function calling reliability
            if not tools:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens

            # Use cached content if provided
            if cached_content:
                config_kwargs["cached_content"] = cached_content

            # Always disable automatic function calling - we handle tools manually
            config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
                disable=True
            )

            # Convert OpenAI-style tool definitions to Gemini FunctionDeclarations
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)
                if gemini_tools:
                    config_kwargs["tools"] = gemini_tools

            response = self._client.models.generate_content(
                model=self._config.model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )

            # Check for function calls first (they may prevent text from being available)
            function_calls = None
            if hasattr(response, 'function_calls') and response.function_calls:
                function_calls = response.function_calls
            # Fallback: check candidates structure
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                if function_calls is None:
                                    function_calls = []
                                function_calls.append(part.function_call)

            # Get text content (may be empty if function calls are present)
            content = ""
            try:
                if response.text:
                    content = response.text.strip()
            except ValueError:
                # "response.text" raises ValueError when there are non-text parts
                # This is expected when function calls are present
                pass

            result = {
                "success": True,
                "content": content,
                "usage": {}  # Gemini doesn't expose token usage the same way
            }

            # Add function calls if present
            if function_calls:
                result["tool_calls"] = self._convert_gemini_function_calls(function_calls)
                result["_gemini_response"] = response

            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def _convert_tools_to_gemini_format(self, tools: List[Dict]) -> Optional[List]:
        """Convert OpenAI-style tool definitions to Gemini FunctionDeclaration format"""
        try:
            from google.genai import types

            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    # Create FunctionDeclaration with parameters_json_schema (not parameters)
                    # This is the correct parameter name for google-genai SDK
                    func_decl = types.FunctionDeclaration(
                        name=func.get("name", ""),
                        description=func.get("description", ""),
                        parameters_json_schema=func.get("parameters", {})
                    )
                    function_declarations.append(func_decl)

            if function_declarations:
                return [types.Tool(function_declarations=function_declarations)]
            return None
        except Exception as e:
            print(f"Error converting tools to Gemini format: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _convert_gemini_function_calls(self, function_calls) -> List:
        """Convert Gemini function calls to Together AI compatible format"""
        converted = []
        for i, fc in enumerate(function_calls):
            # Create a mock object with the same interface as Together AI tool calls
            class MockToolCall:
                def __init__(self, id, name, arguments):
                    self.id = id
                    self.function = type('Function', (), {'name': name, 'arguments': arguments})()

            # Handle both direct function_calls list and part.function_call objects
            fc_name = fc.name if hasattr(fc, 'name') else str(fc)
            fc_args = {}
            if hasattr(fc, 'args') and fc.args:
                fc_args = dict(fc.args)

            converted.append(MockToolCall(
                id=f"call_{i}",
                name=fc_name,
                arguments=json.dumps(fc_args)
            ))
        return converted

    def _grok_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """xAI Grok completion via REST API"""
        try:
            payload = {
                "messages": messages,
                "model": self._config.model,
                "temperature": temperature
            }

            # Only include max_tokens if explicitly set
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            response = requests.post(
                self._client["api_url"],
                headers=self._client["headers"],
                json=payload,
                timeout=self._config.timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data['choices'][0]['message']['content'].strip()

            return {
                "success": True,
                "content": content,
                "usage": data.get("usage", {})
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out",
                "content": None
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e}",
                "content": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def process_tool_calls(
        self,
        tool_calls: List,
        tool_handlers: Dict[str, Callable]
    ) -> List[Dict[str, Any]]:
        """
        Process tool calls from a response.

        Args:
            tool_calls: List of tool call objects from the response
            tool_handlers: Dict mapping function names to handler functions

        Returns:
            List of tool results
        """
        results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name in tool_handlers:
                try:
                    result = tool_handlers[function_name](**arguments)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
                except Exception as e:
                    results.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"error": str(e)})
                    })
            else:
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": f"Unknown function: {function_name}"})
                })

        return results

    def continue_with_tool_results(
        self,
        original_messages: List[Dict[str, str]],
        assistant_message: Any,
        tool_results: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Continue a conversation after processing tool calls.

        Args:
            original_messages: The original message list
            assistant_message: The assistant's message with tool calls
            tool_results: Results from process_tool_calls
            system_prompt: Optional system prompt to include
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Final response dict
        """
        if self.provider == LLMProvider.GEMINI:
            return self._gemini_continue_with_tool_results(
                original_messages, assistant_message, tool_results,
                system_prompt, temperature, max_tokens
            )
        elif self.provider == LLMProvider.TOGETHER_AI:
            # Build the continuation messages (system prompt first if provided)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(original_messages)
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": assistant_message.tool_calls
            })

            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": result["output"]
                })

            return self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            return {
                "success": False,
                "error": f"Tool calling not supported with {self.provider.value}",
                "content": None
            }

    def _gemini_continue_with_tool_results(
        self,
        original_messages: List[Dict[str, str]],
        assistant_message: Any,
        tool_results: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Continue Gemini conversation after function calling"""
        try:
            from google.genai import types

            # Build the prompt with tool results
            prompt_parts = []

            # Add system prompt
            if system_prompt:
                prompt_parts.append(f"Instructions: {system_prompt}")

            # Add original messages
            for msg in original_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"Instructions: {content}")
                else:
                    prompt_parts.append(content)

            # Add function call results
            prompt_parts.append("\n\nFunction call results:")
            for result in tool_results:
                tool_call_id = result.get("tool_call_id", "")
                output = result.get("output", "")
                prompt_parts.append(f"\nResult for {tool_call_id}:\n{output}")

            prompt_parts.append("\n\nBased on the function results above, provide the final response:")

            prompt = "\n\n".join(prompt_parts)

            # Build config
            config_kwargs = {
                "temperature": temperature if temperature is not None else self._config.temperature,
                "thinking_config": types.ThinkingConfig(thinking_budget=0),
            }
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens

            response = self._client.models.generate_content(
                model=self._config.model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )

            return {
                "success": True,
                "content": response.text.strip() if response.text else "",
                "usage": {}
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    @staticmethod
    def extract_json(text: str) -> Optional[Dict]:
        """
        Extract JSON from a text response.
        Handles responses that may contain JSON wrapped in markdown code blocks or other text.

        Args:
            text: The text containing JSON

        Returns:
            Parsed JSON dict or None if extraction fails
        """
        if not text:
            return None

        try:
            # First try: direct JSON parsing
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Second try: extract from markdown code block
        if '```json' in text:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

        # Third try: find JSON object in text
        if '{' in text and '}' in text:
            try:
                start = text.index('{')
                end = text.rindex('}') + 1
                json_str = text[start:end]

                # Clean common issues
                json_str = re.sub(r'//.*?(?=\n|$)', '', json_str)  # Remove // comments
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # Remove /* */ comments
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas

                return json.loads(json_str)
            except (ValueError, json.JSONDecodeError):
                pass

        return None

    @staticmethod
    def create_mock_response(content: str = "Mock response") -> Dict[str, Any]:
        """
        Create a mock response for testing or fallback scenarios.

        Args:
            content: The mock content

        Returns:
            A response dict matching the expected format
        """
        return {
            "success": True,
            "content": content,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "is_mock": True
        }


# Convenience factory functions for common use cases

def get_matching_client(**kwargs) -> LLMClient:
    """Get a client configured for tender matching (uses Gemini 2.5 Flash Lite for speed)"""
    return LLMClient(provider=LLMProvider.GEMINI, temperature=0.7, **kwargs)


def get_chat_client(**kwargs) -> LLMClient:
    """Get a client configured for chat interactions"""
    return LLMClient(provider=LLMProvider.TOGETHER_AI, temperature=0.7, **kwargs)


def get_document_review_client(**kwargs) -> LLMClient:
    """Get a client configured for document review (Gemini)"""
    return LLMClient(provider=LLMProvider.GEMINI, **kwargs)


def get_document_generator_client(**kwargs) -> LLMClient:
    """Get a client configured for document generation (Grok)"""
    return LLMClient(provider=LLMProvider.XAI_GROK, temperature=0.1, **kwargs)


def get_classification_client(**kwargs) -> LLMClient:
    """Get a client configured for CPV classification"""
    return LLMClient(provider=LLMProvider.TOGETHER_AI, **kwargs)


def get_ai_search_client(**kwargs) -> LLMClient:
    """Get a client configured for AI search response generation (Gemini 2.5 Flash)"""
    return LLMClient(provider=LLMProvider.GEMINI, temperature=0.4, **kwargs)


# Global instances for singleton-like usage
_clients: Dict[LLMProvider, LLMClient] = {}


def get_client(provider: LLMProvider = LLMProvider.TOGETHER_AI, **kwargs) -> LLMClient:
    """
    Get a shared client instance for a provider.
    Creates a new instance if one doesn't exist.

    Args:
        provider: The LLM provider
        **kwargs: Additional configuration overrides

    Returns:
        LLMClient instance
    """
    if provider not in _clients or kwargs:
        _clients[provider] = LLMClient(provider=provider, **kwargs)
    return _clients[provider]
