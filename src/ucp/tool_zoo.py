"""
Tool Zoo - Vector Index for Tool Schema Retrieval.

The Tool Zoo is the "memory" of UCP. It stores normalized tool schemas
in a vector database and enables semantic search for relevant tools
based on conversation context.

Implements the LlamaIndex pattern from the design docs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import chromadb
import structlog
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ucp.config import ToolZooConfig
from ucp.models import ToolSchema

logger = structlog.get_logger(__name__)


class ToolZoo:
    """
    Vector database for tool schema storage and retrieval.

    Uses ChromaDB for persistence and sentence-transformers for embeddings.
    """

    def __init__(self, config: ToolZooConfig) -> None:
        self.config = config
        self._embedding_model: SentenceTransformer | None = None
        self._client: chromadb.PersistentClient | None = None
        self._collection: chromadb.Collection | None = None
        self._tools_by_name: dict[str, ToolSchema] = {}
        self._initialized = False

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            logger.info("loading_embedding_model", model=self.config.embedding_model)
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
        return self._embedding_model

    def initialize(self) -> None:
        """Initialize the ChromaDB client and collection."""
        if self._initialized:
            return

        # Ensure directory exists
        persist_dir = Path(self.config.persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Create ChromaDB client with persistence
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create the tools collection
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"description": "UCP Tool Schema Index"},
        )

        # Load existing tools into cache
        self._load_existing_tools()

        self._initialized = True
        logger.info(
            "tool_zoo_initialized",
            persist_dir=str(persist_dir),
            collection=self.config.collection_name,
            existing_tools=self._collection.count(),
        )

    def _load_existing_tools(self) -> None:
        """Load all tools from the collection into the memory cache."""
        results = self._collection.get(include=["metadatas"])
        if results["metadatas"]:
            for metadata in results["metadatas"]:
                if metadata and "full_schema" in metadata:
                    try:
                        schema_dict = json.loads(metadata["full_schema"])
                        tool = ToolSchema(**schema_dict)
                        self._tools_by_name[tool.name] = tool
                    except Exception as e:
                        logger.error("failed_to_load_tool", error=str(e), metadata=metadata)

    def _generate_tool_id(self, tool: ToolSchema) -> str:
        """Generate a stable ID for a tool."""
        # Use hash of name + server for stability
        content = f"{tool.server_name}:{tool.name}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _embed_text(self, text: str) -> list[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def add_tools(self, tools: list[ToolSchema]) -> int:
        """
        Add or update tools in the index.

        Returns the number of tools added.
        """
        if not self._initialized:
            self.initialize()

        if not tools:
            return 0

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for tool in tools:
            tool_id = self._generate_tool_id(tool)
            description = tool.full_description

            ids.append(tool_id)
            documents.append(description)
            embeddings.append(self._embed_text(description))
            metadatas.append({
                "name": tool.name,
                "display_name": tool.display_name,
                "server_name": tool.server_name,
                "domain": tool.domain or "",
                "tags": ",".join(tool.tags),
                "full_schema": tool.model_dump_json(),
            })

            # Store in memory cache
            self._tools_by_name[tool.name] = tool

        # Upsert to ChromaDB
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("tools_indexed", count=len(tools))
        return len(tools)

    def remove_tools(self, tool_names: list[str]) -> int:
        """Remove tools from the index."""
        if not self._initialized:
            return 0

        ids_to_remove = []
        for name in tool_names:
            if name in self._tools_by_name:
                tool = self._tools_by_name[name]
                ids_to_remove.append(self._generate_tool_id(tool))
                del self._tools_by_name[name]

        if ids_to_remove:
            self._collection.delete(ids=ids_to_remove)

        return len(ids_to_remove)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filter_domain: str | None = None,
        filter_tags: list[str] | None = None,
        min_score: float | None = None,
    ) -> list[tuple[ToolSchema, float]]:
        """
        Search for relevant tools based on a query.

        Args:
            query: The search query (e.g., user message or context)
            top_k: Number of results to return
            filter_domain: Only return tools from this domain
            filter_tags: Only return tools with these tags
            min_score: Minimum similarity score (0-1)

        Returns:
            List of (ToolSchema, score) tuples, sorted by relevance
        """
        if not self._initialized:
            self.initialize()

        top_k = top_k or self.config.top_k
        min_score = min_score or self.config.similarity_threshold

        # Build filter
        where_filter = None
        if filter_domain or filter_tags:
            conditions = []
            if filter_domain:
                conditions.append({"domain": {"$eq": filter_domain}})
            if filter_tags:
                # ChromaDB doesn't support array contains, so we use string contains
                for tag in filter_tags:
                    conditions.append({"tags": {"$contains": tag}})
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        # Query the collection
        query_embedding = self._embed_text(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # Get more, then filter by score
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert results to ToolSchema with scores
        output: list[tuple[ToolSchema, float]] = []

        if results["ids"] and results["ids"][0]:
            for i, tool_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                # Cosine distance to similarity: similarity = 1 - distance/2
                similarity = 1 - (distance / 2)

                if similarity < min_score:
                    continue

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                tool_name = metadata.get("name", "")

                # Get full tool schema from cache
                if tool_name in self._tools_by_name:
                    output.append((self._tools_by_name[tool_name], similarity))

        # Sort by score descending and limit
        output.sort(key=lambda x: x[1], reverse=True)
        return output[:top_k]

    def get_tool(self, name: str) -> ToolSchema | None:
        """Get a specific tool by name."""
        return self._tools_by_name.get(name)

    def get_all_tools(self) -> list[ToolSchema]:
        """Get all indexed tools."""
        return list(self._tools_by_name.values())

    def get_tools_by_server(self, server_name: str) -> list[ToolSchema]:
        """Get all tools from a specific server."""
        return [t for t in self._tools_by_name.values() if t.server_name == server_name]

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the tool zoo."""
        tools = list(self._tools_by_name.values())
        servers = set(t.server_name for t in tools)
        domains = set(t.domain for t in tools if t.domain)

        return {
            "total_tools": len(tools),
            "servers": list(servers),
            "domains": list(domains),
            "collection_count": self._collection.count() if self._collection else 0,
        }

    def clear(self) -> None:
        """Clear all tools from the index."""
        if self._collection:
            # Delete all items
            all_ids = self._collection.get()["ids"]
            if all_ids:
                self._collection.delete(ids=all_ids)
        self._tools_by_name.clear()
        logger.info("tool_zoo_cleared")

    def close(self) -> None:
        """
        Release any underlying resources held by ChromaDB.

        On Windows, Chroma can hold file locks (e.g., sqlite-vec segment files)
        that prevent deleting temporary persistence directories during tests.
        """
        if not self._client:
            return

        try:
            system = getattr(self._client, "_system", None)
            if system and hasattr(system, "stop"):
                try:
                    system.stop()
                except Exception as e:
                    # Chroma's stop() is not always idempotent; if the underlying
                    # system was already stopped elsewhere, we still want to proceed
                    # with best-effort cleanup.
                    logger.warning("tool_zoo_close_failed", error=str(e))
        finally:
            self._collection = None
            self._client = None
            self._initialized = False


