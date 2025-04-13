# 🧠 EchoMind

Your **personal AI assistant** that chats like a friend and thinks like a database.  
Upload your documents, ask questions, and let EchoMind handle the rest — whether it needs retrieval or just a good conversation.  
Built with **FastAPI**, **Streamlit**, **Gemini**, and **FAISS**.  

---

## 🚀 Features

- 📄 Upload any `.pdf`, `.txt`, or `.docx`
- 🔍 Smart query classification: retrieval or general chat?
- 🧠 Gemini-powered conversation (remembers your chat!)
- 🗃️ FAISS + Sentence Transformers for fast semantic search
- ☁️ S3 storage for document and vector persistence
- 🔁 Upload new docs anytime — chat resets & vector store refreshes
- 🧰 Built with FastAPI + Streamlit = clean backend + beautiful frontend

---

## 🖼️ Demo Preview

![echomind_ui](https://github.com/MrFluorine/echomind/assets/demo-preview.png)

---

## 🛠 Tech Stack

| Layer         | Tooling                            |
|---------------|-------------------------------------|
| Frontend      | `Streamlit`                        |
| API Backend   | `FastAPI`                          |
| Chat Engine   | `Gemini Pro (Google GenAI)`        |
| Embeddings    | `sentence-transformers/all-MiniLM` |
| Vector DB     | `FAISS`                            |
| File Storage  | `Amazon S3`                        |

---

## 📦 Installation

### 🔧 Prerequisites

- Python 3.10+
- AWS S3 bucket + credentials
- Gemini API Key

### 🔍 Clone & Install

```bash
git clone https://github.com/MrFluorine/echomind.git
cd echomind
pip install -r requirements.txt
```

### 🔐 Setup `.env`

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=your_region
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🧪 Running the App

### 1. Start the **FastAPI Backend**

```bash
uvicorn vector_store_api:app --reload --port 8000
```

### 2. Start the **Streamlit Frontend**

```bash
streamlit run echomind.py
```

---

## 💬 How It Works

1. **Enter your user ID**
2. **Upload a document**
3. Ask anything like:
   - “What’s the architect’s name?”
   - “What is CNN?”
   - “Summarize page 3”
4. It auto-classifies:
   - Needs retrieval → fetch from vector DB
   - General → Gemini chat
5. **All responses are context-aware and stored in chat history**

---

## 📁 Folder Structure

```bash
.
├── echomind.py                # Streamlit UI
├── vector_store_api.py        # FastAPI backend for upload/query
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
```

---

## ⚡️ Powered By

- 🤖 [Gemini](https://ai.google.dev)
- 🧠 [LlamaIndex](https://llamaindex.ai/)
- 🌍 [FastAPI](https://fastapi.tiangolo.com/)
- 🧩 [Streamlit](https://streamlit.io)
- 🚀 [FAISS](https://github.com/facebookresearch/faiss)

---

## ✨ Coming Soon

- ✅ RAG + Gemini response fusion
- 🧑‍💻 Multi-user chat history storage
- 📊 Document analytics (topics, summaries)
- 🔒 Authentication with JWT or OAuth

---

## 🤝 Contribute

PRs welcome! Open an issue or drop a suggestion. This is your EchoMind too.  
Built for personal growth, learning, and fun 🤍

---

## 📫 Contact

Built with 💡 by [@MrFluorine](https://github.com/MrFluorine)

---

> “The best assistants don’t just answer — they understand.”  
> — EchoMind
