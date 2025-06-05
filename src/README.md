# CleanArchitecture Document Loader for RAG Workshop

This directory contains a comprehensive document loading and processing system specifically designed for the [ardalis/CleanArchitecture](https://github.com/ardalis/CleanArchitecture) repository. It implements best practices from the RAG improvement guidelines and integrates with Semantic Kernel's vector store connectors.

## Overview

The system consists of two main components:

1. **Python Document Loader** (`clean_architecture_loader.py`) - Uses LangChain patterns to extract and process documents
2. **C# Vector Store Integration** (`CleanArchitectureDocumentService.cs`) - Integrates with Semantic Kernel for vector storage and retrieval

## Features

### Python Loader
- **Contextual Chunking**: Implements contextual retrieval patterns with meaningful chunk prefixes
- **Multi-threaded Processing**: Efficiently processes large repositories
- **Intelligent File Detection**: Recognizes C# code, configuration, documentation, and project files
- **Metadata Extraction**: Extracts namespaces, classes, methods, dependencies, and architecture patterns
- **Clean Architecture Aware**: Understands project layers (Core, Infrastructure, Web, UseCases, Tests)

### C# Integration
- **Semantic Kernel Compatible**: Works with all Semantic Kernel vector store connectors
- **Type-safe Models**: Strongly-typed document models with proper vector store annotations
- **Batch Processing**: Efficient embedding generation and storage
- **Search Capabilities**: Built-in vector search with metadata filtering

## Quick Start

### Prerequisites
- Python 3.8+
- .NET 8.0 or 9.0
- OpenAI API key (for embeddings)
- Qdrant (optional, for vector storage)

### Setup

1. **Automated Setup**:
   ```bash
   python setup.py
   ```

2. **Manual Setup**:
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Process the CleanArchitecture repository
   python clean_architecture_loader.py
   
   # Build the C# project
   dotnet build RAGWorkshop.DocumentProcessing.csproj
   ```

### Configuration

1. **Update `.env` file** with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

2. **Update `appsettings.json`** for C# configuration:
   ```json
   {
      "AzureOpenAIEmbedding": {
         "ApiKey": "Apikey",
         "Endpoint": "Endpoint",
         "EmbeddingModel": "text-embedding-3-large"
      },
   }
   ```

3. **Start Qdrant** (if using vector storage):
   ```bash
   docker pull qdrant/qdrant
   docker run -p 6333:6333 -p 6334:6334 -v "$(pwd)/data:/qdrant/storage" qdrant/qdrant
   ```

## Usage Examples

### Python Document Loading

```python
from clean_architecture_loader import CleanArchitectureDocumentLoader

# Load from remote repository
loader = CleanArchitectureDocumentLoader()
documents = loader.load()

# Load from local repository
loader = CleanArchitectureDocumentLoader("/path/to/local/repo")
documents = loader.load()

# Export for C# processing
loader.export_documents(documents, "clean_architecture_documents.json")
```

### C# Vector Storage and Search

```csharp

// Load documents processed by Python
var documentService = new CleanArchitectureDocumentService(embeddingService, logger);
var documents = await documentService.LoadDocumentsFromJsonAsync("clean_architecture_documents.json");

// Generate embeddings
await documentService.GenerateEmbeddingsAsync(documents);

// Store in vector database
var collection = vectorStore.GetCollection<string, CleanArchitectureDocument>("cleanarchitecture");
await documentService.StoreDocumentsAsync(collection, documents);

// Search for relevant documents
var results = await documentService.SearchDocumentsAsync(collection, 
    "How to implement repository pattern?");
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

## Architecture Patterns Detected

The system automatically identifies common Clean Architecture patterns:

- **Controllers**: Web API controllers and endpoints
- **Repositories**: Data access repositories
- **Services**: Application and domain services
- **Entities**: Domain entities and aggregates
- **Use Cases**: Application use cases and handlers
- **Configurations**: Dependency injection and service configurations

## Project Layer Classification

Documents are automatically classified into Clean Architecture layers:

- **Core**: Domain models, entities, interfaces
- **Infrastructure**: Data access, external services
- **Web**: Controllers, endpoints, UI
- **UseCases**: Application services, handlers
- **Tests**: Unit tests, integration tests

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
