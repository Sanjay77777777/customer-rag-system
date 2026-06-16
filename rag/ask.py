import chromadb
from chromadb.config import Settings
import ollama

from rag.config import CHROMA_DB_PATH, COLLECTION_NAME


def main() -> None:
    try:
        # ------------------------------------------------------------------
        # 1. Connect to the persistent ChromaDB instance
        # ------------------------------------------------------------------
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        # ------------------------------------------------------------------
        # 2. Load the customers collection
        # ------------------------------------------------------------------
        collection = client.get_collection(COLLECTION_NAME)

        print("Customer RAG Assistant Ready")
        print("Type 'exit' to quit.")

        # ------------------------------------------------------------------
        # 3. Start the interactive question loop
        # ------------------------------------------------------------------
        while True:
            try:
                question = input("\nAsk a question (or type exit): ")

                # Exit conditions
                if question.lower() in ("exit", "quit"):
                    break

                # ------------------------------------------------------------------
                # 4. Retrieve the top 3 semantically similar customer records
                # ------------------------------------------------------------------
                results = collection.query(
                    query_texts=[question],
                    n_results=3,
                )

                # ------------------------------------------------------------------
                # 5. Assemble retrieved records into a single context block
                # ------------------------------------------------------------------
                context = "\n\n".join(results["documents"][0])

                # ------------------------------------------------------------------
                # 6. Build the instruction prompt for the LLM
                # ------------------------------------------------------------------
                prompt = f"""You are a customer database assistant.

Rules:

1. Answer ONLY using the provided customer records.
2. Do not invent customers.
3. If information is not present, say:
   "I could not find that information in the customer database."
4. If the user asks for all matching customers, list every matching customer.
5. Include customer names and relevant attributes.
6. Be concise and factual.

Context:
{context}

Question:
{question}

Answer:"""

                # ------------------------------------------------------------------
                # 7. Send the prompt to Ollama Qwen2.5-Coder and get the answer
                # ------------------------------------------------------------------
                response = ollama.chat(
                    model="qwen2.5-coder:7b",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )

                answer = response["message"]["content"]

                # ------------------------------------------------------------------
                # 8. Print the answer only
                # ------------------------------------------------------------------
                print(answer)

            except Exception as e:
                print(f"An error occurred during retrieval: {e}")

    except Exception as e:
        print(f"Failed to initialize: {e}")


if __name__ == "__main__":
    main()
