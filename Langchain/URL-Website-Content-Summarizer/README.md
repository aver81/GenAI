# URL Content Summarizer (Video + Website) — README

### App URL - https://kaeiq3vdpcetzm6kcftbax.streamlit.app/

## Overview

This project is a Streamlit application that summarizes content from YouTube videos and webpages using Groq LLMs (Llama-3, Mixtral, Gemma, etc.).
It accepts a URL, extracts the text (via loaders), sends it to a summarization LLM, and produces a clean, readable summary with a title.

The app works for:

1. YouTube videos → Extracts transcript automatically
2. Webpages → Extracts page text using HTML loader
3. Any public URL that is accessible and supported by the document loaders

The user can select any model available in the Groq model endpoint (excluding guard models).

## Features
1. Automatic Model Discovery

    - The app fetches Groq's available models at startup:
    - Queries the Groq API
    - Filters out guard / safety models
    - Populates the Streamlit dropdown dynamically
    - Stores models in st.session_state for stability during reruns

2. YouTube and Webpage Parsing

    - Supports intelligent content extraction:
    - If the URL contains "youtube", uses YoutubeLoader
    - Otherwise, falls back to WebBaseLoader
    - Ensures correct text extraction for summarization
    - Handles SSL / certificate issues via optional verify_ssl=False

3. Smart Summarization with Custom Prompt

    - Uses LangChain’s PromptTemplate:
    - Provides structured instructions to LLM
    - Generates a bold, large-font title
    - Produces a concise but clear summary
    - Works for transcripts or raw webpage text

4. Clean and Interactive Streamlit UI

    - User-friendly interface:
    - Sidebar for API key input
    - Dropdown for model selection
    - Input field for URL
    - Validation for required fields and URL format
    - Success and error alerts for UX clarity

5. Modular, LCEL-style Pipeline


    - PromptTemplate

    - ChatGroq (Groq LLM wrapper)

    - StrOutputParser

    - Operator-based LCEL chain pipeline → prompt | llm | StrOutputParser()

    - Keeps the summarization logic clean, declarative, and reusable.

## Architecture & Flow

```
           ┌──────────────────────┐
           │   User Enters URL    │
           └──────────┬───────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  Detect YouTube vs Website  │
        └──────────┬──────────────────┘
                   │
      ┌────────────┴────────────┐
      ▼                           ▼
YouTubeLoader             WebBaseLoader
      │                           │
      ▼                           ▼
Extract Transcript         Extract Page Text
      │                           │
      └───────────────┬──────────┘
                      ▼
               Combine Content
                      ▼
             Apply PromptTemplate
                      ▼
                  ChatGroq LLM
                      ▼
              StrOutputParser()
                      ▼
              Display Summary
```

## Dependencies
    - Streamlit

    - LangChain (core + community)

    - langchain-groq

    - langchain-text-splitters

    - validators

    - python-dotenv

    - requests

# Key Components
1. Model Fetching
```
if "models" not in st.session_state:
    url = "https://api.groq.com/openai/v1/models"
    response = requests.get(url, headers=headers).json()
    st.session_state.models = [
        m["id"] for m in response["data"] if 'guard' not in m["id"]
    ]
```

2. Summarization Prompt
```
template = """
You are an expert summarizer...
Content to summarize = {content}
"""
prompt = PromptTemplate(input_variables=['content'], template=template)
```

3. Loader Selection
```
if "youtube" in urlinput:
    loader = YoutubeLoader.from_youtube_url(...)
else:
    loader = WebBaseLoader(web_path=urlinput, verify_ssl=False)
```

4. LCEL Summarization Chain

```
chain = prompt | llm | StrOutputParser()
response = chain.invoke({'content': data})
```

## Intended Use Cases

1. Summarizing long YouTube lectures

2. Generating quick website summaries

3. Extracting insights from articles

4. Creating concise recaps for research

5. Accelerating content review and note-taking

6. Building RAG or LLM apps around web sources