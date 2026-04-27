from app.services.llm_service import LLMService

class ExplainService:
    def __init__(self):
        self.llm_service = LLMService()
        
    def explain_file(self, filename, content):
        prompt = f"""You are an expert Senior Developer. Analyze the following code file and provide a structured explanation in Markdown.
        
        FILENAME: {filename}
        
        CODE CONTENT (Truncated):
        {content[:25000]}
        
        ---
        
        **Output Format (Strictly adhere to this Markdown structure):**
        
        ## 📄 File Summary
        (Brief overview of what this file does in 2-3 sentences.)
        
        ## 🛠 Key Components
        | Component (Function/Class) | Purpose |
        | :--- | :--- |
        | `function_name` | Brief description of what it handles. |
        
        ## 🔄 Logic Flow
        (Step-by-step simple explanation of how data moves through this file.)
        
        ## 💡 Improvement Suggestions
        - **Readability**: ...
        - **Performance**: ...
        - **Security**: ... (if applicable)
        
        Do not add any intro or outro text. Just the markdown.
        """
        return self.llm_service.generate_text(prompt)
