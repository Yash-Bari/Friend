import os
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv
from chromadb.config import Settings

# Disable ChromaDB telemetry
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_TESTING'] = 'True'

# Load environment variables
load_dotenv()

# Initialize Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

genai.configure(api_key=GOOGLE_API_KEY)

class MemorySystem:
    def __init__(self):
        """Initialize the memory system with ChromaDB collections."""
        import os
        import time
        from pathlib import Path
        
        self.embedding_model = 'models/embedding-001'  # Gemini's embedding model
        db_path = os.path.join(os.getcwd(), 'chroma_db')
        
        # Try to initialize with retries
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Clear the database directory if it exists and we're not on the first attempt
                if attempt > 0 and os.path.exists(db_path):
                    print(f"Attempt {attempt + 1}: Clearing ChromaDB directory...")
                    try:
                        import shutil
                        shutil.rmtree(db_path)
                        # Small delay to ensure the OS releases file handles
                        time.sleep(1)
                    except Exception as e:
                        print(f"Warning: Could not clear ChromaDB directory: {e}")
                
                # Initialize ChromaDB client with the new API
                print(f"Attempt {attempt + 1}: Initializing ChromaDB...")
                self.chroma_client = chromadb.PersistentClient(
                    path=db_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Try to access the collection
                self.collection = self._get_or_create_collection()
                print("ChromaDB initialized successfully.")
                return
                
            except Exception as e:
                print(f"Error initializing ChromaDB (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:  # Last attempt
                    raise RuntimeError(f"Failed to initialize ChromaDB after {max_retries} attempts: {e}")
                
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts using Gemini with fallback."""
        try:
            # Use the Gemini embedding model
            result = genai.embed_content(
                model=self.embedding_model,
                content=texts,
                task_type="retrieval_document"
            )
            return result['embedding'] if isinstance(result['embedding'][0], list) else [result['embedding']]
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            # Return simple hash-based vectors as fallback
            return self._get_fallback_embeddings(texts)
    
    def _get_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate simple fallback embeddings based on text hashing."""
        import hashlib
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to a 768-dimensional vector (repeated pattern)
            vector = []
            for i in range(768):
                vector.append(float(hash_bytes[i % len(hash_bytes)]) / 255.0 - 0.5)
            embeddings.append(vector)
        return embeddings
    
    def _get_or_create_collection(self):
        """Get or create the ChromaDB collection for memory storage."""
        try:
            return self.chroma_client.get_collection("memories")
        except ValueError:
            return self.chroma_client.create_collection("memories")
    
    def save_memory(self, user_id: str, text: str, tags: List[str], metadata: Optional[Dict] = None) -> str:
        """
        Save a memory with the given text and tags.
        
        Args:
            user_id: Unique identifier for the user
            text: The content to remember
            tags: List of tags for categorization
            metadata: Additional metadata to store
            
        Returns:
            str: The ID of the saved memory
        """
        if metadata is None:
            metadata = {}
            
        memory_id = str(uuid.uuid4())
        metadata.update({
            "user_id": user_id,
            "tags": ",".join(tags),
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Get embeddings for the text
        embeddings = self._get_embeddings([text])
        
        self.collection.add(
            documents=[text],
            embeddings=embeddings,
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def query_memory(self, user_id: str, query: str, k: int = 5, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Query memories relevant to the given query text.
        
        Args:
            user_id: User to query memories for
            query: The query text
            k: Number of results to return
            tags: Optional list of tags to filter by
            
        Returns:
            List of relevant memories with metadata
        """
        try:
            # Get query embedding first
            query_embedding = self._get_embeddings([query])[0]
                
            # Get all results first with a higher limit to account for filtering
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max(10, k * 3),  # Get more results to account for filtering
                where={"user_id": user_id} if user_id else None
            )
            
            # If no results found, return empty list
            if not results or results.get('ids') is None or len(results['ids'][0]) == 0:
                return []
            
            # Filter results by tags if specified
            if tags and len(tags) > 0:
                filtered_results = {
                    'ids': [[]],
                    'distances': [[]],
                    'metadatas': [[]],
                    'documents': [[]],
                    'embeddings': [[]] if results.get('embeddings') else None
                }
                
                for i in range(len(results['ids'][0])):
                    if i >= len(results['metadatas'][0]):
                        continue
                        
                    metadata = results['metadatas'][0][i]
                    if metadata and 'tags' in metadata:
                        memory_tags = metadata['tags'].split(',')
                        if any(tag in memory_tags for tag in tags):
                            filtered_results['ids'][0].append(results['ids'][0][i])
                            filtered_results['distances'][0].append(results['distances'][0][i])
                            filtered_results['metadatas'][0].append(metadata)
                            filtered_results['documents'][0].append(results['documents'][0][i])
                            if filtered_results['embeddings'] is not None and i < len(results['embeddings'][0]):
                                filtered_results['embeddings'][0].append(results['embeddings'][0][i])
                                
                            # If we have enough results, break early
                            if len(filtered_results['ids'][0]) >= k:
                                break
                
                # If we have any filtered results, use them
                if len(filtered_results['ids'][0]) > 0:
                    results = filtered_results
                    
                # Trim to requested k results
                for key in ['ids', 'distances', 'metadatas', 'documents']:
                    if results.get(key) and len(results[key]) > 0:
                        results[key] = [results[key][0][:k]]
                if results.get('embeddings') and len(results['embeddings']) > 0:
                    results['embeddings'] = [results['embeddings'][0][:k]]
            
            # If no results after filtering, return empty list
            if not results.get('ids') or len(results['ids'][0]) == 0:
                return []
            
            # Build memories list
            memories = []
            for i in range(min(len(results['ids'][0]), k)):
                # Skip if we don't have all the required data
                if (i >= len(results['metadatas'][0]) or 
                    i >= len(results['documents'][0]) or 
                    i >= len(results['distances'][0])):
                    continue
                    
                memory = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                }
                memories.append(memory)
                
            return memories
            
        except Exception as e:
            print(f"Error querying memory: {str(e)}")
            return []

# Create a singleton instance
memory_system = MemorySystem()

def save_memory(user_id: str, text: str, tags: List[str], metadata: Optional[Dict] = None) -> str:
    """Save a memory (public interface)."""
    return memory_system.save_memory(user_id, text, tags, metadata)

def query_memory(user_id: str, query: str, k: int = 5, tags: List[str] = None) -> List[Dict[str, Any]]:
    """Query memories (public interface)."""
    return memory_system.query_memory(user_id, query, k, tags)
