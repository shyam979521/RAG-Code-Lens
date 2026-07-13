from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.models.models import File

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

    def _build_code_context(self, query, project_name=None, max_files=6, max_chars_per_file=1200):
        """Build a compact code context from uploaded files."""
        files_query = File.query
        if project_name:
            files_query = files_query.filter_by(project_name=project_name)

        files = files_query.order_by(File.created_at.desc()).all()
        if not files:
            return "", []

        query_lower = query.lower()
        scored_files = []

        for file in files:
            content = (file.content or "").strip()
            filename = (file.filename or "").lower()
            filepath = (file.filepath or "").lower()
            score = 0

            if filename and filename in query_lower:
                score += 5
            if filepath and filepath in query_lower:
                score += 5

            if content:
                lowered_content = content.lower()
                for token in query_lower.split():
                    if len(token) > 2 and token in lowered_content:
                        score += 1

            scored_files.append((score, file))

        scored_files.sort(
            key=lambda item: (
                item[0],
                len((item[1].content or "").strip())
            ),
            reverse=True
        )

        context_parts = []
        source_names = []

        for _, file in scored_files[:max_files]:
            content = (file.content or "").strip()
            if not content:
                continue

            snippet = content[:max_chars_per_file]
            if len(content) > max_chars_per_file:
                snippet += "\n... (truncated)"

            display_path = file.filepath or file.filename or "unknown"
            source_names.append(display_path)
            context_parts.append(
                f"File: {display_path}\nProject: {file.project_name}\nCode:\n{snippet}"
            )

        return "\n\n---\n\n".join(context_parts), source_names

    def _generate_local_summary(self, project_name=None):
        """Create a small deterministic summary when the LLM gives a generic answer."""
        files_query = File.query
        if project_name:
            files_query = files_query.filter_by(project_name=project_name)

        files = files_query.order_by(File.created_at.asc()).all()
        if not files:
            return ""

        file_names = [file.filename for file in files if file.filename]
        file_paths = [file.filepath for file in files if file.filepath]
        lower_paths = " ".join(path.lower() for path in file_paths)

        summary_lines = []
        if project_name:
            summary_lines.append(f'This project appears to be "{project_name}".')
        else:
            summary_lines.append("This uploaded codebase contains the following structure.")

        if any(name == 'app.py' for name in file_names):
            summary_lines.append("It looks like a Flask web application with an app entry file.")
        if 'templates' in lower_paths:
            summary_lines.append("It includes HTML templates for rendered pages.")
        if 'static' in lower_paths:
            summary_lines.append("It includes static frontend assets such as CSS or JavaScript.")

        visible_files = ", ".join(file_names[:6])
        if visible_files:
            summary_lines.append(f"Main files found: {visible_files}.")

        for file in files:
            content = (file.content or "").lower()
            if "@app.route" in content:
                route_count = content.count("@app.route")
                summary_lines.append(f'The main app file defines around {route_count} route(s), so this project serves web pages.')
                break

        return " ".join(summary_lines)
    
    def answer_query(self, query, project_name=None):
        """Answer a question about a specific project"""
        print(f"📝 Processing query: {query}")
        if project_name:
            print(f"   Project: {project_name}")
        
        code_context, source_names = self._build_code_context(query, project_name)
        if not code_context:
            return {
                'answer': "No uploaded code files were found for analysis. Please upload a project first.",
                'sources': [],
                'num_sources': 0
            }

        scope = f'the project "{project_name}"' if project_name else "the uploaded codebase"
        prompt = f"""You are analyzing {scope}.

Question: {query}

Use only the code context below to answer. If the answer is not present in the provided code, say that clearly.

Code Context:
{code_context}

Provide a clear, direct answer and mention relevant files when helpful."""
        
        try:
            answer = self.llm_service.generate_text(prompt)
            if answer and answer.lower().startswith("error:"):
                fallback_summary = self._generate_local_summary(project_name)
                if fallback_summary:
                    answer = fallback_summary
            generic_markers = [
                "i don't see any code",
                "please share the code",
                "you haven't provided",
                "no information about your project",
                "no information about the codebase",
                "don't have any information"
            ]
            if answer and any(marker in answer.lower() for marker in generic_markers):
                fallback_summary = self._generate_local_summary(project_name)
                if fallback_summary:
                    answer = fallback_summary
            return {
                'answer': answer,
                'sources': source_names,
                'num_sources': len(source_names)
            }
        except Exception as e:
            fallback_summary = self._generate_local_summary(project_name)
            return {
                'answer': fallback_summary or f"Error: {str(e)}",
                'sources': source_names if fallback_summary else [],
                'num_sources': len(source_names) if fallback_summary else 0
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
