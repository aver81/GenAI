from vector_store import VectorStore
import numpy as np
import streamlit as st
st.title("Vector Store & Cosine Similarity")
st.write("This is a simple application to demonstrate the working of a vector store and cosine similarity.")

#create a class to handle the application logic
vector_store=VectorStore()
st.title("Enter the sentences below that will provide the foundation for the bag of words in vector store")
sentences=st.text_area("Enter Sentences:").split("\n")


#TOKENIZATION AND VOCABULARY BUILDING
#initialize a vocabulary
vocab=set()
#vocab basically is like a bag of all possible unique words from the above sentences
for sentence in sentences:
    tokens=sentence.lower().split()
    vocab.update(tokens)

#assign indices to all unique words
word_to_index={word:i for i,word in enumerate(vocab)}
# st.write(word_to_index)
# st.write(word_to_index['i'])
sentence_vectors={}

#here we count the occurrence of each word in each sentence
#and update its value respectively
#this is done to create a vector representation of each sentence
for sentence in sentences:
    tokens=sentence.lower().split()
    vector=np.zeros(len(vocab))
    for token in tokens:
        vector[word_to_index[token]]+=1
    sentence_vectors[sentence]=vector

#add vectors to the vector store now 
for sentence,vector in sentence_vectors.items():
    vector_store.add_vector(sentence,vector)

#now we can find similar sentences to a query sentence
st.title("Write the sentence that you want to compare against the above sentences")
query_sentence=st.text_input("Enter Query Sentence:")
st.write("Note: The query sentence must not contain any words that are not present in the sentences entered above.")
query_vector=np.zeros(len(vocab))
query_tokens=query_sentence.lower().split()
for token in query_tokens:
    query_vector[word_to_index[token]]+=1

#find similar sentences
similar_sentences=vector_store.find_similar_vectors(query_vector,num_results=5)
if st.button('Submit'): 

    st.write("Query Sentence:",query_sentence)
    st.write("Similar Sentences:")
    for sentence,similarity in similar_sentences:
        #print(f"{sentence}:Similarity = {similarity:.4f}")
        st.write(f"{sentence}:Similarity = {similarity:.4f}")