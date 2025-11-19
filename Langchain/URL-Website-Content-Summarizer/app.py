
from langchain_community.document_loaders import YoutubeLoader,WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.youtube import TranscriptFormat
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.messages import AIMessage,HumanMessage,SystemMessage
import os 
from dotenv import load_dotenv
import streamlit as st
import validators

load_dotenv()
groqkey = os.getenv("GROQ_API_KEY")

# splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
# splitter.split_documents(videodata)
import requests

if "models" not in st.session_state:
    url = "https://api.groq.com/openai/v1/models"
    headers = {
    "Authorization": f"Bearer {groqkey}",
    "Content-Type": "application/json"
    }
    models=[]
    response = requests.get(url, headers=headers).json()
    st.session_state.models = [m["id"] for m in response["data"] if 'guard' not in m["id"]]

template = """
    You are an expert summarizer Based on the provided info, summarize what \
    the content is talking about. Be clear about the summary.
    Provide a clear summary title in bold text and bigger font as well.
    Content to summarize = {content}
    
    """
prompt = PromptTemplate(input_variables=['content'],template=template)

st.title('URL Content Summarizer (Video/Website)')

with st.sidebar:
    groqkey = st.text_input("Groq API Key",type='password',key='groq_key')
modelinput = st.selectbox("Select LLM",st.session_state.models)
st.success(f"Model selected: {modelinput}")
urlinput = st.text_input("Enter website URL")    
if st.button("Summarize"):
    if not groqkey.strip():
        st.error("Please provide Groq API key")
    elif not urlinput.strip():
        st.error("Please enter website URL")
    elif not modelinput:
        st.error("Please select a model from the dropdown options.")
    else:
        if not validators.url(urlinput):
            st.error("Please enter valid website URL")
        else:

            with st.spinner("Analyzing.."):
                llm = ChatGroq(model=modelinput,api_key=groqkey.strip()) 
                if "youtube" in urlinput:
                    loader = YoutubeLoader.from_youtube_url(urlinput,
                                            add_video_info=False,
                                            transcript_format=TranscriptFormat.CHUNKS,
                                            chunk_size_seconds=60)
                
                else:
                    loader = WebBaseLoader(web_path=urlinput,verify_ssl=False)
                data = loader.load()
                chain = prompt | llm | StrOutputParser()
                response = chain.invoke({'content':data})
                st.success(response)