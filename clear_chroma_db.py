import os
import shutil

def clear_chroma_db():
    """
    Remove the ChromaDB data directory to resolve any instance conflicts.
    """
    db_path = os.path.join(os.getcwd(), 'chroma_db')
    
    if os.path.exists(db_path):
        print(f"Removing ChromaDB directory: {db_path}")
        try:
            shutil.rmtree(db_path)
            print("Successfully removed ChromaDB directory.")
            return True
        except Exception as e:
            print(f"Error removing ChromaDB directory: {e}")
            return False
    else:
        print("ChromaDB directory not found. No action needed.")
        return True

if __name__ == "__main__":
    clear_chroma_db()
