from app import create_app, db
from app.models.models import File, Chunk

app = create_app()

with app.app_context():
    print("="*60)
    print("DATABASE DIAGNOSTIC")
    print("="*60)
    
    # Check files
    files = File.query.all()
    print(f"\n✓ Total Files in Database: {len(files)}")
    
    if files:
        print("\nFiles List:")
        for f in files[:10]:  # Show first 10
            print(f"  - {f.filename} ({f.filetype})")
    
    # Check chunks
    chunks = Chunk.query.all()
    print(f"\n✓ Total Chunks in Database: {len(chunks)}")
    
    if chunks:
        print("\nChunk Distribution:")
        for f in files[:5]:  # Show first 5 files
            file_chunks = Chunk.query.filter_by(file_id=f.id).count()
            print(f"  - {f.filename}: {file_chunks} chunks")
    else:
        print("  ❌ NO CHUNKS FOUND!")
        print("  → This means chunking/embedding failed during upload")
    
    # Check FAISS index
    print("\n" + "="*60)
    print("VECTOR DB (FAISS) DIAGNOSTIC")
    print("="*60)
    
    try:
        from app.services.vector_service import VectorService
        vs = VectorService()
        print(f"✓ FAISS Index Total Vectors: {vs.index.ntotal}")
        
        if vs.index.ntotal == 0:
            print("  ❌ VECTOR DB IS EMPTY!")
            print("  → Embeddings were not generated during upload")
        else:
            print(f"  ✓ Good! {vs.index.ntotal} vectors stored")
    except Exception as e:
        print(f"  ❌ Error reading FAISS: {e}")
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    
    if len(files) > 0 and len(chunks) > 0 and vs.index.ntotal > 0:
        print("✓ Everything looks good! Search should work.")
    elif len(files) > 0 and len(chunks) == 0:
        print("❌ FILES uploaded but CHUNKS not created")
        print("→ Re-upload the ZIP after fixing embedding service")
    elif len(files) > 0 and len(chunks) > 0 and vs.index.ntotal == 0:
        print("❌ CHUNKS created but VECTORS not stored")
        print("→ Re-upload the ZIP after fixing vector service")
    else:
        print("❌ No data found. Please upload a ZIP file first.")
