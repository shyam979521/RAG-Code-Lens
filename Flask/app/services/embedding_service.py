import google.generativeai as genai
import time

class EmbeddingService:
    def __init__(self): self.model = None
    def get_embedding(self, text, task_type="retrieval_document"):

    # List of models to try
     for m in ["models/gemini-embedding-001", "models/embedding-001"]:
        try:
            res = genai.embed_content(model=m, content=text[:8000], 
                                    task_type=task_type)
            return res['embedding']
        except:
            time.sleep(2); continue
     return None
