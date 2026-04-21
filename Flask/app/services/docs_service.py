from app.services.llm_service import LLMService

class DocsService:
    def __init__(self):
        self.llm_service = LLMService()
        
    def generate_docs(self, project_context):
        """
        project_context: A string containing summaries or code of key files.
        """
        prompt = f"""You are a technical documentation expert. Generate a professional and comprehensive `README.md` for this software project.
        
        Using the following project context (file summaries/code snippets):
        {project_context[:40000]}
        
        ---
        
        **Output Requirements:**
        1. **Title & Badges**: Project name with hypothetical status badges.
        2. **Project Description**: A clear, high-level summary of what the project does.
        3. **Key Features**: A bulleted list of 5-7 distinct features found in the code.
        4. **Tech Stack**: List languages, frameworks, and libraries used (e.g., Flask, FAISS, Gemini, SQLAlchemy).
        5. **Installation**: Step-by-step guide (Git clone, venv, pip install).
        6. **Configuration**: Explain environment variables (e.g., GEMINI_API_KEY).
        7. **Usage**: How to run the app and use endpoints/features.
        8. **Project Structure**: visualizing the likely directory tree based on the files provided.
        9. **API Reference**: If routes are found, list key endpoints.
        
        Format the output purely in **Markdown**. Do not include conversational text.
        """
        return self.llm_service.generate_text(prompt)
