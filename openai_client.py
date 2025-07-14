import os
import openai
import tiktoken

# Pricing per 1,000 tokens in USD for GPT-4 (8K context)
# Adjust if you use a different model or context size
TOKEN_PRICE_PROMPT = 0.03 / 1000
TOKEN_PRICE_COMPLETION = 0.06 / 1000

def prompt_tech_only(tech, n):
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets or other sensitive endpoints that could be helpful to find. "
        f"The following tech stack is known: {tech}. Create {n} URLs for content discovery. Provide only relative URLs. Create one URL per line. "
        f"Given this tech stack: {tech}, provide {n} possible explanations of what the app likely does."
    )

def prompt_tech_and_urls(tech, urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets or other sensitive endpoints that could be helpful to find. "
        f"The following tech stack is known: {tech}. The following URLs are known:\n{urls_text}\n"
        f"Create {n} additional URLs for content discovery based on this data. Provide only relative URLs. Create one URL per line."
    )

def prompt_urls_only(urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets or other sensitive endpoints that could be helpful to find. "
        f"The following URLs are known:\n{urls_text}\n"
        f"Create {n} additional URLs for content discovery based on this data. Provide only relative URLs. Create one URL per line."
    )

class OpenAIClient:
    def __init__(self, api_key=None, model="gpt-4"):
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key is missing. Provide via -k or environment variable OPENAI_API_KEY.")

        self.model = model
        self.encoder = tiktoken.encoding_for_model(self.model)

    def count_tokens(self, text):
        return len(self.encoder.encode(text))

    def call_openai(self, prompt, max_tokens=5000):
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()

    def estimate_cost(self, total_tokens: int) -> float:
        """
        Estimate cost given total token count.
        Pricing (as of current model):
        - GPT-4: $0.03 / 1K prompt tokens + $0.06 / 1K completion tokens
        Here we approximate prompt and completion tokens equally split.
        """
        # Assuming half prompt, half completion tokens:
        prompt_tokens = total_tokens // 2
        completion_tokens = total_tokens - prompt_tokens
        cost = (prompt_tokens / 1000) * 0.03 + (completion_tokens / 1000) * 0.06
        return cost

