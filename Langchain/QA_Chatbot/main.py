# %%
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage,SystemMessage,trim_messages,AIMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# %%
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')
os.environ['LANGSMITH_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT')
groqkey = os.getenv("GROQ_API_KEY")

# %% [markdown]
# Step 1
# Creating the prompt

# %%
prompt = ChatPromptTemplate.from_messages(
        [
            (SystemMessage(content="You are an expert assistant. Answer all questions" \
            "to the best of your knowledge.")),
            ("human","Question: {input}"),

        ]
)

# %%
def get_response(question,apikey,llm,temperature):
    llm = ChatOpenAI(model=llm,api_key=apikey,temperature=temperature)
    chain = prompt | llm | StrOutputParser()
    response =chain.invoke([{"input":question}])
    return response

# %%
st.title('Enhanced Q&A Chatbot using Langchain')
model = st.selectbox("Select which OpenAI suits you best",("gpt-5",'gpt-5-mini-2025-08-07','gpt-4o-mini'),
             index=None,placeholder="Select LLM")
temp = st.slider("Enter temperature value",min_value=0.0,max_value=1.0,
                 label_visibility="visible")
apikey = st.text_input("Enter OPENAI API KEY",type='password')
input = st.text_input("""What's your question""")
if input:
    st.text(get_response(input,apikey,model,temp))
else:
    st.text("Please provide your query")



