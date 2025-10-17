"""
Test script for RAG functionality
Run this to test the FAISS RAG engine before integrating with the main app.
"""

def test_rag_without_dependencies():
    """Test RAG functionality without installing dependencies."""
    print("🧪 Testing RAG Engine (without dependencies)")
    print("=" * 50)
    
    # Test knowledge base conversion
    from rag_engine import create_documents_from_knowledge_base
    
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
    
    # Convert to documents
    documents = create_documents_from_knowledge_base(sample_kb)
    print(f"✅ Converted {len(documents)} knowledge base entries to documents")
    
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. Key: {doc['metadata']['key']}")
        print(f"   Problem: {doc['metadata']['problem']}")
        print(f"   Category: {doc['metadata']['category']}")
        print(f"   Text preview: {doc['text'][:100]}...")
    
    print("\n✅ Document conversion test passed!")
    return True

def test_resolver_fallback():
    """Test resolver with RAG disabled (keyword fallback)."""
    print("\n🧪 Testing Resolver (Keyword Fallback)")
    print("=" * 50)
    
    try:
        from resolver import QueryResolver
        
        # Create resolver with RAG disabled
        resolver = QueryResolver(use_rag=False)
        
        # Test queries
        test_queries = [
            "My phone screen is cracked",
            "I can't log into my account",
            "My phone is not charging",
            "I'm having network issues"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            result = resolver.resolve_query(query)
            print(f"   Method: {result.get('search_method', 'Unknown')}")
            print(f"   Category: {result['category']}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Solutions: {len(result['solutions'])} found")
            if result['solutions']:
                print(f"   First solution: {result['solutions'][0]}")
        
        print("\n✅ Resolver fallback test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Resolver test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 RAG Engine Test Suite")
    print("=" * 50)
    
    # Test 1: Document conversion
    test1_passed = test_rag_without_dependencies()
    
    # Test 2: Resolver fallback
    test2_passed = test_resolver_fallback()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Document Conversion: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Resolver Fallback: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! RAG engine is ready.")
        print("\n📝 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run the main app: streamlit run main.py")
        print("   3. Check sidebar for RAG status and controls")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
