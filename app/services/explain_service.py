from app.services.llm_service import LLMService

class ExplainService:
    def __init__(self):
        self.llm_service = LLMService()
    
    def explain_file(self, filename, code):
        """Explain a single code file"""
        prompt = f"""Explain this code file like a Senior Engineer:

File Name: {filename}

Code:
{code[:10000]}

Provide:
1. Purpose of this file
2. Main functions and what they do
3. Key dependencies
4. Potential improvements or issues"""

        return self.llm_service.generate_text(prompt)
    
    def explain_function(self, function_name, function_code):
        """Explain a specific function"""
        prompt = f"""Explain this function:

Function Name: {function_name}

Code:
{function_code[:3000]}

Explain:
1. What this function does
2. Parameters and return values
3. Example usage
4. Edge cases"""

        return self.llm_service.generate_text(prompt)
    
    def find_bugs(self, filename, code):
        """Find potential bugs in code"""
        prompt = f"""Review this code for potential bugs and issues:

File: {filename}

Code:
{code[:10000]}

Identify:
1. Potential bugs
2. Security issues
3. Performance problems
4. Code style issues
5. Suggestions for fixes"""

        return self.llm_service.generate_text(prompt)