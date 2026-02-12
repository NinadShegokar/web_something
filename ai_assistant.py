from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
import re

INDEX_DIR = "rag_index"

# --------------------------------------------------
# Session state
# --------------------------------------------------
IS_FIRST_TURN = True


# --------------------------------------------------
# Base system prompt
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a security analysis assistant.

Answer ONLY using the provided scan findings.
If the information is not present, say: "Not detected in the scans."
Do not speculate or introduce hypothetical scenarios.
"""

# --------------------------------------------------
# Instruction policies
# --------------------------------------------------
INSTRUCTION_TEMPLATES = {
    "elaborate": "Elaborate with clear reasoning and structured explanation.",
    "simplify": "Explain in simpler terms for a non-technical audience.",
    "restrict": "Focus strictly on the user's request and retrieved scan context. Be concise.",
    "extract": "Provide a short, list-based factual answer. No extra commentary."
}

# --------------------------------------------------
# Intent detection (heuristic)
# --------------------------------------------------
def detect_intent(question: str) -> str:
    q = question.lower()

    if any(k in q for k in ["explain", "why", "how"]):
        return "elaborate"

    if any(k in q for k in ["dont get", "don't get", "confused", "dont understand"]):
        return "simplify"

    if any(k in q for k in ["list", "what ports", "which ports", "what services"]):
        return "extract"

    return "restrict"


# --------------------------------------------------
# Reward function (demo math)
# R = α·C − β·H − γ·V
# --------------------------------------------------
def compute_reward(answer: str, context: str):
    alpha = 1.0   # context adherence
    beta = 1.0    # hallucination penalty
    gamma = 0.5   # verbosity penalty

    # Context adherence
    context_hits = sum(
        1 for line in context.splitlines()
        if line.strip() and line[:20] in answer
    )
    C = min(context_hits / 3, 1.0)

    # Hallucination detection (intentionally simple)
    hallucination_markers = [
        "could potentially", "might indicate", "possibly",
        "advanced civilizations", "extraterrestrial"
    ]
    H = 1.0 if any(m in answer.lower() for m in hallucination_markers) else 0.0

    # Verbosity penalty
    word_count = len(answer.split())
    V = min(word_count / 150, 1.0)

    reward = alpha * C - beta * H - gamma * V
    reward = round(max(-1.0, min(1.0, reward)), 2)

    return reward, {"C": round(C, 2), "H": H, "V": round(V, 2)}


# --------------------------------------------------
# Main ask function
# --------------------------------------------------
def ask(question: str):
    global IS_FIRST_TURN

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

    # Retrieve context
    docs = db.similarity_search(question, k=2)
    context = "\n\n".join(d.page_content[:1500] for d in docs)

    # Baseline behavior for first query
    if IS_FIRST_TURN:
        intent = "baseline"
        instructions = ""
    else:
        intent = detect_intent(question)
        instructions = INSTRUCTION_TEMPLATES[intent]

    llm = OllamaLLM(
        model="phi3.5:3.8b",
        temperature=0,
        num_predict=150
    )

    prompt = f"""
{SYSTEM_PROMPT}

[INSTRUCTIONS]
{instructions}

[SCAN FINDINGS]
{context}

[QUESTION]
{question}

[ANSWER]
"""

    answer = llm.invoke(prompt).strip()

    # Reward handling
    if IS_FIRST_TURN:
        reward = None
        components = None
        IS_FIRST_TURN = False
    else:
        reward, components = compute_reward(answer, context)

    return {
        "answer": answer,
        "intent": intent,
        "instructions": instructions,
        "reward": reward,
        "reward_components": components
    }


# --------------------------------------------------
# CLI loop (for now)
# --------------------------------------------------
if __name__ == "__main__":
    while True:
        q = input("Ask a question (or 'exit'): ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        result = ask(q)

        print("\nAnswer:")
        print(result["answer"])

        print("\n--- RL SIGNALS ---")
        print(f"Detected intent   : {result['intent']}")
        print(f"Applied policy    : {result['instructions'] or 'Baseline (no policy)'}")

        if result["reward"] is None:
            print("Reward score      : N/A (baseline)")
            print("Reward breakdown  : N/A")
        else:
            print(f"Reward score      : {result['reward']}")
            print(f"Reward breakdown  : {result['reward_components']}")

        print()
