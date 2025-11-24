"""OpenRouter LLM client for ExamGenie."""

import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()


class LLMClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        
        # Initialize OpenAI client pointing to OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        console.print(f"[green]✓[/green] LLM client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            The assistant's response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            console.print(f"[red]✗[/red] LLM API error: {e}")
            raise
    
    def get_embedding(self, text: str, model: str | None = None) -> list[float]:
        """
        Get embeddings for text using OpenRouter.
        
        Args:
            text: Text to embed
            model: Embedding model to use (overrides env var)
            
        Returns:
            Embedding vector
        """
        embedding_model = model or os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-large")
        
        try:
            response = self.client.embeddings.create(
                model=embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] External embedding failed: {e}")
            raise
