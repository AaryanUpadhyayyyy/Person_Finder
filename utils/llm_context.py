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
I found an image on this webpage. Based on the following text extracted from the page (and search result titles associated with the image), generate an EXHAUSTIVE, DEEPLY ANALYTICAL INTELLIGENCE DOSSIER about the person in the image.

CRITICAL RULES:
1. STRICT ANTI-HALLUCINATION: You MUST ONLY use the information explicitly stated in the 'Extracted Text' below. DO NOT use your internal training data to guess who this person is.
2. If the name is common (e.g., "Abhishek Kumar"), do NOT confuse them with an actor or celebrity unless the text explicitly says they are an actor. Read the surrounding context first (are they a politician, a minister, a doctor?) and build the profile based ONLY on that context.
3. If multiple people are mentioned, focus on the primary subject of the article.

Your response MUST be formatted as a detailed, multi-section report using the following structure. Write long, comprehensive paragraphs for each section based ONLY on the provided text:

1. EXECUTIVE SUMMARY
(Provide a deep overview of who this person is, their primary role, and why they are in the news based strictly on the text.)

2. PRIMARY IDENTITY & AFFILIATIONS
(Extract their full name, any titles [Dr., Minister, etc.], exact profession, and organizations/parties they are tied to based on the text.)

3. CONTEXTUAL & NARRATIVE ANALYSIS
(Deeply analyze WHY this image/article exists based on the text. What is the story? Is it a controversy, a political event, a social media post? Explain the situation in extreme detail.)

4. ASSOCIATED ENTITIES & RELATIONSHIPS
(List and explain every other person, location, or organization mentioned in the text in relation to this individual.)

5. TIMELINE & DISCOVERY METADATA
(When was this published? What dates are mentioned in the text? Give a chronological breakdown if applicable.)

If the text is genuinely completely empty or irrelevant, explicitly state: "Insufficient data to build a complete profile."


Extracted Text:
{text_preview}
"""
        
        # Try models in order (fallback chain for decommissioned models)
        models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        last_error = None
        for model_name in models:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are TALAASH INTEL, an elite cyber-intelligence and OSINT profiler. Your job is to deeply analyze web text and construct exhaustive, highly detailed dossiers. You think deeply, analyze context, and write extensively without leaving out a single detail."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model_name,
                    temperature=0.4,
                    max_tokens=2500
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
