from output.Ai_Plotter import AIPlotter


class AIPlotterApp:
    def __init__(self):
        self.plotter = AIPlotter()

    def generate_plot(self, input_text):
        """
        Generate and execute plotting code from given input text.
        
        Args:
            input_text (str): Natural language description of the plot.
            
        Returns:
            dict: Status and message
        """
        output_path = self.plotter.build_output_path(input_text)
        generated_code = self.plotter.generate_code_from_text(input_text, output_path)

        if not generated_code:
            return {
                "success": False,
                "message": "The AI failed to generate valid plotting code.",
                "file_path": None,
            }

        success, saved_path = self.plotter.execute_code(generated_code, output_path)

        if success:
            return {
                "success": True,
                "message": f"Plot created successfully in '{self.plotter.display_folder}'",
                "file_path": saved_path,
            }

        return {
            "success": False,
            "message": "Failed to execute generated plotting code.",
            "file_path": None,
        }