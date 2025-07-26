# manager/sub_agents/rag_retrieval/agent.py (FINAL CORRECTED VERSION)

import os
import json
import numpy as np
import pandas as pd # Needed for CSV parsing
from io import BytesIO
from google.cloud import storage
from vertexai import init
from vertexai.preview.language_models import TextEmbeddingModel
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.function_tool import FunctionTool # Import FunctionTool
from pydantic import BaseModel, Field
from numpy.linalg import norm # For cosine similarity

import logging

# Configuration (These should ideally come from environment variables or a shared config)
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id") # Fallback for local testing
LOCATION = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
BUCKET_NAME = os.environ.get("GCS_RAG_BUCKET", "studyplanandcontent")
EMBEDDINGS_NPY_PATH = os.environ.get("RAG_EMBEDDINGS_NPY_PATH", "embeddingsoutput/iesc106_vector_chunks.npy")
METADATA_CSV_PATH = os.environ.get("RAG_METADATA_CSV_PATH", "embeddingsoutput/iesc106_chunk_metadata.csv")

# Initialize Vertex AI components ONCE at module load
try:
    init(project=PROJECT_ID, location=LOCATION)
    EMBEDDING_MODEL = TextEmbeddingModel.from_pretrained("text-embedding-005")
    STORAGE_CLIENT = storage.Client(project=PROJECT_ID)
    logging.info("Vertex AI and Storage client initialized for RAG.")

    # Load chunk embeddings and metadata once on module load
    # This assumes these files are relatively small. For large datasets,
    # you'd use a vector database (e.g., AlloyDB AI, Matching Engine)
    # or stream data. For hackathon, loading once is fine.
    emb_blob = STORAGE_CLIENT.bucket(BUCKET_NAME).blob(EMBEDDINGS_NPY_PATH)
    emb_buf = BytesIO()
    emb_blob.download_to_file(emb_buf)
    emb_buf.seek(0)
    GLOBAL_CHUNK_EMBEDDINGS = np.load(emb_buf)
    logging.info(f"Loaded {GLOBAL_CHUNK_EMBEDDINGS.shape[0]} chunk embeddings.")

    meta_blob = STORAGE_CLIENT.bucket(BUCKET_NAME).blob(METADATA_CSV_PATH)
    csv_buf = BytesIO()
    meta_blob.download_to_file(csv_buf)
    csv_buf.seek(0)
    GLOBAL_CHUNK_METADATA = pd.read_csv(csv_buf)
    logging.info(f"Loaded {len(GLOBAL_CHUNK_METADATA)} chunk metadata entries.")

except Exception as e:
    logging.error(f"Failed to initialize RAG global components: {e}")
    # Re-raise to fail early if critical components can't load
    raise

# --- Function for RAG Retrieval (to be wrapped as a FunctionTool) ---
class RetrieveContextInput(BaseModel):
    query_text: str = Field(description="The text of the question to retrieve context for.")

class RetrieveContextOutput(BaseModel):
    relevant_context_text: str = Field(description="The full text of the most relevant chunk.")
    relevant_chunk_id: int = Field(description="The ID of the most relevant chunk.")
    similarity_score: float = Field(description="Cosine similarity score of the retrieved chunk.")

async def retrieve_relevant_context(query_text: str) -> RetrieveContextOutput:
    """
    Embeds the query and finds the most relevant document chunk from pre-computed embeddings.
    """
    logging.info(f"Retrieving context for query: {query_text[:50]}...")
    
    # Embed the user query
    try:
        query_embedding_response = EMBEDDING_MODEL.get_embeddings([query_text])
        query_vector = np.array(query_embedding_response[0].values)
    except Exception as e:
        logging.error(f"Error embedding query: {e}")
        return RetrieveContextOutput(
            relevant_context_text="Error: Could not embed query.",
            relevant_chunk_id=-1,
            similarity_score=0.0
        )

    # Compute cosine similarity for each chunk
    def cosine_similarity(a, b):
        return np.dot(a, b) / (norm(a) * norm(b) + 1e-8) # Add small epsilon to prevent division by zero
    
    similarities = [cosine_similarity(query_vector, vec) for vec in GLOBAL_CHUNK_EMBEDDINGS]
    
    if not similarities:
        logging.warning("No embeddings found for similarity comparison.")
        return RetrieveContextOutput(
            relevant_context_text="No relevant context found.",
            relevant_chunk_id=-1,
            similarity_score=0.0
        )

    best_idx = int(np.argmax(similarities))
    best_chunk = GLOBAL_CHUNK_METADATA.iloc[best_idx]
    best_similarity_score = similarities[best_idx]

    logging.info(f"Found best chunk: ID={best_chunk['chunk_id']}, Similarity={best_similarity_score:.4f}")

    return RetrieveContextOutput(
        relevant_context_text=best_chunk['text'],
        relevant_chunk_id=int(best_chunk['chunk_id']),
        similarity_score=float(best_similarity_score)
    )

