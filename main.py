## 🚀 Updated Main Entry Point (main.py)
"""Enhanced RAG + Intelligent Reasoning AI Manufacturing Pipeline Entry Point"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from desktop_app import EnhancedDesktopApp

def main():
    print("🚀 Starting Enhanced RAG + Intelligent Reasoning AI Manufacturing Pipeline...")
    print("🧠 Enhanced RAG (Hierarchical) + Intelligent Reasoning mode enabled")
    print("🔧 Debug mode enabled for troubleshooting")
    
    try:
        print("📚 Initializing Enhanced RAG components...")
        print("   • Loading embedding model...")
        print("   • Building/loading hierarchical reference embeddings...")
        print("   • Setting up enhanced semantic search...")
        print("   • Preparing intelligent reasoning system...")
        
        app = EnhancedDesktopApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start Enhanced RAG system: {e}")
        print("\n📋 Enhanced RAG Troubleshooting:")
        print("1. Check if Ollama is running: ollama serve")
        print("2. Check if model is installed: ollama list")
        print("3. Install model if missing: ollama pull llama3.1:8b")
        print("4. Check .env file exists with Enhanced RAG settings")
        print("5. Ensure embedding model downloads (first run may be slow)")
        print("6. Check internet connection for sentence-transformers download")
        print("7. Verify Enhanced RAG dependencies: pip install sentence-transformers faiss-cpu")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()