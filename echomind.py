from dotenv import load_dotenv
import os
import streamlit as st
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.embeddings import GeminiEmbedding
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

embed_model = GeminiEmbedding(model_name="models/embedding-001")

def parse_document(file_path):
    """Parse document using LlamaParse"""
    parser = LlamaParse(
        result_type="markdown",
        api_key=os.getenv("LLAMA_CLOUD_API_KEY")
    )
    file_extractor = {".pdf": parser}
    documents = SimpleDirectoryReader(
        input_files=[file_path],
        file_extractor=file_extractor
    ).load_data()
    return documents

def create_index(documents):
    """Create vector index for RAG"""
    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model
    )
    return VectorStoreIndex.from_documents(
        documents,
        service_context=service_context
    )

def process_query(query, index, documents):
    """Process user query with RAG or direct context based on document length"""
    if len(documents) <= 4:  # If document is 4 pages or less
        context = "\n".join([doc.text for doc in documents])
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        response = llm.complete(prompt)
        return response.text
    else:
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        return response.response

# Streamlit UI
st.title("EchoMind - Document Chatbot")

# File upload
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Parse document
    documents = parse_document("temp.pdf")
    
    # Create index if document is longer than 4 pages
    if len(documents) > 4:
        index = create_index(documents)
    else:
        index = None
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about the document?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            response = process_query(prompt, index, documents)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clean up temporary file
    os.remove("temp.pdf")