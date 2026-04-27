from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
import os

class RagService:
    def __init__(self):
        print(" Initializing RAG Service...")
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        
        # Test connections
        self.llm_service.test_connection()
        self.embedding_service.test_connection()
        print(" RAG Service ready")
    
    def index_file_chunks(self, file_id, chunks):
        """Index file chunks into vector database for semantic search"""
        if not chunks:
            print("   No chunks to index")
            return 0
        
        vectors = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if not chunk or len(chunk.strip()) < 10:
                continue
                
            print(f"  Indexing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            embedding = self.embedding_service.get_embedding(chunk)
            
            if embedding:
                vectors.append(embedding)
                vector_id = file_id * 10000 + i
                ids.append(vector_id)
            else:
                print(f"  Failed to get embedding for chunk {i+1}")
        
        if vectors:
            added = self.vector_service.add_vectors(vectors, ids)
            print(f" Indexed {added} chunks successfully")
            return added
        
        print("  No vectors were created")
        return 0
    
    def answer_query(self, query, project_name=None):
        """Answer a question about a specific project"""
        print(f"📝 Processing query: {query}")
        if project_name:
            print(f"   Project: {project_name}")
        
        # Build prompt with project context
        if project_name:
            prompt = f"""You are analyzing a project called "{project_name}". 
Answer this question about the codebase: {query}

Provide a clear, helpful answer based on the code."""
        else:
            prompt = f"""Answer this question about the codebase: {query}

Provide a clear, helpful answer."""
        
        try:
            answer = self.llm_service.generate_text(prompt)
            return {
                'answer': answer,
                'sources': [project_name] if project_name else [],
                'num_sources': 1 if project_name else 0
            }
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'sources': [],
                'num_sources': 0
            }
    
    def explain_file(self, filename, content):
        """Explain a specific file (no vector search needed)"""
        if not content or len(content.strip()) == 0:
            return "This file appears to be empty."
        
        if len(content) > 8000:
            content = content[:8000] + "\n... (truncated)"
        
        prompt = f"""Explain this code file like a Senior Engineer:

File: {filename}

Code:
{content}

Please provide a clear explanation covering:
1. PURPOSE: What does this file do?
2. MAIN COMPONENTS: Key functions/classes
3. DEPENDENCIES: What imports does it use?
4. POTENTIAL ISSUES: Any bugs or improvements?
5. HOW TO USE: Basic example

Keep the explanation helpful for developers."""

        try:
            explanation = self.llm_service.generate_text(prompt)
            return explanation
        except Exception as e:
            return f"Error explaining file: {str(e)}"
    
    def generate_readme(self, project_files):
        """Generate README for the project"""
        if not project_files:
            return "No files found to generate README. Please upload some code first."
        
        file_list = []
        for f in project_files[:30]:
            ext = f['name'].split('.')[-1] if '.' in f['name'] else 'unknown'
            file_list.append(f"- `{f['name']}` ({ext})")
        
        files_text = "\n".join(file_list)
        
        prompt = f"""Create a professional README.md for a software project based on these files:

## Files in the project:
{files_text}

Generate a complete README.md with:
1. **Project Title** (based on the files)
2. **Description** (what this project does)
3. **Features** (key capabilities)
4. **Tech Stack** (languages used)
5. **Installation** (how to set it up)
6. **Usage** (how to run it)
7. **Project Structure** (file overview)

Make it professional and clear."""

        try:
            readme = self.llm_service.generate_text(prompt)
            return readme
        except Exception as e:
            return f"Error generating README: {str(e)}"
    
    def get_index_stats(self):
        """Get statistics about the vector index"""
        total = self.vector_service.get_total_vectors()
        return {
            'total_vectors': total,
            'has_index': total > 0
        }