import os
import tiktoken
from openai import OpenAI
from typing import Optional

def prompt_tech_only(tech, n):
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain sensitive or private data or other sensitive endpoints that could be helpful to find. "
        f"The following tech stack is known: {tech}. Create {n} URLs for content discovery. Provide only relative URLs. Create one URL per line. Only output URLs, no description."
    )

def prompt_tech_and_urls(tech, urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain sensitive or private data or other sensitive endpoints that could be helpful to find. "
        f"The following tech stack is known: {tech}. The following URLs are known:\n{urls_text}\n"
        f"Create {n} additional URLs for content discovery based on this data. Provide only relative URLs. Create one URL per line. Only output URLs, no description."
    )

def prompt_urls_only(urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain sensitive or private data or other sensitive endpoints that could be helpful to find. "
        f"The following URLs are known:\n{urls_text}\n"
        f"Create {n} additional URLs for content discovery based on this data. Provide only relative URLs. Create one URL per line. Only output URLs, no description."
    )


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "OpenAI API key must be provided via -k option or OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.encoder = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError(f"Expected string for token counting, got {type(text)}")
        return len(self.encoder.encode(text))

    def call_openai(self, prompt: str, max_tokens: int = 1000) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0,
                n=1,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
