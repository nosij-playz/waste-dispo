from output.Ai_Plotter import AIPlotter
plotter = AIPlotter()

print("--- AI Data Plotter ---")
print("Example: 'Create a bar chart for plastic waste growth: 1990-10M, 2000-20M, 2010-40M'")
    
user_input = input("\nDescribe the plot and provide the data: ")
    
    # Step 1: AI parses the text and writes the code
generated_code = plotter.generate_code_from_text(user_input)
    
if generated_code:
        # Step 2: Execute the code to save the image
    success = plotter.execute_code(generated_code)
    if success:
        print(f"\n🎉 Check the '{plotter.display_folder}' folder for your results!")
else:
    print("\n⚠️ The AI failed to write valid code for this data. Please try re-formatting your data.")
