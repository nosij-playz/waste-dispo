import json
import os
from data_fetch.research import AIAnalyzer, WebSearcher


class ResearchAnalyzer:
    def __init__(self, max_results=10, output_folder="display"):
        self.web_searcher = WebSearcher(max_results=max_results)
        self.ai_analyzer = AIAnalyzer()
        self.output_folder = output_folder

        os.makedirs(self.output_folder, exist_ok=True)

    def run_research(self, query):
        """
        Perform web search + AI analysis.

        Args:
            query (str): Research topic/query

        Returns:
            dict: Structured result
        """
        if not query:
            return {
                "success": False,
                "error": "No query provided."
            }

        try:
            # Step 1: Web Search
            raw_data = self.web_searcher.search(query)

            if not raw_data:
                return {
                    "success": False,
                    "error": "No search results found."
                }

            # Step 2: AI Analysis
            final_json_list = self.ai_analyzer.study_and_simplify_batch(raw_data)

            return {
                "success": True,
                "query": query,
                "results_count": len(final_json_list),
                "report": final_json_list
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def save_report(self, query, filename="research_report.json"):
        """
        Run research and save report to JSON file.
        """
        result = self.run_research(query)

        if result["success"]:
            filepath = os.path.join(self.output_folder, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)

            result["saved_to"] = filepath

        return result

    def get_json(self, query):
        """
        Return JSON string output.
        """
        return json.dumps(self.run_research(query), indent=4)