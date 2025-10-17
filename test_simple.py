"""
Simple test for the project without heavy dependencies
Tests the basic functionality without FAISS/sentence-transformers
"""

def test_basic_functionality():
    """Test basic project functionality without RAG dependencies."""
    print("🧪 Testing Basic Project Functionality")
    print("=" * 50)
    
    try:
        # Test resolver without RAG
        from resolver import QueryResolver
        
        print("✅ Resolver imported successfully")
        
        # Create resolver with RAG disabled
        resolver = QueryResolver(use_rag=False)
        print("✅ Resolver initialized (keyword mode)")
        
        # Test knowledge base loading
        kb_size = len(resolver.knowledge_base)
        print(f"✅ Knowledge base loaded: {kb_size} entries")
        
        # Test query resolution
        test_queries = [
            "My phone screen is cracked",
            "I can't log into my account", 
            "My phone is not charging",
            "I'm having network issues"
        ]
        
        print("\n🔍 Testing Query Resolution:")
        for query in test_queries:
            result = resolver.resolve_query(query)
            print(f"   '{query}' → {result['category']} (confidence: {result['confidence']:.2f})")
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_main_app_imports():
    """Test that main app can be imported without errors."""
    print("\n🧪 Testing Main App Imports")
    print("=" * 50)
    
    try:
        # Test individual modules
        from categorizer import TicketCategorizer
        from tagger import TicketTagger
        from notifier import Notifier
        from sheets_client import GoogleSheetsClient
        from chatbot import Chatbot
        
        print("✅ All core modules imported successfully")
        
        # Test resolver (should work without RAG)
        from resolver import QueryResolver
        resolver = QueryResolver(use_rag=False)
        print("✅ Resolver works in keyword mode")
        
        print("\n✅ Main app imports test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🚀 Simple Project Test Suite")
    print("=" * 50)
    
    # Test 1: Basic functionality
    test1_passed = test_basic_functionality()
    
    # Test 2: Main app imports
    test2_passed = test_main_app_imports()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Basic Functionality: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Main App Imports: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Basic functionality works! You can run the app.")
        print("\n📝 Next steps:")
        print("   1. Install updated dependencies: pip install -r requirements.txt")
        print("   2. Run the app: streamlit run main.py")
        print("   3. RAG will be disabled initially, but keyword search works")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
