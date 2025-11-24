# ExamGenie 📚

A little vibe coded tool I made for preparing for exams at NTNU while testing Antigravity.

The idea is to feed it all previous exams, and optionally context such as lecture slides/textbooks, and it will generate a study guide with comprehensive explanations and examples.

Use with care :D

## Features

- 📄 **PDF Extraction**: Extract text from multiple exam PDFs
- 🧠 **AI Topic Analysis**: Automatically identify and structure topics hierarchically
- 📖 **Detailed Explanations**: Generate comprehensive explanations with intuitive examples
- 🔍 **RAG Support**: Optional context from textbooks using vector search
- 📝 **PDF Output**: Beautiful study guides with table of contents
- ⚡ **Flexible Embeddings**: Support for external (OpenAI) or local (sentence-transformers) embeddings

## Installation

ExamGenie uses `uv` for package management. Install dependencies:

```bash
cd examgenie
uv sync
```

### System Requirements

For PDF generation, you need `pandoc` and a LaTeX distribution:

**macOS:**
```bash
brew install pandoc
brew install --cask mactex-no-gui
```

**Linux:**
```bash
sudo apt-get install pandoc texlive-latex-base texlive-latex-extra
```

## Configuration

Create a `.env` file in your project directory:

```bash
# Required: OpenRouter API key
OPENROUTER_API_KEY=your_api_key_here

# Optional: Model selection (defaults shown)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional: Embedding model
# For external embeddings (via OpenRouter):
EMBEDDING_MODEL=openai/text-embedding-3-large

# For local embeddings:
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Get your OpenRouter API key at [openrouter.ai](https://openrouter.ai)

## Usage

### Basic Analysis

Analyze exams and generate a study guide:

```bash
uv run examgenie analyze --exams-dir ./my_exams --output study_guide.pdf
```

### With Context Documents

Include textbooks or reference materials for enhanced explanations:

```bash
uv run examgenie analyze \
  --exams-dir ./my_exams \
  --context-dir ./textbooks \
  --output study_guide.pdf
```

### Options

- `--exams-dir PATH`: Directory containing exam PDFs (required)
- `--context-dir PATH`: Optional directory with context documents
- `--output PATH`: Output PDF path (default: `study_guide.pdf`)
- `--rebuild-index`: Force rebuild of RAG index
- `--db-dir PATH`: ChromaDB persistence directory (default: `.examgenie_db`)

### Help

```bash
uv run examgenie --help
uv run examgenie analyze --help
```

## How It Works

1. **PDF Extraction**: Extracts text from all exam PDFs in the specified directory
2. **Topic Analysis**: Uses LLM to identify and structure topics hierarchically
3. **Context Indexing** (optional): Embeds context documents in a vector database
4. **Explanation Generation**: For each topic, generates:
   - Detailed explanations
   - Key concepts
   - Intuitive examples and analogies
   - Related exam questions (with source references)
5. **PDF Generation**: Compiles everything into a formatted study guide

## Architecture

```
examgenie/
├── models.py              # Pydantic data models
├── llm_client.py          # OpenRouter API client
├── pdf_extractor.py       # PDF text extraction
├── rag_system.py          # Vector database & embeddings
├── topic_analyzer.py      # Topic extraction & structuring
├── explanation_generator.py  # Detailed explanations
├── output_generator.py    # PDF generation
└── main.py               # CLI interface
```

## Development

### Type Checking

ExamGenie uses modern Python 3.13+ syntax with strict type hints:
- `|` for unions instead of `Union`
- `| None` instead of `Optional`
- Built-in `dict`, `list` instead of `Dict`, `List`

### Code Style

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

## Example Output

The generated study guide includes:

- **Table of Contents**: Navigate topics easily
- **Hierarchical Structure**: Main topics → subtopics → explanations
- **Key Concepts**: Important points to remember
- **Examples**: Intuitive analogies and real-world applications
- **Example Questions**: Related questions from source exams with file references

## Troubleshooting

### PDF Generation Fails

If pypandoc fails to generate PDF, the tool will save a Markdown file instead. Ensure pandoc and LaTeX are properly installed.

### Embedding Errors

If external embeddings fail, the system will attempt to fall back to local sentence-transformers. Check your `EMBEDDING_MODEL` configuration and API key.

### Memory Issues

For large document sets, consider:
- Processing exams in smaller batches
- Using local embeddings instead of external
- Adjusting chunk size in `rag_system.py`

## License

MIT

## Contributing

Contributions welcome! Please ensure:
- Modern Python 3.13+ syntax
- Strict type hints
- Tests for new features
- Updated documentation