class HybridToolZoo(ToolZoo):
    """
    Extended Tool Zoo with keyword search fallback.

    Combines semantic search with BM25-style keyword matching
    for more robust retrieval.
    """

    def __init__(self, config: ToolZooConfig) -> None:
        super().__init__(config)
        self._keyword_index: dict[str, set[str]] = {}  # word -> tool_names

    def initialize(self) -> None:
        """Initialize and build keyword index from loaded tools."""
        super().initialize()
        # Build keyword index from loaded tools
        for tool in self._tools_by_name.values():
            self._index_keywords(tool)

    def _index_keywords(self, tool: ToolSchema) -> None:
        """Index keywords for a single tool."""
        words = self._tokenize(tool.full_description)
        for word in words:
            if word not in self._keyword_index:
                self._keyword_index[word] = set()
            self._keyword_index[word].add(tool.name)

    def add_tools(self, tools: list[ToolSchema]) -> int:
        """Add tools and build keyword index."""
        count = super().add_tools(tools)

        # Build keyword index
        for tool in tools:
            self._index_keywords(tool)

        return count

    def _tokenize(self, text: str) -> set[str]:
        """Simple tokenization for keyword matching."""
        import re
        # Lowercase, split on non-alphanumeric
        words = re.split(r'\W+', text.lower())
        # Filter short words and common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'for', 'on'}
        return {w for w in words if len(w) > 2 and w not in stopwords}

    def keyword_search(self, query: str, top_k: int = 10) -> list[tuple[ToolSchema, float]]:
        """Perform keyword-based search."""
        query_words = self._tokenize(query)

        # Count matches per tool
        tool_scores: dict[str, int] = {}
        for word in query_words:
            if word in self._keyword_index:
                for tool_name in self._keyword_index[word]:
                    tool_scores[tool_name] = tool_scores.get(tool_name, 0) + 1

        # Convert to scores (normalize by query length)
        results = []
        for tool_name, matches in tool_scores.items():
            score = matches / len(query_words) if query_words else 0
            if tool_name in self._tools_by_name:
                results.append((self._tools_by_name[tool_name], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query: str,
        top_k: int | None = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[tuple[ToolSchema, float]]:
        """
        Combined semantic + keyword search.

        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
        """
        top_k = top_k or self.config.top_k

        # Get both result sets
        semantic_results = self.search(query, top_k=top_k * 2, min_score=0.0)
        keyword_results = self.keyword_search(query, top_k=top_k * 2)

        # Combine scores
        combined: dict[str, float] = {}
        tool_cache: dict[str, ToolSchema] = {}

        for tool, score in semantic_results:
            combined[tool.name] = semantic_weight * score
            tool_cache[tool.name] = tool

        for tool, score in keyword_results:
            existing = combined.get(tool.name, 0)
            combined[tool.name] = existing + keyword_weight * score
            tool_cache[tool.name] = tool

        # Sort and return
        sorted_tools = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [(tool_cache[name], score) for name, score in sorted_tools[:top_k]]
