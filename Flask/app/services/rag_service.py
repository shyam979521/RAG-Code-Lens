from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.models.models import Chunk, File

class RagService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        
    def answer_query(self, query):
        # 1. Embed query
        query_embedding = self.embedding_service.get_embedding(query, task_type="retrieval_query")
        if not query_embedding:
            return {"answer": "Error: Could not generate embedding for query.", "citations": []}
            
        # 2. Search for more chunks so we can filter and diversify
        indices, distances = self.vector_service.search(query_embedding, k=30) 
        
        # 3. Retrieve and Diversify
        logic_context = []
        other_context = []
        citations = []
        seen_chunks = set()
        file_chunk_counts = {} # To limit chunks per file
        
        for idx in indices:
            if idx == -1 or idx in seen_chunks: continue
            chunk = Chunk.query.get(int(idx))
            if not chunk: continue
            
            file = chunk.file
            # Limit: Max 3 chunks per file to avoid "CSS Bloat"
            count = file_chunk_counts.get(file.id, 0)
            if count >= 3:
                continue
                
            context_str = f"File: {file.filepath}\nContent:\n{chunk.chunk_text}\n"
            
            # Prioritize logic files (Python, JS, etc.)
            if file.filetype in ['.py', '.js', '.ts', '.java', '.c', '.cpp']:
                logic_context.append(context_str)
            else:
                other_context.append(context_str)
                
            if file.filepath not in citations:
                citations.append(file.filepath)
            
            seen_chunks.add(idx)
            file_chunk_counts[file.id] = count + 1
            
            # If we have enough context, stop early (e.g., 12 chunks total)
            if len(logic_context) + len(other_context) >= 12:
                break
        
        # Reorder context: Logic files ALWAYS first
        all_context = logic_context + other_context
        context = "\n---\n".join(all_context)
        
        print(f"--- RAG Search Results ({len(citations)} files): {citations}")
        import sys
        sys.stdout.flush()
        
        # 4. Generate Answer
        prompt = f"""You are an advanced AI Codebase Assistant.
        Below is the relevant code context retrieved from the database to help you answer.
        
        CONTEXT:
        {context}
        
        USER QUESTION: {query}
        
        INSTRUCTIONS:
        1. Use the provided context to explain the logic clearly.
        2. If the context is specific code, explain how it works.
        3. Even if the exact answer isn't in a single line, try to INFER the meaning from the surrounding code.
        4. If you absolutely cannot find anything related, then only say you don't know.
        
        Provide a professional, technical, and helpful answer in Markdown format."""
        
        answer = self.llm_service.generate_text(prompt)
        
        return {
            "answer": answer,
            "citations": citations
        }
