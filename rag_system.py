import os
# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
import ollama
from config import Config
import streamlit as st

class RAGSystem:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            base_url=Config.OLLAMA_BASE_URL,
            model=Config.EMBEDDING_MODEL
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        try:
            self.vectorstore = Chroma(
                collection_name=Config.COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=Config.VECTOR_DB_PATH
            )
        except Exception as e:
            st.error(f"Error initializing vector store: {str(e)}")
    
    def process_and_store_transcript(self, transcript, meeting_id):
        """Process transcript and store in vector database"""
        try:
            # Split transcript into chunks
            with st.spinner("Splitting transcript into chunks..."):
                chunks = self.text_splitter.split_text(transcript)
            
            if not chunks:
                return False, "No chunks created from transcript"
            
            # Create metadata for each chunk
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadatas.append({
                    "meeting_id": meeting_id,
                    "chunk_index": i,
                    "chunk_type": "transcript",
                    "total_chunks": len(chunks)
                })
            
            # Store in vector database
            with st.spinner(f"Storing {len(chunks)} chunks in vector database..."):
                self.vectorstore.add_texts(
                    texts=chunks,
                    metadatas=metadatas,
                    ids=[f"{meeting_id}_chunk_{i}" for i in range(len(chunks))]
                )
                
                # Persist the database
                self.vectorstore.persist()
            
            return True, f"Successfully stored {len(chunks)} chunks"
            
        except Exception as e:
            return False, f"Error processing transcript: {str(e)}"
    
    def retrieve_relevant_chunks(self, query, k=5):
        """Retrieve relevant chunks for a query"""
        try:
            if not self.vectorstore:
                return []
            
            # Perform similarity search
            relevant_docs = self.vectorstore.similarity_search(
                query=query,
                k=k
            )
            
            return [doc.page_content for doc in relevant_docs]
            
        except Exception as e:
            st.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    def get_meeting_context(self, meeting_id):
        """Get all chunks for a specific meeting"""
        try:
            if not self.vectorstore:
                return ""
            
            # Get all chunks for the meeting
            results = self.vectorstore.get(
                where={"meeting_id": meeting_id}
            )
            
            if results and results['documents']:
                # Sort chunks by index and combine
                chunks_with_metadata = list(zip(results['documents'], results['metadatas']))
                sorted_chunks = sorted(chunks_with_metadata, key=lambda x: x[1]['chunk_index'])
                
                return " ".join([chunk[0] for chunk in sorted_chunks])
            
            return ""
            
        except Exception as e:
            st.error(f"Error getting meeting context: {str(e)}")
            return ""
