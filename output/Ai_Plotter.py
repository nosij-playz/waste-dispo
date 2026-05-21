import os
import ollama
import re
import json

class AIPlotter:
    def __init__(self, model_name="gemma4:31b-cloud"):
        self.model_name = model_name
        self.display_folder = "Display"
        
        if not os.path.exists(self.display_folder):
            os.makedirs(self.display_folder)

    def generate_code_from_text(self, user_query):
        """
        plotter reads the text, extracts the data, and writes the plotting code.
        """
        print(f"🧠 plotter is parsing data and designing the plot...")
        
        prompt = (
            f"You are a professional Data Scientist. The user will provide a request that includes both "
            f"the type of graph they want and the data for that graph as text.\n\n"
            f"USER REQUEST AND DATA: {user_query}\n\n"
            f"YOUR TASK:\n"
            f"1. Extract the data points from the text provided.\n"
            f"2. Write Python code to visualize this data using 'matplotlib' and 'seaborn'.\n"
            f"3. Create a Pandas DataFrame inside the code using the extracted data.\n"
            f"4. Save the plot as a .png file in the 'display/' folder with a relevant name.\n"
            f"5. Return ONLY the raw Python code. Do NOT provide explanations, do NOT use markdown backticks (like ```python).\n"
            f"6. Ensure all necessary imports (pandas, matplotlib.pyplot, seaborn) are included."
        )

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            code = response['message']['content']
            return self._clean_code(code)
        except Exception as e:
            print(f"Error generating code: {e}")
            return None

    def _clean_code(self, code):
        """
        Removes any accidental markdown or conversational text.
        """
        # Remove markdown code blocks if the AI added them
        code = re.sub(r"```python\n?", "", code)
        code = re.sub(r"```", "", code)
        # Remove any lines that start with # if the AI added "Here is the code..."
        lines = code.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('Here is')]
        return "\n".join(cleaned_lines).strip()

    def execute_code(self, code):
        """
        Executes the generated Python code.
        """
        if not code:
            return False

        print("\n🚀 Executing generated code...")
        try:
            # Execute the code in a local scope
            exec(code, {"__name__": "__main__"})
            print("✅ Plot successfully generated and saved in the 'display' folder.")
            return True
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            print("\n--- Generated Code That Failed ---\n")
            print(code)
            return False

