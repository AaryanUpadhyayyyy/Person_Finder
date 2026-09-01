import requests
from bs4 import BeautifulSoup
from groq import Groq
import os
import sys

def analyze_context(url: str, groq_api_key: str):
    if not url or url == "#" or not url.startswith("http"):
        return None
        
    try:
        # Fetch the webpage
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit text length to avoid token limits (keep first 5000 chars)
        text_preview = text[:5000]
        
        if len(text_preview) < 50:
            return "Not enough context found on the page."
            
        # Initialize Groq client
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""
I found an image on this webpage. Based on the following text extracted from the page, please answer these three questions concisely:
1. When was this picture taken? (or when was this article published?)
2. What is the context of the image? (Why was it posted?)
3. Who is the person in this image? (If mentioned)

Extracted Text:
{text_preview}
"""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes webpage text to provide context for images. Be concise."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.3,
            max_tokens=300
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"LLM Context analysis failed: {e}", file=sys.stderr)
        return None
