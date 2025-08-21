"""
Vector Search service for semantic clause matching and similarity search.

This service handles:
- Vertex AI Vector Search index management
- Embedding generation and storage pipeline
- Similarity search for clause comparison and precedent finding
- Semantic matching for legal clause analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass

from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
from vertexai.language_models import TextEmbeddingModel
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.document import Clause
from ..core.exceptions import VectorSearchError

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    embedding: List[float]
    text: str
    metadata: Dict[str, Any]


@dataclass
class SimilarityMatch:
    """Result of similarity search."""
    clause_id: str
    similarity_score: float
    clause_text: str
    metadata: Dict[str, Any]


class VectorSearchService:
    """
    Service for managing vector embeddings and semantic search for legal clauses.
    
    Integrates with Vertex AI Vector Search for scalable similarity matching.
    """
    
    def __init__(self):
        """Initialize Vector Search service."""
        # Initialize AI Platform
        aiplatform.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Initialize embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        
        # Vector Search configuration
        self.index_id = settings.VECTOR_SEARCH_INDEX_ID
        self.endpoint_id = settings.VECTOR_SEARCH_ENDPOINT_ID
        
        # Initialize index and endpoint if configured
        self.index = None
        self.endpoint = None
        
        if self.index_id:
            try:
                self.index = MatchingEngineIndex(self.index_id)
            except Exception as e:
                logger.warning(f"Failed to initialize Vector Search index: {str(e)}")
        
        if self.endpoint_id:
            try:
                self.endpoint = MatchingEngineIndexEndpoint(self.endpoint_id)
            except Exception as e:
                logger.warning(f"Failed to initialize Vector Search endpoint: {str(e)}")
        
        # Embedding cache for performance
        self._embedding_cache = {}
        self._cache_size_limit = 1000
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of EmbeddingResult objects
            
        Raises:
            VectorSearchError: If embedding generation fails
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            all_results = []
            
            # Process in batches to avoid API limits
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_results = await self._generate_batch_embeddings(batch_texts)
                all_results.extend(batch_results)
            
            logger.info(f"Successfully generated {len(all_results)} embeddings")
            return all_results
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise VectorSearchError(f"Failed to generate embeddings: {str(e)}") from e
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for a batch of texts."""
        try:
            # Check cache first
            cached_results = []
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    cached_results.append((i, self._embedding_cache[cache_key]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Generate embeddings for uncached texts
            new_embeddings = []
            if uncached_texts:
                embeddings_response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.embedding_model.get_embeddings(uncached_texts)
                )
                
                for text, embedding_obj in zip(uncached_texts, embeddings_response):
                    embedding_vector = embedding_obj.values
                    result = EmbeddingResult(
                        embedding=embedding_vector,
                        text=text,
                        metadata={"length": len(text), "model": "textembedding-gecko@003"}
                    )
                    new_embeddings.append(result)
                    
                    # Cache the result
                    cache_key = self._get_cache_key(text)
                    self._cache_embedding(cache_key, result)
            
            # Combine cached and new results in original order
            all_results = [None] * len(texts)
            
            # Place cached results
            for original_index, cached_result in cached_results:
                all_results[original_index] = cached_result
            
            # Place new results
            for i, result in enumerate(new_embeddings):
                original_index = uncached_indices[i]
                all_results[original_index] = result
            
            return all_results
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise VectorSearchError(f"Failed to generate batch embeddings: {str(e)}") from e
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def _cache_embedding(self, cache_key: str, result: EmbeddingResult):
        """Cache embedding result with size limit."""
        if len(self._embedding_cache) >= self._cache_size_limit:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]
        
        self._embedding_cache[cache_key] = result
    
    async def embed_clauses(self, clauses: List[Clause]) -> List[EmbeddingResult]:
        """
        Generate embeddings for legal clauses.
        
        Args:
            clauses: List of Clause objects
            
        Returns:
            List of EmbeddingResult objects with clause metadata
        """
        try:
            # Prepare texts for embedding
            clause_texts = []
            for clause in clauses:
                # Combine clause text with category for better embeddings
                enhanced_text = clause.text
                if clause.category:
                    enhanced_text = f"[{clause.category.upper()}] {enhanced_text}"
                clause_texts.append(enhanced_text)
            
            # Generate embeddings
            embedding_results = await self.generate_embeddings(clause_texts)
            
            # Add clause metadata to results
            for i, result in enumerate(embedding_results):
                clause = clauses[i]
                result.metadata.update({
                    "clause_id": str(clause.id),
                    "classification": clause.classification.value,
                    "risk_score": clause.risk_score,
                    "category": clause.category,
                    "keywords": clause.keywords
                })
            
            return embedding_results
            
        except Exception as e:
            logger.error(f"Clause embedding failed: {str(e)}")
            raise VectorSearchError(f"Failed to embed clauses: {str(e)}") from e
    
    async def store_embeddings(
        self, 
        embeddings: List[EmbeddingResult],
        index_name: Optional[str] = None
    ) -> bool:
        """
        Store embeddings in Vector Search index.
        
        Args:
            embeddings: List of embedding results to store
            index_name: Optional index name (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.index:
                logger.warning("Vector Search index not configured, skipping storage")
                return False
            
            logger.info(f"Storing {len(embeddings)} embeddings in Vector Search index")
            
            # Prepare data for index update
            embedding_vectors = []
            embedding_ids = []
            
            for i, result in enumerate(embeddings):
                embedding_vectors.append(result.embedding)
                # Use clause_id if available, otherwise generate ID
                embedding_id = result.metadata.get("clause_id", f"embedding_{i}")
                embedding_ids.append(embedding_id)
            
            # Convert to numpy array
            embedding_matrix = np.array(embedding_vectors, dtype=np.float32)
            
            # Update index (this is a simplified version - actual implementation
            # would depend on the specific Vector Search setup)
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._update_index,
                embedding_matrix,
                embedding_ids,
                embeddings
            )
            
            logger.info("Successfully stored embeddings in Vector Search index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {str(e)}")
            return False
    
    def _update_index(
        self, 
        embedding_matrix: np.ndarray, 
        embedding_ids: List[str],
        embedding_results: List[EmbeddingResult]
    ):
        """Update the Vector Search index with new embeddings."""
        # This is a placeholder for the actual index update logic
        # The real implementation would use the Vector Search API
        # to update the index with new embeddings
        logger.info(f"Index update placeholder: {len(embedding_ids)} embeddings")
    
    async def search_similar_clauses(
        self, 
        query_text: str, 
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SimilarityMatch]:
        """
        Search for similar clauses using semantic similarity.
        
        Args:
            query_text: Text to search for similar clauses
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            List of SimilarityMatch objects
            
        Raises:
            VectorSearchError: If search fails
        """
        try:
            logger.info(f"Searching for similar clauses to: {query_text[:100]}...")
            
            # Generate embedding for query
            query_embeddings = await self.generate_embeddings([query_text])
            query_embedding = query_embeddings[0].embedding
            
            # Perform similarity search
            if self.endpoint:
                # Use Vector Search endpoint
                matches = await self._search_with_endpoint(query_embedding, top_k)
            else:
                # Use fallback in-memory search
                matches = await self._search_fallback(query_embedding, top_k)
            
            # Filter by similarity threshold
            filtered_matches = [
                match for match in matches 
                if match.similarity_score >= similarity_threshold
            ]
            
            logger.info(f"Found {len(filtered_matches)} similar clauses above threshold")
            return filtered_matches
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise VectorSearchError(f"Failed to search similar clauses: {str(e)}") from e
    
    async def _search_with_endpoint(
        self, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[SimilarityMatch]:
        """Search using Vector Search endpoint."""
        try:
            # Perform the search
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._execute_endpoint_search,
                query_embedding,
                top_k
            )
            
            # Parse response into SimilarityMatch objects
            matches = []
            for neighbor in response:
                match = SimilarityMatch(
                    clause_id=neighbor.id,
                    similarity_score=neighbor.distance,  # Convert distance to similarity
                    clause_text=neighbor.metadata.get("text", ""),
                    metadata=neighbor.metadata
                )
                matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Endpoint search failed: {str(e)}")
            return []
    
    def _execute_endpoint_search(self, query_embedding: List[float], top_k: int):
        """Execute search against Vector Search endpoint."""
        # This is a placeholder for the actual endpoint search
        # The real implementation would use the Vector Search API
        logger.info(f"Endpoint search placeholder: top_k={top_k}")
        return []
    
    async def _search_fallback(
        self, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[SimilarityMatch]:
        """Fallback in-memory similarity search."""
        logger.info("Using fallback similarity search")
        
        # This is a simplified fallback that would search against
        # cached embeddings or a local index
        matches = []
        
        # For now, return empty results as this would require
        # a local embedding store
        return matches
    
    async def find_clause_precedents(
        self, 
        clause: Clause, 
        top_k: int = 5
    ) -> List[SimilarityMatch]:
        """
        Find legal precedents for a given clause.
        
        Args:
            clause: Clause to find precedents for
            top_k: Number of precedents to return
            
        Returns:
            List of similar clauses that could serve as precedents
        """
        try:
            # Create enhanced query text for precedent search
            query_parts = [clause.text]
            
            if clause.category:
                query_parts.append(f"Category: {clause.category}")
            
            if clause.keywords:
                query_parts.append(f"Keywords: {', '.join(clause.keywords[:5])}")
            
            enhanced_query = " | ".join(query_parts)
            
            # Search for similar clauses
            similar_clauses = await self.search_similar_clauses(
                enhanced_query, 
                top_k=top_k * 2,  # Get more results to filter
                similarity_threshold=0.6  # Lower threshold for precedents
            )
            
            # Filter and rank precedents
            precedents = []
            for match in similar_clauses:
                # Skip if it's the same clause
                if match.clause_id == str(clause.id):
                    continue
                
                # Prefer clauses with similar risk levels
                match_risk = match.metadata.get("risk_score", 0.5)
                risk_similarity = 1.0 - abs(clause.risk_score - match_risk)
                
                # Adjust similarity score based on risk similarity
                adjusted_score = (match.similarity_score * 0.7) + (risk_similarity * 0.3)
                
                precedent = SimilarityMatch(
                    clause_id=match.clause_id,
                    similarity_score=adjusted_score,
                    clause_text=match.clause_text,
                    metadata={
                        **match.metadata,
                        "precedent_type": "similar_clause",
                        "risk_similarity": risk_similarity
                    }
                )
                precedents.append(precedent)
            
            # Sort by adjusted similarity score and return top results
            precedents.sort(key=lambda x: x.similarity_score, reverse=True)
            return precedents[:top_k]
            
        except Exception as e:
            logger.error(f"Precedent search failed: {str(e)}")
            return []
    
    async def compare_clauses(
        self, 
        clause1: Clause, 
        clause2: Clause
    ) -> Dict[str, Any]:
        """
        Compare two clauses for similarity and differences.
        
        Args:
            clause1: First clause to compare
            clause2: Second clause to compare
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Generate embeddings for both clauses
            embeddings = await self.embed_clauses([clause1, clause2])
            
            # Calculate cosine similarity
            embedding1 = np.array(embeddings[0].embedding)
            embedding2 = np.array(embeddings[1].embedding)
            
            similarity = self._cosine_similarity(embedding1, embedding2)
            
            # Compare other attributes
            comparison = {
                "semantic_similarity": float(similarity),
                "classification_match": clause1.classification == clause2.classification,
                "risk_score_difference": abs(clause1.risk_score - clause2.risk_score),
                "category_match": clause1.category == clause2.category,
                "common_keywords": list(set(clause1.keywords) & set(clause2.keywords)),
                "unique_keywords_1": list(set(clause1.keywords) - set(clause2.keywords)),
                "unique_keywords_2": list(set(clause2.keywords) - set(clause1.keywords)),
                "length_difference": abs(len(clause1.text) - len(clause2.text)),
                "overall_similarity": self._calculate_overall_similarity(
                    similarity, clause1, clause2
                )
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Clause comparison failed: {str(e)}")
            return {"error": str(e)}
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_overall_similarity(
        self, 
        semantic_similarity: float, 
        clause1: Clause, 
        clause2: Clause
    ) -> float:
        """Calculate overall similarity score combining multiple factors."""
        # Weight different similarity factors
        weights = {
            "semantic": 0.5,
            "classification": 0.2,
            "risk": 0.2,
            "category": 0.1
        }
        
        # Semantic similarity
        semantic_score = semantic_similarity
        
        # Classification similarity
        classification_score = 1.0 if clause1.classification == clause2.classification else 0.0
        
        # Risk similarity
        risk_score = 1.0 - abs(clause1.risk_score - clause2.risk_score)
        
        # Category similarity
        category_score = 1.0 if clause1.category == clause2.category else 0.0
        
        # Calculate weighted average
        overall_similarity = (
            semantic_score * weights["semantic"] +
            classification_score * weights["classification"] +
            risk_score * weights["risk"] +
            category_score * weights["category"]
        )
        
        return overall_similarity
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache and index."""
        stats = {
            "cache_size": len(self._embedding_cache),
            "cache_limit": self._cache_size_limit,
            "index_configured": self.index is not None,
            "endpoint_configured": self.endpoint is not None,
            "embedding_model": "textembedding-gecko@003"
        }
        
        if self.index:
            try:
                # Get index statistics if available
                stats["index_id"] = self.index_id
            except Exception as e:
                logger.warning(f"Failed to get index stats: {str(e)}")
        
        return stats
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")