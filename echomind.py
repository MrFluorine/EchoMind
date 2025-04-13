from dotenv import load_dotenv
import os
import streamlit as st
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from google import genai
from google.genai import types
import requests
import json
from io import BytesIO

# Load environment variables
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Prompt for user ID
if "user_authenticated" not in st.session_state:
    user_id_input = st.text_input("Enter your user ID")
    if user_id_input:
        st.session_state.user_id = user_id_input
        st.session_state.user_authenticated = True
        st.rerun()
    st.stop()

user_id = st.session_state.user_id

uploaded_file = st.file_uploader("Upload your document", type=["pdf", "docx", "txt"])

if uploaded_file:
    if st.session_state.get("last_uploaded_file") != uploaded_file.name:
        st.info("Uploading and processing document...")
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        data = {"user_id": user_id}
        res = requests.post("http://localhost:8000/create_vectorstore/", files=files, data=data)
        if res.status_code == 200:
            doc_info = res.json()
            st.session_state["doc_id"] = doc_info["doc_id"]
            st.session_state["messages"] = []
            st.session_state["last_uploaded_file"] = uploaded_file.name
            st.success("Document processed and vector store created.")
            st.rerun()
        else:
            st.error("Failed to upload and process document.")
            st.stop()

doc_id = st.session_state.get("doc_id")

def process_query(query, user_id, doc_id):
    url = "http://localhost:8000/query_vectorstore/"
    payload = {
        "user_id": user_id,
        "doc_id": doc_id,
        "query": query,
        "top_k": 3
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        result = response.json()
        chunks = result.get("results", [])
        return "\n\n".join([f"**Page {r['page']}**:\n{r['chunk_text']}" for r in chunks])
    else:
        return "Error querying the vector store."

def classify_query(query):
    prompt = f"""You are a classification assistant that decides whether a user's query needs to be answered using uploaded documents or not.

    Classify the following query into one of two categories:

    A. The answer is likely found in a user-uploaded document (like a resume, contract, report, or technical PDF). These are specific, document-bound questions such as names, dates, definitions specific to the file, or information only present in the user's context.

    B. The answer is general or conversational, such as asking for opinions, public knowledge, definitions, summaries, or explanations not tied to any specific uploaded document.

    Return only "A" or "B".

    Query: \"{query}\" """

    result = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return result.text.strip()

def generate_chat_response(history):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction="""You are a personal AI assistant! You will be given a chat history with you and a user.
            You have to respond to the last question user asked."""
        ),
        contents=history
    )
    return response.text.strip()

# Streamlit UI
st.title("EchoMind - Give your documents a voice")

# Display chat messages
for message in st.session_state.messages:
    role = message.get("role")
    content = message.get("content") if "content" in message else message.get("parts", [""])[0]
    with st.chat_message(role):
        st.markdown(content)

# Chat input
if prompt := st.chat_input("What would you like to know about the document?"):
    classification = classify_query(prompt)
    st.session_state.history = [str(m) for m in st.session_state.messages]

    if classification == "A":
        # Use retrieval
        result = process_query(prompt, user_id, doc_id)
        combined = f'{prompt}\ncontext from retrival is : {result}'
        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        st.session_state.history.append(str({"role": "user", "parts": [combined]}))

    else:
        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        st.session_state.history.append(str({"role": "user", "parts": [prompt]}))

    # Generate response from Gemini
    response = generate_chat_response(st.session_state.history)
    st.session_state.messages.append({"role": "model", "parts": [response]})
    st.session_state.history.append(str({"role": "model", "parts": [response]}))

    with st.chat_message("assistant"):
        st.markdown(response)