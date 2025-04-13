from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil
import tempfile
import faiss
import boto3
import pickle
import numpy as np
import hashlib
import nest_asyncio
nest_asyncio.apply()
from uuid import uuid4

from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import FlatReader
from llama_cloud_services import LlamaParse
from sentence_transformers import SentenceTransformer

app = FastAPI(title="EchoVector Store API")
from dotenv import load_dotenv
load_dotenv()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
S3_BUCKET = "echomind"  # Update this
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
s3 = boto3.client("s3")

# Helper: Generate a document hash-based ID
def generate_doc_id_from_file(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Helper: Check if file exists in S3
def s3_key_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False

# Upload helpers
def upload_to_s3(file_path, s3_key):
    s3.upload_file(file_path, S3_BUCKET, s3_key)
    return f"s3://{S3_BUCKET}/{s3_key}"

def save_pickle_and_upload(obj, filename, s3_key):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)
    return upload_to_s3(filename, s3_key)

@app.post("/create_vectorstore/")
async def create_vectorstore(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        # Compute doc hash
        doc_id = generate_doc_id_from_file(temp_path)
        base_s3_path = f"users/{user_id}/{doc_id}/"
        s3_index_key = f"{base_s3_path}index.faiss"
        s3_texts_key = f"{base_s3_path}texts.pkl"
        s3_meta_key = f"{base_s3_path}metadata.pkl"
        s3_doc_key = f"{base_s3_path}{file.filename}"

        # Check if vector store already exists
        if all(
            s3_key_exists(S3_BUCKET, key)
            for key in [s3_index_key, s3_texts_key, s3_meta_key]
        ):
            return {
                "message": "🟢 Vector store already exists. Skipping creation.",
                "doc_id": doc_id,
                "s3": {
                    "document": f"s3://{S3_BUCKET}/{s3_doc_key}",
                    "index": f"s3://{S3_BUCKET}/{s3_index_key}",
                    "texts": f"s3://{S3_BUCKET}/{s3_texts_key}",
                    "metadata": f"s3://{S3_BUCKET}/{s3_meta_key}",
                }
            }

        # Upload original file to S3
        s3_doc_url = upload_to_s3(temp_path, s3_doc_key)

        # File extractor
        llama_pdf_parser = LlamaParse(result_type="markdown", chunking_strategy="page")
        file_extractor = {
            ".pdf": llama_pdf_parser,
            ".txt": FlatReader(),
            ".docx": llama_pdf_parser,
        }

        reader = SimpleDirectoryReader(
            input_files=[temp_path],
            file_extractor=file_extractor
        )
        documents = await reader.aload_data()

        if len(documents) > 2:
            splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            nodes = splitter.get_nodes_from_documents(documents)
            final_chunks = [
                Document(text=node.get_content(), metadata=node.metadata)
                for node in nodes
            ]
        else:
            final_chunks = documents

        texts = [doc.text for doc in final_chunks]
        metadatas = [doc.metadata for doc in final_chunks]

        embeddings = embed_model.encode(texts, show_progress_bar=False)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings))

        # Save vector store components
        index_file = f"{doc_id}_index.faiss"
        text_file = f"{doc_id}_texts.pkl"
        meta_file = f"{doc_id}_meta.pkl"

        faiss.write_index(index, index_file)
        s3_index_url = upload_to_s3(index_file, s3_index_key)
        s3_text_url = save_pickle_and_upload(texts, text_file, s3_texts_key)
        s3_meta_url = save_pickle_and_upload(metadatas, meta_file, s3_meta_key)

        os.remove(temp_path)

        return {
            "message": "✅ Vector store created successfully.",
            "doc_id": doc_id,
            "s3": {
                "document": s3_doc_url,
                "index": s3_index_url,
                "texts": s3_text_url,
                "metadata": s3_meta_url
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()  # 👈 This will show the full error trace
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/query_vectorstore/")
async def query_vectorstore(
    user_id: str = Form(...),
    doc_id: str = Form(...),
    query: str = Form(...),
    top_k: int = Form(3)
):
    try:
        base_s3_path = f"users/{user_id}/{doc_id}/"
        index_key = f"{base_s3_path}index.faiss"
        texts_key = f"{base_s3_path}texts.pkl"
        metadata_key = f"{base_s3_path}metadata.pkl"

        # Temp file paths
        index_path = f"/tmp/{doc_id}_index.faiss"
        texts_path = f"/tmp/{doc_id}_texts.pkl"
        meta_path = f"/tmp/{doc_id}_meta.pkl"

        # Download from S3
        s3.download_file(S3_BUCKET, index_key, index_path)
        s3.download_file(S3_BUCKET, texts_key, texts_path)
        s3.download_file(S3_BUCKET, metadata_key, meta_path)

        # Load components
        index = faiss.read_index(index_path)
        with open(texts_path, "rb") as f:
            texts = pickle.load(f)
        with open(meta_path, "rb") as f:
            metadatas = pickle.load(f)

        # Embed query
        query_vec = embed_model.encode([query])
        D, I = index.search(np.array(query_vec), k=top_k)

        results = []
        for idx in I[0]:
            results.append({
                "chunk_text": texts[idx],
                "page": metadatas[idx].get("page_label", "Unknown")
            })

        return {
            "query": query,
            "results": results
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})