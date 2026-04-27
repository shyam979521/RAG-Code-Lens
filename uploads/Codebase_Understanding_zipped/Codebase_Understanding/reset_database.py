from app import create_app, db
from app.models.models import File, Chunk, Dependency
import os

app = create_app()

print("="*60)
print("RESETTING DATABASE AND VECTOR STORE")
print("="*60)

with app.app_context():
    # Count current data
    file_count = File.query.count()
    chunk_count = Chunk.query.count()
    dep_count = Dependency.query.count()
    
    print(f"\nCurrent State:")
    print(f"  Files: {file_count}")
    print(f"  Chunks: {chunk_count}")
    print(f"  Dependencies: {dep_count}")
    
    # Delete all data
    print("\nDeleting all records...")
    Chunk.query.delete()
    Dependency.query.delete()
    File.query.delete()
    db.session.commit()
    print("  ✓ Database cleared")
    
    # Reset FAISS index
    print("\nResetting FAISS vector store...")
    try:
        from app.services.vector_service import VectorService
        vs = VectorService()
        vs.reset_index()
        print("  ✓ FAISS index reset")
    except Exception as e:
        print(f"  ❌ Error resetting FAISS: {e}")
    
    # Remove uploaded files
    print("\nCleaning workspace folder...")
    workspace = app.config['UPLOAD_FOLDER']
    if os.path.exists(workspace):
        import shutil
        shutil.rmtree(workspace)
        os.makedirs(workspace)
        print("  ✓ Workspace cleaned")
    
    print("\n" + "="*60)
    print("✓ RESET COMPLETE!")
    print("="*60)
    print("\nNow:")
    print("1. Make sure Flask server is running: python app.py")
    print("2. Go to: http://localhost:5000/upload")
    print("3. Upload your ZIP file again")
    print("4. Wait for processing to complete")
    print("5. Try Smart Search!")
