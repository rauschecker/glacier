import os
import sys
from openai import OpenAI

def prompt_tech_only(tech, n):
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets "
        f"or other sensitive endpoints that could be helpful to find. The following tech stack is known: "
        f"{tech}. Create {n} URLs for content discovery. Provide only relative URLs. "
        f"Create one URL per line."
    )

def prompt_tech_and_urls(tech, urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets "
        f"or other sensitive endpoints that could be helpful to find. The following tech stack is known: "
        f"{tech}. The following URLs have already been found:\n{urls_text}\n"
        f"Create {n} URLs for content discovery. Provide only relative URLs. "
        f"Create one URL per line."
    )

def prompt_urls_only(urls, n):
    urls_text = "\n".join(urls)
    return (
        f"You are assisting a pentester in content discovery and provide URLs that may contain secrets "
        f"or other sensitive endpoints that could be helpful to find. The following URls have already been found:\n"
        f"{urls_text}\nCreate {n} URLs for content discovery. Provide only relative URLs. "
        f"Create one URL per line."
    )
    
class OpenAIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Error: OpenAI API key is missing.\n"
                  "Provide via constructor, -k option, or OPENAI_API_KEY env variable.")
            sys.exit(1)
        self.client = OpenAI(api_key=self.api_key)

    def call_openai(self, prompt, max_tokens=5000):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes tech stacks and URLs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            sys.exit(1)
