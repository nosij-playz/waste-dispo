import json
from data_fetch.research import AIAnalyzer, WebSearcher

ws = WebSearcher(max_results=10) 
ai = AIAnalyzer()

query = "waste management on plastic and solid waste"
    
    # 2. Fetch raw data (Fast)
print(f"🌐 Step 1: Searching the web for '{query}'...")
raw_data = ws.search(query)

    # 3. Analyze in one batch (Fastest)
print(f"📖 Step 2: Analyzing content with AI Batch Processing...")
final_json_list = ai.study_and_simplify_batch(raw_data)

    # 4. Final Output
print("\n--- FINAL SIMPLIFIED AI RESEARCH REPORT ---\n")
print(json.dumps(final_json_list, indent=4))

    # Save to file
with open("display/research_report.json", "w", encoding="utf-8") as f:
        json.dump(final_json_list, f, indent=4)
    
print(f"\n✅ Final report saved to display/research_report.json")