# Wrap the retrieval function as a FunctionTool
retrieve_context_tool = FunctionTool(
    name="retrieve_context",
    description="Retrieves the most relevant text context for a given query from the indexed knowledge base.",
    parameters=RetrieveContextInput, # Input schema for the function tool
    return_schema=RetrieveContextOutput, # Output schema for the function tool
    function=retrieve_relevant_context,
)


# --- Pydantic Model for the parsed request output (from knowledge_base_pipeline's first agent) ---
class ParsedRequestOutput(BaseModel):
    extracted_question: str = Field(description="The question extracted from the request.")
    extracted_language: str = Field(description="The language extracted from the request, defaults to English.")


# --- RAG Sub-Agent 1: Request Parser (Moved from knowledge_base/agent.py for clarity, but logic is same) ---
# This agent takes the 'request' from the manager_agent and parses it.
rag_request_parser_agent = LlmAgent(
    name="RagRequestParserAgent",
    model="gemini-1.5-flash",
    description="Parses the user's question and language from the raw request for RAG processing.",
    instruction="""
    You are an intelligent assistant. The teacher's full request is: '{session.state.request}'.
    
    Your task is to:
    1.  **Extract the core 'question'** the teacher or student is asking from the request.
    2.  **Identify the desired 'language'** for the answer from the request. If no language is explicitly mentioned, assume 'English'.

    Output only in JSON, with keys 'extracted_question' and 'extracted_language'.
    """,
    output_schema=ParsedRequestOutput,
    output_key="parsed_rag_request_details", # Store parsed details here
)


# --- RAG Sub-Agent 2: Context Retrieval & Verification ---
# This agent will orchestrate the actual tool call to retrieve context.
context_retriever_agent = LlmAgent(
    name="ContextRetrieverAgent",
    model="gemini-1.5-flash", # Use Flash for calling the tool and simple logic
    description="Uses a specialized tool to retrieve relevant context for a question from the knowledge base.",
    instruction="""
    You are a context retrieval specialist.
    The question you need to find context for is: '{parsed_rag_request_details.extracted_question}'
    
    Your task is to call the 'retrieve_context' tool with the extracted question to get relevant information.
    
    Output nothing except the tool call.
    """,
    tools=[retrieve_context_tool], # <--- This agent calls the FunctionTool!
    output_key="retrieved_context_raw", # This will store the raw output from the tool
)


# --- RAG Sub-Agent 3: Answer Generation from Context ---
rag_answer_generator = LlmAgent(
    name="RagAnswerGenerator",
    model="gemini-1.5-pro", # Pro for best answer generation and summarization
    description="Generates a simple answer to the question based on the provided relevant context.",
    instruction="""
    You are a helpful tutor for primary school children.
    
    **Original Question:** '{parsed_rag_request_details.extracted_question}'
    **Relevant Context from Study Material:**
    ```
    {retrieved_context_raw.tool_response.relevant_context_text}
    ```
    **Desired Language:** '{parsed_rag_request_details.extracted_language}'
    
    Your task is to:
    1.  Answer the original question strictly based on the provided 'Relevant Context'.
    2.  Simplify the answer drastically for primary school children, using short sentences and basic vocabulary.
    3.  Ensure the answer is in '{parsed_rag_request_details.extracted_language}'.
    4.  Do NOT include analogies or cultural touches yet. Focus solely on accurate, simplified information from the context.
    
    Output *only* the simplified answer text. If the context is not sufficient to answer the question, state that politely.
    """,
    output_key="rag_simplified_answer"
)


# Define the main RAG pipeline
rag_retrieval_pipeline = SequentialAgent(
    name="RagRetrievalPipeline",
    description="A pipeline to retrieve relevant information from an indexed knowledge base and generate a simplified answer.",
    sub_agents=[
        rag_request_parser_agent,      # 1. Parse the incoming request (new first step)
        context_retriever_agent,       # 2. Call the FunctionTool to retrieve context
        rag_answer_generator,          # 3. Generate answer from retrieved context
    ],
)

# You will import and use this pipeline within your knowledge_base_pipeline