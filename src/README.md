# CleanArchitecture Document Loader for RAG Workshop

This directory contains a comprehensive document loading and processing system specifically designed for the [ardalis/CleanArchitecture](https://github.com/ardalis/CleanArchitecture) repository. 

## Overview

The system consists of two main components:

1. **Python Document Loader** (`clean_architecture_loader.py`) - Uses LangChain patterns to extract and process documents
2. **Vector DB Initializer** (`initialize_vector_db.py`) - Loads processed documents into a Qdrant vector database

## Features

### Python Loader
- **Contextual Chunking**: Implements contextual retrieval patterns with meaningful chunk prefixes
- **Multi-threaded Processing**: Efficiently processes large repositories
- **Intelligent File Detection**: Recognizes C# code, configuration, documentation, and project files
- **Metadata Extraction**: Extracts namespaces, classes, methods, dependencies, and architecture patterns
- **Clean Architecture Aware**: Understands project layers (Core, Infrastructure, Web, UseCases, Tests)


## Quick Start

### Prerequisites
- Docker (for Qdrant vector storage)
- Python 3.11
- Azure API key (for embeddings)
- Qdrant 

### Setup
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt


### Configuration

1. **Update `.env` file** with your Azure API key and endpoint:
   ```
   AZURE_EMBEDDINGS_API_KEY=your-api-key-here
   AZURE_EMBEDDINGS_BASE_URL=https://your-azure-endpoint.openai.azure.com/
   ```

3. **Start Qdrant** :
   ```bash
   docker pull qdrant/qdrant
   docker run -p 6333:6333 -p 6334:6334 -v "$(pwd)/data:/qdrant/storage" qdrant/qdrant
   ```

## Usage Examples

### Python Document Loading

```bash
python ./src/preprocessing/clean_architecture_loader.py --input-path './path/to/clean_architecture_repo' --output-path ./path/to/clean_architecture_documents.json

```
### Initialize Vector Database

```bash
python ./src/preprocessing/initialize_vector_db.py --json "path/to/clean_architecture_documents.json" --collection cleanarchitecture --recreate

```

## Document Structure

Each processed document includes rich metadata:

```json
{
  "page_content": "[File: EfRepository.cs | Type: csharp | Layer: Infrastructure | Pattern: Repository]\n\n// Enhanced content with context...",
  "metadata": {
    "source": "/path/to/file.cs",
    "file_type": "csharp",
    "token_count": 450,
    "chunk_index": 0,
    "total_chunks": 1
  }
}
```

## Advanced Features

### Contextual Prefixes
Following RAG best practices, each chunk includes contextual information:
```
[File: ContributorController.cs | Type: csharp | Layer: Web | Pattern: Controller | Classes: ContributorController | Part 1 of 2]

// Original content follows...
```

### Intelligent Chunking
- Token-based chunking with configurable overlap
- Preserves code structure and readability
- Maintains context across chunk

## Extending the Loader

### Adding New File Types
```python
FILE_TYPE_PATTERNS = {
    'typescript': ['*.ts', '*.tsx'],
    'razor': ['*.razor', '*.cshtml'],
    # Add your patterns here
}
```

### Custom Metadata Extraction
```python
def extract_custom_info(self, content: str, file_path: Path) -> Dict[str, Any]:
    # Implement your custom analysis
    return custom_metadata
```

## License

MIT License - See repository root for details.
