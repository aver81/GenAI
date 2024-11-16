import numpy as np

class VectorStore:
    def __init__(self):
        self.vector_data = {} #dictionary to store vectors
        self.vector_index= {} #dictionary to indexing structure of vectors

    def add_vector(self,vector_id,vector):
        '''
        Add a vector to the vector store 
        Args:
        vector_id (str or int): unique identifier for the vector
        vector (numpy array): vector to be stored
        '''
        self.vector_data[vector_id] = vector
        self.update_index(vector_id,vector)

    def get_vector(self,vector_id):
        '''
        Get a vector from the vector store
        Args:
        vector_id (str or int): unique identifier for the vector
        Returns (numpy array): vector if found, else None
        '''
        return self.vector_data.get(vector_id)

    def update_index(self,vector_id,vector):
        '''
        Update the index structure for the vector
        Args:
        vector_id (str or int): unique identifier for the vector
        vector (numpy array): vector data to be stored
        '''
        for existing_id,existing_vector in self.vector_data.items():
            similarity = np.dot(vector,existing_vector)/(np.linalg.norm(vector)*np.linalg.norm(existing_vector))
            if existing_id not in self.vector_index:
                self.vector_index[existing_id]={}
            self.vector_index[existing_id][vector_id] =similarity

    def find_similar_vectors(self,query_vector,num_results=5):
        '''
        Find similar vectors to the query vector
        Args:
        query_vector - the query vector
        num_results - number of similar vectors to return

        Returns: list of tuples (vector_id,similarity score) 
        '''
        results=[]
        for vector_id,vector in self.vector_data.items():
            similarity = np.dot(query_vector,vector)/(np.linalg.norm(query_vector)*np.linalg.norm(vector))
            results.append((vector_id,similarity))
        
        #sort the list in descending order of similarity
        results.sort(key=lambda x:x[1],reverse=True)
        return results[:num_results]
