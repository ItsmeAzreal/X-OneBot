"""
RAG (Retrieval Augmented Generation) Search Service.
Provides semantic search over menu items, FAQs, and business information.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import logging
from app.config.settings import settings
from app.models import MenuItem, Business, MenuCategory
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RAGSearchService:
    """
    Semantic search using vector embeddings.
    
    Indexes:
    1. Menu items with descriptions
    2. FAQ questions and answers
    3. Business policies
    4. Dietary and allergen information
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize Qdrant client
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collection names
        self.collections = {
            "menu_items": "menu_items_v1",
            "faqs": "faqs_v1",
            "policies": "policies_v1"
        }
        
        # Initialize collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Create vector collections if they don't exist."""
        vector_size = 384  # Size for all-MiniLM-L6-v2
        
        for collection_name in self.collections.values():
            try:
                self.qdrant.get_collection(collection_name)
            except:
                # Collection doesn't exist, create it
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name}")
    
    def index_menu_items(self, business_id: int):
        """
        Index all menu items for a business.
        
        Creates searchable vectors from menu item names and descriptions.
        """
        # Get all menu items
        items = self.db.query(MenuItem).filter(
            MenuItem.business_id == business_id
        ).all()
        
        if not items:
            return
        
        points = []
        for item in items:
            # Create searchable text
            text = f"{item.name}. {item.description or ''}. "
            
            # Add dietary tags
            if item.dietary_tags:
                text += f"Dietary: {', '.join(item.dietary_tags)}. "
            
            # Add allergens
            if item.allergens:
                text += f"Allergens: {', '.join(item.allergens)}. "
            
            # Add price
            text += f"Price: ${item.base_price}"
            
            # Generate embedding
            embedding = self.embedder.encode(text)
            
            # Create point
            point = PointStruct(
                id=item.id,
                vector=embedding.tolist(),
                payload={
                    "business_id": business_id,
                    "item_id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.base_price,
                    "dietary_tags": item.dietary_tags,
                    "allergens": item.allergens,
                    "category_id": item.category_id,
                    "is_available": item.is_available,
                    "text": text
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        self.qdrant.upsert(
            collection_name=self.collections["menu_items"],
            points=points
        )
        
        logger.info(f"Indexed {len(points)} menu items for business {business_id}")
    
    def search_menu(
        self,
        query: str,
        business_id: int,
        limit: int = 5,
        dietary_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search menu items semantically.
        
        Args:
            query: Search query (e.g., "vegan options", "something sweet")
            business_id: Business to search within
            limit: Maximum results
            dietary_filter: Filter by dietary restrictions
            
        Returns:
            List of matching menu items with relevance scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query)
        
        # Build filter
        search_filter = {
            "must": [
                {"key": "business_id", "match": {"value": business_id}},
                {"key": "is_available", "match": {"value": True}}
            ]
        }
        
        # Add dietary filter if provided
        if dietary_filter:
            for dietary in dietary_filter:
                search_filter["must"].append({
                    "key": "dietary_tags",
                    "match": {"any": [dietary]}
                })
        
        # Search
        results = self.qdrant.search(
            collection_name=self.collections["menu_items"],
            query_vector=query_embedding.tolist(),
            query_filter=search_filter,
            limit=limit
        )
        
        # Format results
        items = []
        for result in results:
            item = {
                "item_id": result.payload["item_id"],
                "name": result.payload["name"],
                "description": result.payload["description"],
                "price": result.payload["price"],
                "dietary_tags": result.payload["dietary_tags"],
                "allergens": result.payload["allergens"],
                "score": result.score
            }
            items.append(item)
        
        return items
    
    def index_faqs(self, business_id: int, faqs: List[Dict[str, str]]):
        """
        Index FAQ questions and answers.
        
        Args:
            business_id: Business ID
            faqs: List of {"question": ..., "answer": ...}
        """
        points = []
        for i, faq in enumerate(faqs):
            # Combine question and answer for embedding
            text = f"Question: {faq['question']} Answer: {faq['answer']}"
            embedding = self.embedder.encode(text)
            
            point = PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    "business_id": business_id,
                    "question": faq["question"],
                    "answer": faq["answer"]
                }
            )
            points.append(point)
        
        self.qdrant.upsert(
            collection_name=self.collections["faqs"],
            points=points
        )
        
        logger.info(f"Indexed {len(points)} FAQs for business {business_id}")
    
    def search_faqs(
        self,
        query: str,
        business_id: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search FAQs for relevant answers."""
        query_embedding = self.embedder.encode(query)
        
        results = self.qdrant.search(
            collection_name=self.collections["faqs"],
            query_vector=query_embedding.tolist(),
            query_filter={
                "must": [{"key": "business_id", "match": {"value": business_id}}]
            },
            limit=limit
        )
        
        faqs = []
        for result in results:
            if result.score > 0.7:  # Relevance threshold
                faqs.append({
                    "question": result.payload["question"],
                    "answer": result.payload["answer"],
                    "score": result.score
                })
        
        return faqs
    
    def find_similar_items(
        self,
        item_id: int,
        business_id: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find items similar to a given item."""
        # Get the item's embedding
        item_result = self.qdrant.retrieve(
            collection_name=self.collections["menu_items"],
            ids=[item_id]
        )
        
        if not item_result:
            return []
        
        item_vector = item_result[0].vector
        
        # Search for similar items
        results = self.qdrant.search(
            collection_name=self.collections["menu_items"],
            query_vector=item_vector,
            query_filter={
                "must": [
                    {"key": "business_id", "match": {"value": business_id}},
                    {"key": "is_available", "match": {"value": True}}
                ],
                "must_not": [
                    {"key": "item_id", "match": {"value": item_id}}
                ]
            },
            limit=limit
        )
        
        similar_items = []
        for result in results:
            similar_items.append({
                "item_id": result.payload["item_id"],
                "name": result.payload["name"],
                "price": result.payload["price"],
                "score": result.score
            })
        
        return similar_items 

