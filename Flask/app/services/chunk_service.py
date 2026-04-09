class ChunkService:
    def chunk_text(self, text, chunk_size=4000, overlap=400):
        if not text: return []
        chunks, start = [], 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text): break
            start += (chunk_size - overlap)
        return chunks
