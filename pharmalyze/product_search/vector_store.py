# product_search/vector_store.py
from pathlib import Path
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from django.conf import settings
import numpy as np
from typing import List, Dict, Any

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(Path(settings.BASE_DIR) / "vector_db"),
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        self._initialize_collections()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def _initialize_collections(self):
        """Initialize or get existing collections"""
        self.product_collection = self.client.get_or_create_collection(
            name="products",
            metadata={"description": "Product database with embeddings"}
        )
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge",
            metadata={"description": "Knowledge base with embeddings"}
        )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI's API"""
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def add_product(self, product_id: str, product_data: Dict[str, Any]):
        """Add product to vector store"""
        # Create embedding from product name and description
        text_for_embedding = f"{product_data['name']} {product_data['description']} {product_data['category']}"
        embedding = self.get_embedding(text_for_embedding)
        
        # Add to collection
        self.product_collection.add(
            ids=[str(product_id)],
            embeddings=[embedding],
            metadatas=[product_data],
            documents=[text_for_embedding]
        )
        
        return embedding

    def add_knowledge(self, knowledge_id: str, knowledge_data: Dict[str, Any]):
        """Add knowledge entry to vector store"""
        text_for_embedding = f"{knowledge_data['title']} {knowledge_data['content']}"
        embedding = self.get_embedding(text_for_embedding)
        
        self.knowledge_collection.add(
            ids=[str(knowledge_id)],
            embeddings=[embedding],
            metadatas=[knowledge_data],
            documents=[text_for_embedding]
        )
        
        return embedding

    def semantic_search(self, query: str, collection_name: str = "products", 
                       n_results: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Perform semantic search with similarity threshold"""
        query_embedding = self.get_embedding(query)
        collection = self.client.get_collection(collection_name)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Filter results based on similarity threshold
        distances = results['distances'][0]
        filtered_indices = [i for i, d in enumerate(distances) if (1 - d) >= threshold]
        
        filtered_results = {
            'ids': [results['ids'][0][i] for i in filtered_indices],
            'distances': [distances[i] for i in filtered_indices],
            'metadatas': [results['metadatas'][0][i] for i in filtered_indices],
            'documents': [results['documents'][0][i] for i in filtered_indices]
        }
        
        return filtered_results