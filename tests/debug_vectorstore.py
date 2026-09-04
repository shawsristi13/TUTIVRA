from dotenv import load_dotenv; load_dotenv()
import sys, json, os
sys.path.insert(0,'.')
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever

RAG_STORAGE = 'rag_storage'
vs = VectorStore()
vs.load(RAG_STORAGE)
print('index ntotal:', vs.index.ntotal)
print('has documents:', hasattr(vs, 'documents'))
if hasattr(vs, 'documents'):
    print('document count:', len(vs.documents))
    print('first doc keys:', list(vs.documents[0].keys()) if vs.documents else 'EMPTY')
else:
    # documents.json exists?
    dp = os.path.join(RAG_STORAGE, 'documents.json')
    print('documents.json exists:', os.path.exists(dp))
    if os.path.exists(dp):
        with open(dp) as f:
            docs = json.load(f)
        print('docs in file:', len(docs))
        # VectorStore.__init__ sets self.documents = []
        # load() populates it - let's check the source
        import inspect
        src = inspect.getsource(vs.__class__)
        for i, line in enumerate(src.split('\n'),1):
            if 'document' in line.lower():
                print(f'  {i}: {line}')

# Try retrieving directly
r = Retriever(vs)
results = r.retrieve('binary search time complexity', top_k=3)
print('retrieve results:', len(results))
if results:
    print('top result score:', results[0].get('score'))
    print('top result keys:', list(results[0].keys()))
