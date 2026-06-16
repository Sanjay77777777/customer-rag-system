# Customer RAG

A simple Retrieval-Augmented Generation (RAG) application that uses ChromaDB, SentenceTransformers, and Ollama Qwen2.5-Coder to answer questions about customer data.

## Project Structure

```
customer-rag/
├── data/
│   └── data.txt          # Sample customer records
├── rag/
│   ├── build_index.py    # Build vector index from customer data
│   ├── ask.py            # Query the RAG system
│   └── config.py         # Configuration settings
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Ollama is running locally with the Qwen2.5-Coder model.

3. Build the index:
   ```bash
   python rag/build_index.py
   ```

4. Ask questions:
   ```bash
   python rag/ask.py "Which customers are in the Platinum segment?"
   ```
