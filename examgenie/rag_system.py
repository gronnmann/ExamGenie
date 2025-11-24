"""RAG system for context document embeddings and retrieval."""

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from rich.console import Console
from sentence_transformers import SentenceTransformer

from .llm_client import LLMClient
from .pdf_extractor import PDFExtractor

console = Console()


class RAGSystem:
    """Retrieval-Augmented Generation system using ChromaDB."""
    
    def __init__(self, persist_directory: Path, llm_client: LLMClient):
        """
        Initialize the RAG system.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            llm_client: LLM client for embeddings
        """
        self.persist_directory = persist_directory
        self.llm_client = llm_client
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-large")
        
        # Determine if using external or local embeddings
        self.use_external_embeddings = not self.embedding_model_name.startswith("sentence-transformers/")
        
        if self.use_external_embeddings:
            console.print(f"[cyan]→[/cyan] Using external embeddings: {self.embedding_model_name}")
            # ChromaDB with custom embedding function
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
            self.local_model = None
        else:
            console.print(f"[cyan]→[/cyan] Using local embeddings: {self.embedding_model_name}")
            # Extract model name after "sentence-transformers/"
            model_name = self.embedding_model_name.replace("sentence-transformers/", "")
            self.local_model = SentenceTransformer(model_name)
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        
        self.collection_name = "context_documents"
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
    
    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using configured model."""
        if self.use_external_embeddings:
            return self.llm_client.get_embedding(text)
        else:
            return self.local_model.encode(text).tolist()
    
    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        chunks: list[str] = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def index_documents(self, context_dir: Path, rebuild: bool = False) -> None:
        """
        Index context documents from a directory.
        
        Args:
            context_dir: Directory containing context PDFs
            rebuild: If True, rebuild the index from scratch
        """
        if not context_dir.exists():
            console.print(f"[yellow]⚠[/yellow] Context directory not found: {context_dir}")
            return
        
        # Get or create collection
        try:
            if rebuild:
                try:
                    self.client.delete_collection(self.collection_name)
                    console.print("[cyan]→[/cyan] Deleted existing collection")
                except Exception:
                    pass
            
            # Create collection with custom embedding function if using external
            if self.use_external_embeddings:
                collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            else:
                collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            
            # Check if already indexed
            if collection.count() > 0 and not rebuild:
                console.print(f"[green]✓[/green] Using existing index with {collection.count()} chunks")
                return
            
            # Extract PDFs
            extractor = PDFExtractor()
            documents = extractor.extract_from_directory(context_dir)
            
            if not documents:
                return
            
            console.print("[cyan]→[/cyan] Chunking and embedding documents...")
            
            # Process each document
            all_chunks: list[str] = []
            all_metadatas: list[dict[str, str]] = []
            all_ids: list[str] = []
            
            for doc in documents:
                chunks = self._chunk_text(doc.text)
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "filename": doc.filename,
                        "chunk_index": str(i),
                    })
                    all_ids.append(f"{doc.filename}_{i}")
            
            # Generate embeddings and add to collection
            console.print(f"[cyan]→[/cyan] Generating embeddings for {len(all_chunks)} chunks...")
            
            # Process in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                batch_metadatas = all_metadatas[i:i + batch_size]
                batch_ids = all_ids[i:i + batch_size]
                
                # Generate embeddings
                if self.use_external_embeddings:
                    # For external, we need to embed one at a time (API limitation)
                    batch_embeddings = [self._get_embedding(chunk) for chunk in batch_chunks]
                else:
                    # Local model can batch
                    batch_embeddings = self.local_model.encode(batch_chunks).tolist()
                
                collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_chunks,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                )
                
                console.print(f"[cyan]→[/cyan] Indexed {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")
            
            console.print(f"[green]✓[/green] Indexed {len(all_chunks)} chunks from {len(documents)} documents")
        
        except Exception as e:
            console.print(f"[red]✗[/red] Error indexing documents: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> list[str]:
        """
        Search for relevant context chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant text chunks
        """
        try:
            collection = self.client.get_collection(self.collection_name)
            
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            
            # Extract documents
            if results["documents"] and len(results["documents"]) > 0:
                return results["documents"][0]
            return []
        
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Search error: {e}")
            return []
