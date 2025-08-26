# 🚀 Enhanced RAG + Intelligent AI Manufacturing Pipeline

An advanced AI-powered 3D CAD generation system that combines Retrieval-Augmented Generation (RAG) with intelligent reasoning to create CadQuery models through natural conversation.

## ✨ Key Features

### 🧠 **Object-First Intelligent Conversation Flow**
- **Immediate object detection** from user's first message
- **Smart parameter extraction** from reference examples
- **Context-aware questioning** based on actual object requirements
- **Adaptive code generation** with feature removal/addition

### 🔄 **Dual-Mode Generation System**
- **RAG Mode**: Uses hierarchical reference examples when relevant
- **Intelligent Reasoning**: Falls back to engineering principles for novel designs
- **Toggle Control**: Switch between modes to compare approaches

### 📚 **Hierarchical Reference Library**
- 16+ pre-built references across 4 complexity levels
- Semantic search with similarity scoring
- Automatic complexity-based selection
- Categories: Primitive, Functional, Mathematical, Manufacturing

## 🎯 System Innovation

### Traditional CAD Chatbot Flow ❌
```
User: "I want a cup"
Bot: "What dimensions?" (generic)
User: "100mm height, 60mm diameter"
Bot: "What thickness?" (still generic)
→ Finally searches for examples
→ Often fails to match
```

### Our Object-First Flow ✅
```
User: "I want a cup"
→ Immediate RAG search for "cup"
→ Finds "mug" reference (0.534 similarity)
→ Extracts actual parameters: mug_radius, mug_height, handle
Bot: "For your cup, what radius (default 40mm) and height (default 90mm)? Want a handle?"
→ Generates using adapted reference
```

## 📋 Prerequisites

- Python 3.11
- [Ollama](https://ollama.ai/) installed and running
- CUDA-capable GPU (optional, for faster inference)
- 8GB+ RAM recommended

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/WKJBryan/Text-to-3D.git
cd Text-to-3D
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install and start Ollama**
```bash
# Install Ollama (Mac/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull the default model
ollama pull llama3.1:8b
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your preferences
```

## 🚀 Quick Start

### Desktop Application
```bash
python main.py
```

### Test Scripts
```bash
# Test RAG search functionality
python test_rag_search.py

# Test handle removal feature
python test_handle_removal.py

# Test ring generation
python test_ring_generation.py
```

## 💡 Usage Examples

### Simple Object Generation
```
User: "I need a gear"
Assistant: "For your spur gear, how many teeth? (default: 20)"
User: "24 teeth"
Assistant: "What module? (default: 2.5mm)"
User: "3mm"
→ Generates involute gear with exact specifications
```

### Feature Removal
```
User: "I want a cup"
Assistant: "What height and radius for your cup? Do you want a handle?"
User: "100mm height, 30mm radius, no handle"
→ Generates cup without handle code
```

### Complex Objects
```
User: "I need a phone stand"
→ Finds phone_stand reference
→ Asks about angle, phone size, charging port
→ Generates with stability features and cable management
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            Desktop UI (CustomTkinter)        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│     Intelligent Conversation Assistant       │
│  • Object-first detection                    │
│  • Smart parameter extraction                │
│  • Context-aware questioning                 │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐ ┌────────▼────────┐
│  RAG Generator │ │   LLM Engine    │
│ • Semantic     │ │ • Ollama API    │
│   search       │ │ • Generation    │
│ • Code adapt   │ │ • Temperature   │
└───────┬────────┘ └─────────────────┘
        │
┌───────▼────────────────────────────┐
│     Reference Library               │
│ • Simple: box, cylinder, sphere    │
│ • Medium: phone_stand, mug, bracket│
│ • Complex: gear, spring, thread    │
│ • Advanced: living_hinge, snap_fit │
└────────────────────────────────────┘
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Model Configuration
DEFAULT_MODEL=llama3.1:8b
PERFORMANCE_MODE=balanced  # fast, balanced, quality

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.3
VECTOR_SEARCH_TOP_K=3

# UI Configuration
WINDOW_SIZE=900x700
THEME=dark

# Export Configuration
EXPORT_DIRECTORY=./exports
```

### Performance Modes
- **fast**: Quick responses, smaller context (512 tokens)
- **balanced**: Default, good for most uses (1024 tokens)
- **quality**: Best results, larger context (2048 tokens)

## 📁 Project Structure

```
enhanced-rag-manufacturing/
├── main.py                 # Entry point
├── desktop_app.py          # UI application
├── .env                    # Configuration
├── src/
│   ├── assistant.py        # Conversation logic
│   ├── llm_engine.py       # Ollama interface
│   └── generation/
│       ├── RAG_generator.py      # Code generation
│       ├── reference_library.py  # Example library
│       └── export.py             # STL/STEP export
├── exports/                # Generated models
├── embeddings/             # Cached embeddings
└── tests/                  # Test scripts
```

## 🔍 How RAG Works

### 1. **Semantic Search**
- User input → Embedding model → Vector representation
- Searches reference library using FAISS
- Returns top-k similar examples with scores

### 2. **Similarity-Based Strategy**
```
≥ 0.5  → Direct adaptation (very similar)
0.3-0.5 → Pattern combination (good match)
0.2-0.3 → Category adaptation (related)
< 0.2  → Intelligent reasoning (no match)
```

### 3. **Code Adaptation**
- LLM adapts reference code to user specifications
- Handles feature removal (no handle, plain, simple)
- Updates dimensions and parameters
- Maintains manufacturing constraints

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Model Not Found
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.1:8b
```

### Slow Generation
- Switch to "fast" mode in .env
- Use smaller model (llama2:7b)
- Reduce VECTOR_SEARCH_TOP_K
- Ensure GPU acceleration is working

### RAG Search Issues
```bash
# Rebuild embeddings
python -c "from src.generation.RAG_generator import EnhancedRAGCADGenerator; g = EnhancedRAGCADGenerator(None); g.rebuild_embeddings()"
```

## 🚧 Advanced Features

### Adding Custom References
```python
from src.generation.RAG_generator import EnhancedRAGCADGenerator

generator = EnhancedRAGCADGenerator(llm_engine)
generator.add_reference_example(
    name="custom_part",
    description="My custom mechanical part",
    code=cadquery_code,
    complexity="medium",
    category="functional"
)
```

### Custom LLM Models
```bash
# Use different Ollama model
ollama pull mistral:latest

# Update .env
DEFAULT_MODEL=mistral:latest
```

## 📊 Performance Metrics

- **Object Detection**: ~100ms
- **RAG Search**: ~200ms
- **LLM Generation**: 2-10s (depends on model/mode)
- **Code Execution**: ~500ms
- **Total Response**: 3-15s typical

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional reference examples
- Support for more CAD formats
- Multi-language support
- Cloud deployment options
- Web interface

## 📄 License

GNU AFFERO GENERAL PUBLIC LICENSE Version 3 - See LICENSE file for details

## 🙏 Acknowledgments

- [CadQuery](https://github.com/CadQuery/cadquery) - Parametric CAD scripting
- [Ollama](https://ollama.ai/) - Local LLM deployment
- [Sentence-Transformers](https://www.sbert.net/) - Semantic embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: bryan_wang@mymail.sutd.edu.sg

## 🔮 Future Roadmap

- [ ] Assembly support (multi-part objects)
- [ ] Constraint solver integration
- [ ] Real-time collaborative design
- [ ] Voice input support
- [ ] AR/VR visualization
- [ ] Cloud-based rendering
- [ ] Fine-tuned CAD-specific LLM

---

**Built with ❤️ for the maker community**
