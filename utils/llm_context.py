import requests
from groq import Groq
import os
import sys

def analyze_context(url: str, groq_api_key: str, score: float, fallback_title: str = ""):
    if not groq_api_key:
        return "GROQ_API_KEY is not configured. Cannot generate intelligence brief."
        
    if not url or url == "#" or not url.startswith("http"):
        return "No valid source URL provided to extract intelligence."
        
    try:
        # Use Jina Reader API to extract clean markdown from JS-heavy sites (e.g., FB, IG, X)
        headers = {
            "User-Agent": "Talaash-Scanner/1.0"
        }
        
        jina_url = f"https://r.jina.ai/{url}"
        print(f"Fetching context from: {jina_url}")
        
        try:
            resp = requests.get(jina_url, headers=headers, timeout=15)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            print(f"Jina Reader failed: {e}. Using fallback title.")
            text = ""
            
        # Combine Jina extracted text with the Google Lens title (which often contains the post caption)
        combined_text = f"Title/Caption from Search: {fallback_title}\n\nPage Content:\n{text}"
        
        # Limit text length to avoid token limits (keep first 6000 chars)
        text_preview = combined_text[:6000]
        
        if len(text_preview.strip()) < 10:
            return "Not enough context found on the page or in the search title."
            
        # Initialize Groq client
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""
I found an image on this webpage. Based on the following text extracted from the page (and its search title), please answer these questions concisely like a military intelligence brief (use bullet points):
1. Who is the person in this image? (If mentioned)
2. What is the context of the image? (Why was it posted? Is it a social media post, article, etc.?)
3. When was this published or taken? (If mentioned)

Extract any useful intelligence. If the text is empty or irrelevant, just state that no intelligence could be gathered.

Extracted Text:
{text_preview}
"""
        
        # Try models in order (fallback chain for decommissioned models)
        models = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        last_error = None
        for model_name in models:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are TALAASH INTEL, an AI analyst providing concise, highly accurate intelligence briefs based on web text. Keep it strictly to the facts found in the text."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model_name,
                    temperature=0.2,
                    max_tokens=300
                )
                return chat_completion.choices[0].message.content
            except Exception as model_err:
                print(f"Model {model_name} failed: {model_err}")
                last_error = model_err
                continue
        
        return f"INTELLIGENCE FAILURE: All models failed. Last error: {str(last_error)}"
        
    except Exception as e:
        print(f"LLM Context analysis failed: {e}", file=sys.stderr)
        return f"INTELLIGENCE FAILURE: {str(e)}"
