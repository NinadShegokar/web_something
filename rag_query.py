from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM

INDEX_DIR = "rag_index"

SYSTEM_PROMPT = """
You are a security analysis assistant.

Answer ONLY using the provided scan findings.
If the information is not present, say: "Not detected in the scans."
Explain clearly for a non-technical audience.
Do not exaggerate risks.
"""

def ask(question: str):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

    docs = db.similarity_search(question, k=2)
    context = "\n\n".join(d.page_content[:1500] for d in docs)

    llm = OllamaLLM(
        model="phi3.5:3.8b",
        temperature=0,
        num_predict=120
    )

    prompt = f"""{SYSTEM_PROMPT}

Scan Findings:
{context}

Question:
{question}

Answer:
"""

    return llm.invoke(prompt)

if __name__ == "__main__":
    q = input("Ask a question: ")
    print("\n" + ask(q))
