
# Multi-Tool AI Chatbot using LangChain, Groq, and Streamlit

App Link - https://khybwbfwmzetyh2ds9tcyf.streamlit.app/


This project is an interactive AI chatbot built with LangChain, Groq LLMs, and Streamlit, designed to intelligently route queries to different tools such as:

- Wikipedia → for general knowledge
- ArXiv → for scientific papers
- DuckDuckGo Search → for real-time web search

It uses a ReAct Agent (classic LangChain agent) capable of reasoning, choosing tools, and responding conversationally.
The UI is built entirely in Streamlit with full conversation history and real-time tool-execution display.

## Features
1. Multi-Tool Agent Capabilities
  The assistant dynamically chooses the correct tool based on the user query:

    - For general Definitions, facts, people and places, it uses the ```WikipediaAPIWrapper``` and ```WikiQueryRun``` tools.
    - For research papers, it uses ```ArXivAPIWrapper``` and ```ArXivQueryRun```.
   - Web search, current events	 use **DuckDuckGo Search**.
    - For the rest, its	Llama-3 via Groq

2. Interactive Chat Interface (Streamlit)

  - Chat bubbles for user + assistant
  - Persistent chat history using session_state
  - Real-time streaming of agent “thoughts” and tool calls
  - Clean assistant output in a chat-style layout

3. Powered by Groq

The chatbot uses Llama-3.3-70B-Versatile (or any other Groq model you choose), providing:

  1. Extremely fast inference
  2. Accurate reasoning
  3. Low latency

The Groq API key is entered securely via a Streamlit sidebar.

# Project Structure
```
|-- app.py                # Main Streamlit application
|-- README.md             # Project documentation
|-- .env                  # Environment variables (API keys)
|-- requirements.txt      # Python dependencies
```


# How It Works

The chatbot uses a LangChain Classic ReAct Agent:
```
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)
```

ReAct agents:

1. Think step-by-step
2. Decide which tool to use
3. Execute the tool
4. Observe results
5. Build a final answer
6. StreamlitCallbackHandler streams:
    - Thought: ...
    - Action: WikipediaQueryRun
    - Observation: ...

# Tools Used
1. Wikipedia Tool

  - Used for general knowledge, definitions, and factual queries.

2. ArXiv Tool

  - Used for academic research, ML papers, scientific topics.

3. DuckDuckGo Search Tool

  - Used for real-time and broad web queries.

4. Streamlit Components

1. st.chat_input() → Chat textbox
2. st.chat_message() → Chat bubble rendering
3. st.session_state → Saves conversation history
4. StreamlitCallbackHandler → Streams tool calls live
5. Sidebar input for API key

# Future Improvements

1. RAG retrievers
2. Custom vectorstores
3. Additional APIs as tools
4. Memory modules
5. Personality prompts

Typing animation effects

Just extend the agent or tool list.
