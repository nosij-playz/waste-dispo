import os
import json
import webbrowser
import ollama

class DashboardModule:
    def __init__(self, model_name="gemma4:31b-cloud"):
        self.model_name = model_name
        self.base_template_path = "interface/base.html"
        self.output_file = "interface/dashboard.html"

    def _read_base_template(self):
        with open(self.base_template_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_dashboard(self, data_json):
        """
        Passes JSON to Gemma 4 to create a beautiful HTML layout.
        """
        print(" Designing your dashboard...")
        
        # Ensure the input is a proper JSON string
        if isinstance(data_json, list) or isinstance(data_json, dict):
            data_str = json.dumps(data_json, indent=2)
        else:
            data_str = data_json

        prompt = (
            f"You are a world-class Frontend Developer specializing in UI/UX. "
            f"I have the following data: {data_str}\n\n"
            f"TASK:\n"
            f"Create a modern, grid-based dashboard layout using Tailwind CSS. "
            f"Each data entry should be a 'glass-card'.\n"
            f"Requirements:\n"
            f"1. If 'title' is missing, use 'Untitled'.\n"
            f"2. If 'content' is missing, use 'No description available'.\n"
            f"3. If 'link' exists, make it a stylish blue button.\n"
            f"4. If 'image' exists, display it as a rounded image. If missing, use a a nice placeholder icon.\n"
            f"5. Add a 'Close Dashboard' button at the top right that uses JavaScript 'window.close()'.\n"
            f"6. Include a header titled 'Environmental Intelligence Report'.\n"
            f"7. Return ONLY the HTML code that goes INSIDE the <body> tag. "
            f"Do NOT provide markdown backticks, do NOT provide the <html> or <body> tags."
        )

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            html_content = response['message']['content']
            
            # Clean any accidental markdown
            html_content = html_content.replace("```html", "").replace("```", "").strip()

            # Inject into base template
            base_html = self._read_base_template()
            final_html = base_html.replace("{{CONTENT}}", html_content)

            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(final_html)
            
            return True
        except Exception as e:
            print(f"Error generating dashboard: {e}")
            return False

    def open_dashboard(self):
        """Opens the generated dashboard in a new window."""
        path = os.path.abspath(self.output_file)
        webbrowser.open_new(f"file://{path}")
        print(f"🚀 Dashboard opened in your browser.")

    def close_dashboard(self):
        """
        Note: Python cannot force-close a browser tab due to OS security.
        The 'Close' button inside the HTML handles this.
        """
        print("ℹ️ To close the dashboard, please use the 'Close' button inside the window.")

# ==========================================
# EXAMPLE USAGE
# ==========================================
