from app.services.llm_service import LLMService

class DocsService:
    def __init__(self):
        self.llm_service = LLMService()
    
    def generate_docs(self, project_summary):
        """Generate documentation for the project"""
        prompt = f"""Create comprehensive documentation for this project:

Project Files:
{project_summary}

Generate:
1. Project Overview
2. Architecture Diagram (text-based)
3. Setup Instructions
4. API Documentation (if applicable)
5. Contributing Guidelines
6. License Information"""

        return self.llm_service.generate_text(prompt)
    
    def generate_api_docs(self, functions_list):
        """Generate API documentation from functions"""
        prompt = f"""Generate API documentation for these functions:

Functions:
{functions_list}

Create documentation with:
- Function signatures
- Parameter descriptions
- Return values
- Example usage"""

        return self.llm_service.generate_text(prompt)
    
    def generate_code_comments(self, code):
        """Generate comments for code"""
        prompt = f"""Add detailed comments to this code:

Code:
{code[:8000]}

Add:
- File header comment
- Function docstrings
- Inline comments for complex logic
- Type hints suggestions"""

        return self.llm_service.generate_text(prompt)