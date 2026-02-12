from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

DOCS_DIR = Path("./parsed_docs")
INDEX_DIR = Path("./rag_index")

def main():
    if not DOCS_DIR.exists():
        print("parsed_docs directory not found.")
        return

    documents = []
    metadatas = []

    for file in DOCS_DIR.glob("*.txt"):
        text = file.read_text().strip()
        if not text:
            continue
        documents.append(text)
        metadatas.append({"source": file.name})

    if not documents:
        print("No documents to index.")
        return

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    db = FAISS.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas
    )

    db.save_local(str(INDEX_DIR))
    print(f"RAG index built with {len(documents)} documents.")

if __name__ == "__main__":
    main()
