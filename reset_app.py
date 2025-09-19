#!/usr/bin/env python3
"""
Reset script to clear corrupted data and restart fresh.
This will clear ChromaDB and can optionally clear MongoDB data.
"""

import os
import shutil
import time
from pathlib import Path

def clear_chromadb():
    """Clear ChromaDB data."""
    chroma_path = Path("./chroma_db")
    if chroma_path.exists():
        print("Clearing ChromaDB data...")
        try:
            shutil.rmtree(chroma_path)
            print("✓ ChromaDB data cleared successfully")
        except Exception as e:
            print(f"✗ Error clearing ChromaDB: {e}")
    else:
        print("ChromaDB directory not found, nothing to clear")

def clear_mongodb():
    """Clear MongoDB data (optional)."""
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        load_dotenv()
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ai_friend')
        
        client = MongoClient(mongo_uri)
        db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'ai_friend'
        db = client[db_name]
        
        # List collections to clear
        collections = ['user_profiles', 'daily_plans', 'chat_messages']
        
        for collection_name in collections:
            if collection_name in db.list_collection_names():
                result = db[collection_name].delete_many({})
                print(f"✓ Cleared {result.deleted_count} documents from {collection_name}")
            else:
                print(f"Collection {collection_name} not found")
                
        client.close()
        print("✓ MongoDB data cleared successfully")
        
    except Exception as e:
        print(f"✗ Error clearing MongoDB: {e}")

def main():
    print("🔄 Lumi AI Friend - Reset Application")
    print("=" * 40)
    
    # Always clear ChromaDB
    clear_chromadb()
    
    # Ask user about MongoDB
    while True:
        choice = input("\nDo you want to clear MongoDB data too? (y/N): ").strip().lower()
        if choice in ['', 'n', 'no']:
            print("Keeping MongoDB data intact")
            break
        elif choice in ['y', 'yes']:
            clear_mongodb()
            break
        else:
            print("Please enter 'y' for yes or 'n' for no")
    
    print("\n✅ Reset complete! You can now restart the application.")
    print("\nTo restart:")
    print("python run.py")

if __name__ == "__main__":
    main()
