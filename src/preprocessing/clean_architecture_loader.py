"""
Document Loader for CleanArchitecture Repository
==================================================

This module provides comprehensive document loading functionality specifically designed
for processing the ardalis/CleanArchitecture repository. It includes specialized loaders
for C# code files, documentation, configuration files, and project structure analysis.

Features:
- Contextual document chunking following RAG best practices
- Multi-threaded processing for large repositories
- Intelligent file type detection and specialized processing
- Metadata extraction including file types
- Integration-ready output for Semantic Kernel vector stores

Author: Generated for RAG Workshop
License: MIT
"""


import logging
import json
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Generator
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party imports
from tqdm import tqdm
import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Enhanced metadata for documents processed from CleanArchitecture repository."""
    source: str
    file_type: str
    token_count: int = 0
    chunk_index: int = 0
    total_chunks: int = 1
    


class SimpleDirectoryLoader:
    """Enhanced directory loader with CleanArchitecture-specific processing."""
    
    FILE_TYPE_PATTERNS = {
        'csharp': ['*.cs'],
        'project': ['*.csproj', '*.sln'],
        'config': ['*.json', '*.xml', '*.yml', '*.yaml', 'appsettings*.json'],
        'documentation': ['*.md', '*.rst', '*.txt'],
        'web': ['*.html', '*.css', '*.js', '*.ts'],
        'test': ['*test*.cs', '*Test*.cs', '*Tests*.cs'],
        'migration': ['*Migration*.cs', '*migration*.cs']
    }
    
    def __init__(self, base_path: Union[str, Path], max_workers: int = 4):
        self.base_path = Path(base_path)
        self.max_workers = max_workers
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def identify_file_type(self, file_path: Path) -> str:
        """Identify file type based on patterns."""
        file_name = file_path.name
        
        for file_type, patterns in self.FILE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if fnmatch.fnmatch(file_name, pattern):
                    return file_type
        
        return 'other'
    
    
    def load_file_content(self, file_path: Path) -> Optional[str]:
        """Load file content with encoding detection."""
        try:
            with open(file_path, 'r', encoding="utf-8", errors='replace') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            return None
    
    def create_enhanced_metadata(self, file_path: Path, content: str, chunk_index: int = 0, total_chunks: int = 1) -> DocumentMetadata:
        """Create enhanced metadata for a document."""
        file_type = self.identify_file_type(file_path)
        
        file_type = self.identify_file_type(file_path)
        
        # Find the CleanArchitecture-main folder in the path
        path_parts = file_path.parts
        try:
            # Find the index of CleanArchitecture-main in the path
            clean_arch_index = next(i for i, part in enumerate(path_parts) if 'CleanArchitecture' in part)
            # Create path starting from CleanArchitecture-main
            relative_parts = path_parts[clean_arch_index:]
            source_path = '\\'.join(relative_parts)
        except StopIteration:
            # Fallback if CleanArchitecture-main not found in path
            source_path = str(file_path)
        
        metadata = DocumentMetadata(
            source=source_path,
            file_type=file_type,
            token_count=len(self.tokenizer.encode(content)),
            chunk_index=chunk_index,
            total_chunks=total_chunks
        )
        
        return metadata
    
    def chunk_content(self, content: str, max_tokens: int = 1000, overlap_tokens: int = 100) -> List[str]:
        """Chunk content with token-based splitting and overlap."""
        self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_tokens,
                chunk_overlap=overlap_tokens,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        
        return self.text_splitter.split_text(content)
    
    def add_contextual_prefix(self, content: str, metadata: DocumentMetadata) -> str:
        """Add contextual prefix to content following RAG best practices."""
        context_parts = []
        
        # File context
        context_parts.append(f"File: {Path(metadata.source).name}")
        context_parts.append(f"Type: {metadata.file_type}")
        
        # Chunk context
        if metadata.total_chunks > 1:
            context_parts.append(f"Part {metadata.chunk_index + 1} of {metadata.total_chunks}")
        
        context_prefix = f"[{' | '.join(context_parts)}]\\n\\n"
        return context_prefix + content
    
    def process_file(self, file_path: Path) -> List[Document]:
        """Process a single file into one or more documents."""
        try:
            content = self.load_file_content(file_path)
            if not content:
                return []
            
            # Chunk content
            chunks = self.chunk_content(content)
            documents = []
            
            for i, chunk in enumerate(chunks):
                # Create metadata
                metadata = self.create_enhanced_metadata(file_path, chunk, i, len(chunks))
                
                # Add contextual prefix
                enhanced_content = self.add_contextual_prefix(chunk, metadata)
                
                # Create document
                doc = Document(
                    page_content=enhanced_content,
                    metadata=asdict(metadata)
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def get_files_to_process(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> List[Path]:
        """Get list of files to process with filtering."""
        if include_patterns is None:
            include_patterns = ['*.cs', '*.md', '*.json', '*.xml', '*.txt', '*.csproj', '*.sln']
        
        if exclude_patterns is None:
            exclude_patterns = [
                '**/bin/**', '**/obj/**', '**/.git/**', '**/packages/**',
                '**/node_modules/**', '**/.vs/**', '**/wwwroot/lib/**'
            ]
        
        all_files = []
        for pattern in include_patterns:
            all_files.extend(self.base_path.rglob(pattern))
        
        # Filter out excluded patterns
        filtered_files = []
        for file_path in all_files:
            file_path_str = str(file_path)
            
            # Check if file should be excluded
            should_exclude = False
            for exclude_pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path_str, exclude_pattern):
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(file_path)
        
        return filtered_files
    
    def load_documents(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None, 
                      show_progress: bool = True) -> List[Document]:
        """Load all documents from the repository."""
        files_to_process = self.get_files_to_process(include_patterns, exclude_patterns)
        
        logger.info(f"Processing {len(files_to_process)} files from {self.base_path}")
        
        all_documents = []
        
        if show_progress:
            progress_bar = tqdm(total=len(files_to_process), desc="Loading documents")
        
        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file_path): file_path 
                             for file_path in files_to_process}
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                    
                    if show_progress:
                        progress_bar.update(1)
                        progress_bar.set_postfix({
                            'docs': len(all_documents),
                            'current': file_path.name[:30]
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    if show_progress:
                        progress_bar.update(1)
        
        if show_progress:
            progress_bar.close()
        
        logger.info(f"Successfully loaded {len(all_documents)} documents")
        return all_documents


class CleanArchitectureDocumentLoader:
    """Main document loader for CleanArchitecture repository."""
    
    def __init__(self, repository_path: Optional[Union[str, Path]] = None):
        self.repository_path = Path(repository_path) if repository_path else None
        print(self.repository_path)
        
    def load_from_local(self, repository_path: Union[str, Path]) -> List[Document]:
        """Load documents from local repository path."""
        repo_path = Path(repository_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        loader = SimpleDirectoryLoader(repo_path)
        return loader.load_documents()
    
    
    def load(self) -> List[Document]:
        """Load documents from repository (local if available, otherwise Raise)."""
        if self.repository_path and self.repository_path.exists():
            logger.info(f"Loading from local repository: {self.repository_path}")
            return self.load_from_local(self.repository_path)
        else:
            raise ValueError("No valid repository path provided. Please clone the CleanArchitecture repository first.")

    
    def export_documents(self, documents: List[Document], output_path: Union[str, Path], 
                        format: str = 'json') -> None:
        """Export documents to file for later processing."""
        output_path = Path(output_path)
        
        if format == 'json':
            # Convert documents to serializable format
            doc_data = []
            for doc in documents:
                doc_data.append({
                    'page_content': doc.page_content,
                    'metadata': doc.metadata
                })
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
                
        elif format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for doc in documents:
                    doc_data = {
                        'page_content': doc.page_content,
                        'metadata': doc.metadata
                    }
                    f.write(json.dumps(doc_data, ensure_ascii=False) + '\\n')
        
        logger.info(f"Exported {len(documents)} documents to {output_path}")


import argparse

def main():
    """CLI for CleanArchitecture document loader."""
    parser = argparse.ArgumentParser(
        description="Load and export documents from a CleanArchitecture repository."
    )
    parser.add_argument(
        "--input-path", "-i", required=True, type=str,
        help="Path to the CleanArchitecture repository root."
    )
    parser.add_argument(
        "--output-path", "-o", required=True, type=str,
        help="Path to export the processed documents (json or jsonl)."
    )
    parser.add_argument(
        "--format", "-f", choices=["json", "jsonl"], default="json",
        help="Export format: json (default) or jsonl."
    )
    args = parser.parse_args()

    loader = CleanArchitectureDocumentLoader(args.input_path)
    documents = loader.load()
    loader.export_documents(documents, args.output_path, format=args.format)

if __name__ == "__main__":
    main()
