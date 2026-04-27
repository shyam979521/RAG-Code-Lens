import google.generativeai as genai
from config import Config
import time

class EmbeddingService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self._working_model = None

    def get_embedding(self, text, task_type="retrieval_document"):
        # List of models to try in order of preference
        models_to_try = [
            "models/gemini-embedding-001",
            "models/text-embedding-004",
            "models/embedding-001",
            "gemini-embedding-001",
            "text-embedding-004",
            "embedding-001"
        ]
        
        # If we already found a working model, prioritize it
        if self._working_model:
            # Insert working model at the front (or just use it, but list check is safer if it transiently fails)
            if self._working_model in models_to_try:
                models_to_try.remove(self._working_model)
            models_to_try.insert(0, self._working_model)

        retries = 5 # More retries for free tier
        delay = 5   # More initial delay for free tier
        
        for model_name in models_to_try:
            for attempt in range(retries):
                try:
                    # Truncate text if too long (Gemini has limits)
                    result = genai.embed_content(
                        model=model_name,
                        content=text[:9000], # Safety clip
                        task_type=task_type,
                        title="Code Chunk" if task_type == "retrieval_document" else None
                    )
                    self._working_model = model_name
                    return result['embedding']
                    
                except Exception as e:
                    error_msg = str(e)
                    # If model not found, try the next one in the list immediately
                    if "404" in error_msg or "not found" in error_msg.lower():
                        break # Break inner loop to try next model
                        
                    if "429" in error_msg or "quota" in error_msg.lower():
                        print(f"--- [Wait] API Busy. Re-trying in {delay}s... (Attempt {attempt+1}/{retries})")
                        time.sleep(delay)
                        delay += 5 # Linear backoff
                        continue # Retry same model
                        
                    print(f"--- Embedding error for {model_name}: {error_msg}")
                    return None # Critical error, stop
        
        print(f"!!! Error: None of the following models were found or available: {models_to_try}")
        return None

    def get_embeddings_batch(self, texts, task_type="retrieval_document"):
        """
        Processes a list of texts in a single batch request to speed up processing.
        """
        if not texts:
            return []
            
        models_to_try = [
            "models/gemini-embedding-001",
            "models/text-embedding-004",
            "models/embedding-001"
        ]
        
        if self._working_model:
            if self._working_model in models_to_try:
                models_to_try.remove(self._working_model)
            models_to_try.insert(0, self._working_model)

        retries = 3
        delay = 5
        
        for model_name in models_to_try:
            for attempt in range(retries):
                try:
                    # Filter/Truncate texts
                    safe_texts = [t[:9000] for t in texts]
                    
                    result = genai.embed_content(
                        model=model_name,
                        content=safe_texts,
                        task_type=task_type
                    )
                    self._working_model = model_name
                    return result['embedding']
                    
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg or "not found" in error_msg.lower():
                        break
                    
                    if "429" in error_msg or "quota" in error_msg.lower():
                        print(f"--- [Wait] API Batch Busy. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay += 5
                        continue
                    
                    print(f"--- Batch error for {model_name}: {error_msg}")
                    return []
        return []
