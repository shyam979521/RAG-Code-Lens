class ExplainService:
    def explain_file(self, name, code):
        prompt = f"Explain this code file like a Senior Engineer: {name}\nCode: 
{code[:10000]}"
    return llm_service.generate_text(prompt)
