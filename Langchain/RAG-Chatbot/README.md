# PDF Question Answering Assistant using Langchain and LCEL

## A Streamlit + LangChain + Groq RAG App for Querying Any PDF

This project allows users to upload any PDF file and ask questions based on its content. Behind the scenes, the app performs:

1. PDF text extraction
2. Intelligent text chunking
3. Embedding generation
4. Vector search with Chroma
5. Context-aware answering using a Groq LLM

All done dynamically in-memory, without persistent storage.

# Features
1. Upload Any PDF

Users can upload a document (reports, articles, PPTs exported as PDF, notes, etc.).

2. RAG Pipeline (Retrieval-Augmented Generation)

The app:

1. Extracts text using PyPDFLoader
2. Splits into overlapping chunks using RecursiveCharacterTextSplitter
3. Creates embeddings with OpenAI's text-embedding-3-small
4. Stores them in an in-memory Chroma vector DB
5. Retrieves relevant context based on the user's query
6. Generates an accurate answer using Groq's llama-3.1-8b-instant model

# Modern LCEL (LangChain Expression Language)

Uses the new LCEL pipeline:

```Retriever → Prompt → Groq LLM → Output Parser ```


📁 Project Structure
repo/
│
├── main.py                  → Main Streamlit application
├── requirements.txt         → Python dependencies
└── .streamlit/ (optional)   → Streamlit configuration

# Installation & Setup

1. Clone this repository
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo

2. Install dependencies
pip install -r requirements.txt

3. Set environment variables

Create a .env file in the project root:

OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key


(Only OpenAI and Groq keys are required for this app.)

4. Run the app
streamlit run main.py

# How the RAG Pipeline Works
1. Load PDF

PyPDFLoader extracts the raw text content.

2. Split document

RecursiveCharacterTextSplitter breaks the document into 1000-character chunks with 100-character overlap.

3. Generate embeddings

Using:

```OpenAIEmbeddings(model="text-embedding-3-small")```. This provides fast and high-quality vector embeddings.

4. Create vector DB

Chroma stores embeddings in-memory:

vectordb = Chroma.from_documents(content, embeddings)

5. Retrieve relevant chunks

The retriever fetches the most relevant text for a query.

6. Feed into LLM

The app uses Groq’s lightning-fast Llama 3.1 8B model for answer generation.

# Code Summary

Here’s the main LCEL chain:

chain = (
    {"context": vectordbretriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


And execution:

answer = chain.invoke(query)

# Example Usage

Upload a PDF (e.g., a research paper)

Enter a question like:

What does the paper say about attention mechanisms?


The chatbot returns a context-grounded answer extracted from your PDF.

# Technologies Used
Component	Library
UI	Streamlit
PDF Loading	LangChain PyPDFLoader
Chunking	RecursiveCharacterTextSplitter
Embeddings	OpenAI embeddings
Vector DB	Chroma
LLM	Groq (Llama 3.1 8B Instant)
Orchestration	LangChain LCEL

# Notes

Chroma DB is not persisted, making this ideal for dynamic uploads.

PDFs must contain selectable text (OCR not included yet).

PPT files are supported only if exported to text-based PDF.

# Future Enhancements

1. Add OCR fallback for image-only PDFs
2. Add chat history
3. Multi-PDF indexing
4. Allow LLM model switching in UI
5. Source citation and chunk viewer
