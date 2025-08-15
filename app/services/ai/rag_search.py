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

# Add this to handle the specific Qdrant exception
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)


class RAGSearchService:
    """
    Semantic search using vector embeddings.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.collections = {
            "menu_items": "menu_items_v1",
            "faqs": "faqs_v1",
            "policies": "policies_v1"
        }
        
        self._initialize_collections()
    
    # === FIX IS HERE ===
    def _initialize_collections(self):
        """Create vector collections only if they don't exist."""
        vector_size = 384
        
        # Get all existing collections from Qdrant
        try:
            existing_collections = [col.name for col in self.qdrant.get_collections().collections]
        except Exception as e:
            logger.error(f"Could not connect to Qdrant to get collections: {e}")
            # If we can't connect, we can't proceed.
            # This will prevent the app from crashing on startup if Qdrant is down.
            return

        for collection_name in self.collections.values():
            # Check if the collection is already in the list of existing ones
            if collection_name not in existing_collections:
                try:
                    # If it doesn't exist, create it
                    self.qdrant.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {collection_name}")
                except UnexpectedResponse as e:
                    # Handle the rare case where another process creates it at the same time
                    if "already exists" in str(e):
                        logger.warning(f"Collection {collection_name} already exists (race condition).")
                    else:
                        raise e # Re-raise other unexpected errors
            else:
                logger.debug(f"Collection {collection_name} already exists. Skipping creation.")

    def index_menu_items(self, business_id: int):
        """
        Index all menu items for a business.
        """
        items = self.db.query(MenuItem).filter(MenuItem.business_id == business_id).all()
        if not items:
            return
        
        points = []
        for item in items:
            text = f"{item.name}. {item.description or ''}. Dietary: {', '.join(item.dietary_tags)}. Allergens: {', '.join(item.allergens)}. Price: ${item.base_price}"
            embedding = self.embedder.encode(text)
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
        
        self.qdrant.upsert(
            collection_name=self.collections["menu_items"],
            points=points,
            wait=True
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
        """
        query_embedding = self.embedder.encode(query)
        
        search_filter = {"must": [
            {"key": "business_id", "match": {"value": business_id}},
            {"key": "is_available", "match": {"value": True}}
        ]}
        
        if dietary_filter:
            for dietary in dietary_filter:
                search_filter["must"].append({"key": "dietary_tags", "match": {"any": [dietary]}})
        
        results = self.qdrant.search(
            collection_name=self.collections["menu_items"],
            query_vector=query_embedding.tolist(),
            query_filter=search_filter,
            limit=limit
        )
        
        items = []
        for result in results:
            items.append({
                "item_id": result.payload["item_id"],
                "name": result.payload["name"],
                "description": result.payload["description"],
                "price": result.payload["price"],
                "score": result.score
            })
        return items
    
    # ... (rest of the file is unchanged) ...
    def index_faqs(self, business_id: int, faqs: List[Dict[str, str]]):
        points = []
        for i, faq in enumerate(faqs):
            text = f"Question: {faq['question']} Answer: {faq['answer']}"
            embedding = self.embedder.encode(text)
            point = PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={"business_id": business_id, "question": faq["question"], "answer": faq["answer"]}
            )
            points.append(point)
        self.qdrant.upsert(collection_name=self.collections["faqs"], points=points, wait=True)
        logger.info(f"Indexed {len(points)} FAQs for business {business_id}")

    def search_faqs(self, query: str, business_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.encode(query)
        results = self.qdrant.search(
            collection_name=self.collections["faqs"],
            query_vector=query_embedding.tolist(),
            query_filter={"must": [{"key": "business_id", "match": {"value": business_id}}]},
            limit=limit
        )
        faqs = []
        for result in results:
            if result.score > 0.7:
                faqs.append({"question": result.payload["question"], "answer": result.payload["answer"], "score": result.score})
        return faqs

    def find_similar_items(self, item_id: int, business_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        item_result = self.qdrant.retrieve(collection_name=self.collections["menu_items"], ids=[item_id])
        if not item_result:
            return []
        item_vector = item_result[0].vector
        results = self.qdrant.search(
            collection_name=self.collections["menu_items"],
            query_vector=item_vector,
            query_filter={
                "must": [
                    {"key": "business_id", "match": {"value": business_id}},
                    {"key": "is_available", "match": {"value": True}}
                ],
                "must_not": [{"key": "item_id", "match": {"value": item_id}}]
            },
            limit=limit
        )
        similar_items = []
        for result in results:
            similar_items.append({"item_id": result.payload["item_id"], "name": result.payload["name"], "price": result.payload["price"], "score": result.score})
        return similar_items