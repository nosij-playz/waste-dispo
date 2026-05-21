import json
import ollama
from ddgs import DDGS
from typing import List, Dict

class WebSearcher:
    def __init__(self, max_results: int = 8):
        self.max_results = max_results

    def search(self, query: str) -> List[Dict]:
        results = []
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=self.max_results
                )
                for item in search_results:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "link": item.get("href", "") # Changed 'source' to 'link'
                    })
        except Exception as e:
            print(f"Search Error: {e}")
        return results

class AIAnalyzer:
    def __init__(self, model_name="gemma4:31b-cloud"):
        self.model_name = model_name

    def study_and_simplify_batch(self, raw_results: List[Dict]):
        """
        Sends ALL results to the AI in one go (Batch Processing) 
        to drastically increase speed.
        """
        if not raw_results:
            return [{"error": "No data to analyze"}]

        # 1. Format all results into a single block of text for the AI
        formatted_data = ""
        for i, item in enumerate(raw_results):
            formatted_data += f"--- Source {i+1} ---\nTitle: {item['title']}\nContent: {item['snippet']}\nLink: {item['link']}\n\n"

        # 2. Create a comprehensive prompt for a JSON List output
        prompt = (
            f"You are an expert environmental scientist and a friendly teacher. "
            f"I will give you a list of search results. Your task is to study all of them and "
            f"simplify the information so a 15-year-old can understand it. Be friendly and encouraging. "
            f"\n\nDATA TO STUDY:\n{formatted_data}\n\n"
            f"IMPORTANT: You must return ONLY a JSON list of objects. "
            f"Each object must have exactly these keys: 'title', 'explain', 'source', 'link'. "
            f"- 'title': The original title.\n- 'explain': Your friendly simplified explanation.\n"
            f"- 'source': The name of the website/platform (extracted from the link).\n- 'link': The original URL."
        )

        print(f"\n🧠 Analyzer is processing {len(raw_results)} sources in one batch... Please wait.")

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            ai_content = response['message']['content']
            
            # Clean markdown formatting
            cleaned_json = ai_content.replace("```json", "").replace("```", "").strip()
            
            # Parse the AI's list string into a Python list
            return json.loads(cleaned_json)
            
        except Exception as e:
            print(f"Batch processing error: {e}")
            # Fallback: if batch fails, return raw data in the requested format
            return [
                {"title": i['title'], "explain": i['snippet'], "source": "Web", "link": i['link']} 
                for i in raw_results
            ]


