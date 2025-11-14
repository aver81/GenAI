# %%
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from dotenv import load_dotenv
import streamlit as st
import os

# %%
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
os.environ['LANGSMITH_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT')
groqkey = os.getenv("GROQ_API_KEY")
    

st.set_page_config(page_title="PDF QA Chatbot", page_icon="📘", layout="wide")

st.markdown("""
<style>
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #5D6D7E;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>📘 PDF Question Answering Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Ask any question from your uploaded PDF</div>", unsafe_allow_html=True)

llm = ChatGroq(model='llama-3.1-8b-instant',api_key=groqkey)
prompt = ChatPromptTemplate.from_template(
    """
        You are an expert assistant. Answer all questions based on the provided context
        <context>
        Context:
        {context}
        </context>
        Question : {question}
    """
)
def rag_chain_function():
    progress = st.progress(0)
    info = st.empty()
    loader = PyPDFLoader("temp.pdf")
    info.write("PDF loaded!")
    progress.progress(25)

    info.write("Splitting PDF into chunks")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=100)
    content = splitter.split_documents(docs)
    progress.progress(50)


    info.write("Generating Embeddings and creating Vector DB")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma.from_documents(content ,embeddings)
    progress.progress(100)
    vectordbretriever = vectordb.as_retriever()
    chain = (
                    {"context":vectordbretriever,"question":RunnablePassthrough()}
                    | prompt
                    | llm
                    | StrOutputParser()

        )
    answer = chain.invoke(query)
    return answer
    

pdfdocument = st.file_uploader("Upload your PDF file",type='pdf')
if pdfdocument is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdfdocument.read())
    query = st.text_input("""Enter your query based on your PDF:""")
    if st.button("Get results"):
        answer = rag_chain_function()
        st.write(answer)
else:
    st.error("Please upload PDF file.")

