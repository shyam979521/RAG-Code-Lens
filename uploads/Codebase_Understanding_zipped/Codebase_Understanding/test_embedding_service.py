from app.services.embedding_service import EmbeddingService

print("="*60)
print("TESTING EMBEDDING SERVICE")
print("="*60)

es = EmbeddingService()

# Test 1: Document embedding
print("\nTest 1: Document Embedding (for file chunks)")
try:
    vec = es.get_embedding("def login(username, password): return True", task_type="retrieval_document")
    if vec:
        print(f"  ✓ SUCCESS! Vector length: {len(vec)}")
    else:
        print(f"  ❌ FAILED: Returned None")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 2: Query embedding
print("\nTest 2: Query Embedding (for search)")
try:
    vec = es.get_embedding("where is login logic?", task_type="retrieval_query")
    if vec:
        print(f"  ✓ SUCCESS! Vector length: {len(vec)}")
    else:
        print(f"  ❌ FAILED: Returned None")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

print("\n" + "="*60)
print("If both tests passed, you're ready to upload!")
print("If failed, check the error message above.")
print("="*60)
