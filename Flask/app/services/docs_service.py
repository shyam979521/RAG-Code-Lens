class DocsService:
    def generate_docs(self, project_summary):
        prompt = f"Create a high-level technical README for this project based on these 
    files:\n{project_summary}"
return llm_service.generate_text(prompt)