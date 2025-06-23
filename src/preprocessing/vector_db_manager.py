import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VectorDBManager:
    """Manage Qdrant vector database operations with Azure AI embeddings"""
    
    def __init__(self, collection_name: str = "documents"):
        # Initialize Qdrant client (local instance)
        self.client = QdrantClient(
            host="localhost", 
            port=6333,
            # For cloud instance, use:
            # url="your-qdrant-cloud-url",
            # api_key="your-api-key"
        )
        self.collection_name = collection_name
        self.vector_size = 3072  # Azure OpenAI text-embedding-3-large dimension
        
        # Initialize Azure AI Inference Embeddings Client
        self.embeddings_client = self._initialize_embeddings_client()
    
    def _initialize_embeddings_client(self):
        """Initialize Azure AI Inference Embeddings Client"""
        try:
            # Get Azure credentials from environment variables
            endpoint = os.getenv("AZURE_EMBEDDINGS_BASE_URL")
            api_key = os.getenv("AZURE_EMBEDDINGS_API_KEY")
            
            if not endpoint or not api_key:
                logger.warning("Azure AI credentials not found in environment variables")
                return None
            
            client = AzureOpenAI(
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint,
                api_key=api_key
            )
            logger.info("Azure AI Embeddings Client initialized successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Embeddings Client: {e}")
            return None

    def create_embedding(self, text: str, model: str = "text-embedding-3-large") -> List[float]:
        """Create embedding for given text using Azure AI Inference"""
        if not self.embeddings_client:
            raise ValueError("Azure AI Embeddings Client not initialized. Check your credentials.")
        
        try:
            response = self.embeddings_client.embeddings.create(
                input=[text],
                model=model
            )
            
            if response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                logger.debug(f"Created embedding with {len(embedding)} dimensions")
                return embedding
            else:
                raise ValueError("No embedding data received from Azure AI")
                
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise
    
    def initialize_collection(self):
        """Initialize or recreate the collection"""
        try:
            # Delete existing collection if it exists
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted existing collection: {self.collection_name}")
        except UnexpectedResponse:
            # Collection doesn't exist, which is fine
            pass
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            )
        )
        logger.info(f"Created new collection: {self.collection_name}")

    def add_document(self, doc_id: str, text: str, embedding: List[float] = None, 
                    metadata: Dict[str, Any] = None):
        """Add a single document with id, text, and embedding to the collection"""
        if metadata is None:
            metadata = {}
        
        # Create embedding if not provided
        if embedding is None:
            embedding = self.create_embedding(text)
        
        # Add the document text to metadata
        full_metadata = {**metadata, "document": text}
        
        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload=full_metadata
        )
        
        # Upload point to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        logger.info(f"Added document with ID: {doc_id}")
        return doc_id
    
    def add_document_with_text(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """Convenience method to add document with automatic embedding generation"""
        return self.add_document(doc_id, text, embedding=None, metadata=metadata)
    
    def search_similar_by_text(self, query_text: str, n_results: int = 5, 
                              filter_conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for similar documents using text query (creates embedding automatically)"""
        query_embedding = self.create_embedding(query_text)
        return self.search_similar(query_embedding, n_results, filter_conditions)
    
    def search_similar(self, query_embedding: List[float], n_results: int = 5, 
                      filter_conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for similar documents"""
        
        # Build filter if provided
        query_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)
        
        # Perform search
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=query_filter
        )
        
        # Format results to match ChromaDB-style output
        documents = []
        metadatas = []
        distances = []
        ids = []
        
        for result in search_results:
            # Extract document text from payload
            payload = result.payload
            documents.append(payload.get("document", ""))
            
            # Remove document from metadata to avoid duplication
            metadata = {k: v for k, v in payload.items() if k != "document"}
            metadatas.append(metadata)
            
            # Convert score to distance (Qdrant returns similarity score, we want distance)
            distances.append(result.score)
            ids.append(str(result.id))
        
        return {
            "documents": [documents],
            "metadatas": [metadatas], 
            "score": [distances],
            "ids": [ids]
        }
    
    
    def delete_documents(self, ids: List[str]):
        """Delete documents by IDs"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )
        logger.info(f"Deleted {len(ids)} documents from collection")
    
    def update_document(self, doc_id: str, document: str, embedding: List[float], 
                       metadata: Dict[str, Any]):
        """Update a single document"""
        full_metadata = {**metadata, "document": document}
        
        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload=full_metadata
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        logger.info(f"Updated document with ID: {doc_id}")