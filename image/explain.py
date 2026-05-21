import ollama
import os

class Vision:
    def __init__(self, model_name="gemma4:31b-cloud"):
        """
        Initializes the Vision Analyzer with a specific model.
        """
        self.model_name = model_name

    def explain_image(self, image_path, prompt=None):
        """
        Passes an image path and returns the model's response as a string.
        """
        # 1. Verify if the image file exists
        if not os.path.exists(image_path):
            return f"Error: The file at {image_path} was not found."

        # Default prompt if none is provided
        if prompt is None:
            prompt = "Please explain this image in detail. What is happening, and what are the key objects or people visible?"

        try:
            # 2. Call the Ollama chat interface
            response = ollama.chat(
                model=self.model_name, 
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [image_path] 
                    },
                ],
            )
            
            # 3. Return only the text content of the message
            return response['message']['content']

        except Exception as e:
            return f"An error occurred while processing the image: {str(e)}"

