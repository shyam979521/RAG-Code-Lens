class ChunkService:
    def chunk_text(self, text, chunk_size=4000, overlap=400):
        """
        Splits text into chunks of approximately chunk_size characters.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end == text_len:
                break
                
            start += (chunk_size - overlap)
            
        return chunks
