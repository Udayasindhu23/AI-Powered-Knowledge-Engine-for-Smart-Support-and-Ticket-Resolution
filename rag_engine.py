"""
Advanced RAG (Retrieval-Augmented Generation) Engine with FAISS
Provides semantic search capabilities for the knowledge base using vector embeddings.
"""

import os
import json
import pickle
from typing import List, Dict, Tuple, Optional
import pandas as pd
from datetime import datetime

# Try to import optional dependencies
try:
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAG dependencies not available: {e}")
    print("Falling back to keyword-based search")
    RAG_AVAILABLE = False
    # Create dummy classes for type hints
    class SentenceTransformer:
        pass
    class IndexFlatIP:
        pass


class RAGEngine:
    """
    Advanced RAG engine using FAISS for vector similarity search.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "data/faiss_index"):
        """
        Initialize the RAG engine.
        
        Args:
            model_name: Sentence transformer model name
            index_path: Path to store FAISS index
        """
        self.model_name = model_name
        self.index_path = index_path
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.available = RAG_AVAILABLE
        
        if not self.available:
            print("⚠️ RAG engine initialized but dependencies not available")
            return
        
        # Create data directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load or create index
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        index_file = os.path.join(self.index_path, "faiss_index.bin")
        metadata_file = os.path.join(self.index_path, "metadata.json")
        
        # Load embedding model
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            print(f"✅ Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            # Mark RAG unavailable to prevent downstream calls
            self.available = False
            return
        
        # Try to load existing index
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                self.index = faiss.read_index(index_file)
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                print(f"✅ Loaded existing FAISS index with {len(self.documents)} documents")
                return
            except Exception as e:
                print(f"⚠️ Error loading existing index: {e}")
        
        # Create new index
        self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        try:
            if not self.embedding_model:
                print("❌ Cannot create FAISS index: embedding model not loaded")
                self.available = False
                return
            # Get embedding dimension
            sample_text = "This is a sample text for embedding dimension calculation."
            sample_embedding = self.embedding_model.encode([sample_text])
            dimension = sample_embedding.shape[1]
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            print(f"✅ Created new FAISS index with dimension {dimension}")
        except Exception as e:
            print(f"❌ Error creating FAISS index: {e}")
    
    def add_documents(self, documents: List[Dict], batch_size: int = 32):
        """
        Add documents to the FAISS index.
        
        Args:
            documents: List of document dictionaries with 'text', 'metadata' keys
            batch_size: Batch size for embedding generation
        """
        if not self.available:
            print("❌ RAG not available - dependencies missing")
            return
            
        if not self.embedding_model or not self.index:
            print("❌ Embedding model or index not initialized")
            return
        
        try:
            # Extract texts and metadata
            texts = []
            metadata_list = []
            
            for doc in documents:
                if 'text' in doc:
                    texts.append(doc['text'])
                    metadata_list.append(doc.get('metadata', {}))
            
            if not texts:
                print("⚠️ No texts found in documents")
                return
            
            # Generate embeddings in batches
            print(f"🔄 Generating embeddings for {len(texts)} documents...")
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=True)
                embeddings.append(batch_embeddings)
            
            # Concatenate all embeddings
            embeddings = np.vstack(embeddings)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            self.documents.extend(texts)
            self.metadata.extend(metadata_list)
            
            print(f"✅ Added {len(texts)} documents to FAISS index")
            
            # Save index and metadata
            self._save_index()
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
    
    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.3) -> List[Dict]:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents with scores and metadata
        """
        if not self.available:
            return []
            
        if not self.embedding_model or not self.index or len(self.documents) == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents) and score >= score_threshold:
                    results.append({
                        'text': self.documents[idx],
                        'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                        'score': float(score),
                        'index': int(idx)
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            return []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Save FAISS index
            index_file = os.path.join(self.index_path, "faiss_index.bin")
            faiss.write_index(self.index, index_file)
            
            # Save metadata
            metadata_file = os.path.join(self.index_path, "metadata.json")
            data = {
                'documents': self.documents,
                'metadata': self.metadata,
                'model_name': self.model_name,
                'created_at': datetime.now().isoformat(),
                'total_documents': len(self.documents)
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved FAISS index and metadata to {self.index_path}")
            
        except Exception as e:
            print(f"❌ Error saving index: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the current index."""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'model_name': self.model_name,
            'index_path': self.index_path
        }
    
    def rebuild_index(self, documents: List[Dict]):
        """Rebuild the entire index from scratch."""
        print("🔄 Rebuilding FAISS index...")
        
        # Clear existing data
        self.documents = []
        self.metadata = []
        
        # Create new index
        self._create_new_index()
        
        # Add all documents
        self.add_documents(documents)
        
        print("✅ FAISS index rebuilt successfully")


def create_documents_from_knowledge_base(kb: Dict) -> List[Dict]:
    """
    Convert knowledge base dictionary to document format for RAG.
    
    Args:
        kb: Knowledge base dictionary
        
    Returns:
        List of document dictionaries
    """
    documents = []
    
    for key, data in kb.items():
        # Create text content combining problem, keywords, and solutions
        text_parts = []
        
        if data.get('problem'):
            text_parts.append(f"Problem: {data['problem']}")
        
        if data.get('keywords'):
            keywords_text = ', '.join(data['keywords'])
            text_parts.append(f"Keywords: {keywords_text}")
        
        if data.get('solutions'):
            solutions_text = ' '.join(data['solutions'])
            text_parts.append(f"Solutions: {solutions_text}")
        
        # Combine all parts
        full_text = ' '.join(text_parts)
        
        # Create document
        doc = {
            'text': full_text,
            'metadata': {
                'key': key,
                'problem': data.get('problem', ''),
                'category': data.get('category', ''),
                'keywords': data.get('keywords', []),
                'solutions': data.get('solutions', [])
            }
        }
        
        documents.append(doc)
    
    return documents


def test_rag_engine():
    """Test the RAG engine with sample data."""
    # Sample knowledge base
    sample_kb = {
        "login_issues": {
            "problem": "Cannot login to account",
            "keywords": ["login", "signin", "password", "account"],
            "solutions": ["Reset password", "Check email", "Clear cache"],
            "category": "Account Issues"
        },
        "phone_screen": {
            "problem": "Phone screen not responding",
            "keywords": ["phone", "screen", "touch", "unresponsive"],
            "solutions": ["Restart phone", "Remove screen protector", "Update software"],
            "category": "Phone Issues"
        }
    }
    
    # Create RAG engine
    rag = RAGEngine()
    
    # Convert to documents
    documents = create_documents_from_knowledge_base(sample_kb)
    
    # Add documents
    rag.add_documents(documents)
    
    # Test search
    query = "My phone screen is not working"
    results = rag.search(query, top_k=3)
    
    print(f"\n🔍 Search results for: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"   Problem: {result['metadata']['problem']}")
        print(f"   Category: {result['metadata']['category']}")
        print(f"   Solutions: {result['metadata']['solutions']}")
    
    return rag


if __name__ == "__main__":
    # Run test
    test_rag_engine()
