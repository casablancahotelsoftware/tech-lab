import argparse
import os
import json
import uuid
from vector_db_manager import VectorDBManager
from tqdm import tqdm

def load_documents(json_path, collection_name, recreate):
    db_manager = VectorDBManager(collection_name=collection_name)
    if recreate:
        db_manager.initialize_collection()
    else:
        print(f"Using existing collection: {collection_name}")

    with open(json_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    for doc in tqdm(documents, desc="Uploading documents"):
        text = doc.get("page_content", "")
        metadata = doc.get("metadata", {})
        doc_id = str(uuid.uuid4())
        db_manager.add_document_with_text(doc_id, text, metadata=metadata)

    print("All documents loaded into Qdrant.")

def main():
    parser = argparse.ArgumentParser(description="Load documents into Qdrant vector store.")
    parser.add_argument(
        "--json", 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), "..", "clean_architecture_documents.json"),
        help="Path to the JSON file with documents."
    )
    parser.add_argument(
        "--collection", 
        type=str, 
        default="clean_architecture_docs",
        help="Qdrant collection name."
    )
    parser.add_argument(
        "--recreate", 
        action="store_true",
        help="Recreate the collection (delete if exists)."
    )
    args = parser.parse_args()
    load_documents(args.json, args.collection, args.recreate)

if __name__ == "__main__":
    main()