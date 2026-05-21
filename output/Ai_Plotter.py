import os
import ollama
import re
from datetime import datetime


class AIPlotter:
    def __init__(self, model_name="gemma4:31b-cloud"):
        self.model_name = model_name
        self.display_folder = "display"
        
        if not os.path.exists(self.display_folder):
            os.makedirs(self.display_folder)

    def _slugify(self, text, max_len=60):
        text = (text or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")
        if not text:
            text = "plot"
        return text[:max_len]

    def build_output_path(self, user_query):
        slug = self._slugify(user_query)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{ts}.png"
        return os.path.join(self.display_folder, filename)

    def generate_code_from_text(self, user_query, output_path):
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
            f"4. Save the plot to the exact file path in the variable OUTPUT_PATH (do not choose your own path).\n"
            f"   - Use: plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches='tight')\n"
            f"   - Do not call plt.show()\n"
            f"5. Return ONLY the raw Python code. Do NOT provide explanations, do NOT use markdown backticks (like ```python).\n"
            f"6. Ensure all necessary imports (pandas, matplotlib.pyplot, seaborn) are included.\n\n"
            f"OUTPUT_PATH = {output_path!r}"
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

    def execute_code(self, code, output_path):
        """
        Executes the generated Python code.
        """
        if not code or not output_path:
            return False, None

        print("\n🚀 Executing generated code...")
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Execute the code in a local scope and provide OUTPUT_PATH
            exec_globals = {
                "__name__": "__main__",
                "OUTPUT_PATH": output_path,
            }
            exec(code, exec_globals)

            if os.path.exists(output_path):
                print(f"✅ Plot successfully generated and saved: {output_path}")
                return True, output_path

            print("❌ Plot code ran, but no image was saved to OUTPUT_PATH.")
            return False, None
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            print("\n--- Generated Code That Failed ---\n")
            print(code)
            return False, None

