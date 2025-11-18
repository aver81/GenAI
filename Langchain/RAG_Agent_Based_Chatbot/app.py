from langchain_community.document_loaders import ArxivLoader
from langchain_community.tools import ArxivQueryRun,WikipediaQueryRun,DuckDuckGoSearchRun
from langchain_community.utilities import ArxivAPIWrapper,WikipediaAPIWrapper,DuckDuckGoSearchAPIWrapper
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader,WebBaseLoader
from langchain.agents import AgentState,create_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_chroma import Chroma
from langchain_classic.agents import initialize_agent,AgentType
from dotenv import load_dotenv
import streamlit as st
import os


load_dotenv()

LANGSMITH_API_KEY = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGSMITH_TRACING'] = "false"
os.environ['LANGCHAIN_TRACING_V2'] = "false"
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
os.environ['LANGSMITH_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT')

st.title("AI Research & Knowledge Agent")
st.write("RAG Based LCEL+Langchain Agent that queries Wikipedia, Arxiv and the Web for answering any of your queries")

#Defining the 3 tools to be used by the Agent
wikiwrapper = WikipediaAPIWrapper(top_k_results=2,doc_content_chars_max=250)
wikiquery = WikipediaQueryRun(api_wrapper=wikiwrapper)
wikiquery.description = (
    "Use this tool to answer GENERAL KNOWLEDGE questions. "
    "For anything about facts, people, places, objects, or definitions, use this tool."
)
arxivwrapper = ArxivAPIWrapper(top_k_results=5,doc_content_chars_max=250)
arxivquery = ArxivQueryRun(api_wrapper=arxivwrapper)
arxivquery.description = (
    "Use this to search scientific research papers on arXiv.org."
)
search = DuckDuckGoSearchRun(name="Search") # For web search

#Getting input for Groq API key
with st.sidebar:
    groqapi_input = st.text_input("Enter GROQ API key", type="password")



# INITIALIZING SESSION STATE HISTORY
if "messages" not in st.session_state:
    st.session_state['messages'] = [

        {
            "role":"assistant","content":"Hi I am a chatbot"
        }
    ]

# DISPLAY ALL PREVIOUS CHAT HISTORY
for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

#TAKE USER PROMPT INPUT, ADD IT TO CHAT HISTORY AND DISPLAY IT AGAIN
prompt=st.chat_input("What is machine learning")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt}) #Adding the user's query to chat history
    st.chat_message("user").write(prompt) #Displaying the user query again

    llm = ChatGroq(api_key=groqapi_input,model='llama-3.3-70b-versatile') #Setting up the LLM model
    tools = [arxivquery,wikiquery,search] #Defining the tools list
    agent = initialize_agent(tools,llm,agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True) # Defining the LLM configuration

    with st.chat_message("assistant"): #Starting the assistant/LLM message response
        st_cb = StreamlitCallbackHandler(st.container(),expand_new_thoughts=True) #intercepts the agent tool calls, and shows its thinking; shows tool actions too that the LLM chooses to execute
        response = agent.run(
            prompt,
            callbacks=[st_cb] #Agent called and starts executing based on the prompt; Also shows the callbacks it makes to the tools
        )
        st.session_state.messages.append({"role":"assistant","content":response}) #Stores the Agent's response in history
        st.write(response) #Display the LLM's response





