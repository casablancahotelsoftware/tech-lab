
from langchain_core.messages import SystemMessage, HumanMessage

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to your Qdrant instance (adjust host/port as needed)
qdrant_client = QdrantClient(host="localhost", port=6333)

# Set up the embedding function
embeddings = AzureOpenAIEmbeddings(
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_EMBEDDINGS_BASE_URL"),
    api_key=os.getenv("AZURE_EMBEDDINGS_API_KEY"),
    azure_deployment="text-embedding-3-large"
)

llm = AzureChatOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_EMBEDDINGS_BASE_URL"),
    api_key=os.getenv("AZURE_EMBEDDINGS_API_KEY"),
    azure_deployment="gpt-4.1-mini"
)

# Create the vector store interface
qdrant = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name="cleanarchitecture",
    url="http://localhost:6333",
    content_payload_key="document", 
)

# Create the retriever
retriever = qdrant.as_retriever()

# Define a system prompt that tells the model how to use the retrieved context
system_prompt = """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.
Context: {context}:"""
    
# Define a question
question = """What is Clean Architecture?"""

# Retrieve relevant documents
docs = retriever.invoke(question)

# Combine the documents into a single string
docs_text = "".join(d.page_content for d in docs)

print(f"Retrieved {len(docs)} documents.")
print(docs_text)  # Output the retrieved context

# Populate the system prompt with the retrieved context
system_prompt_fmt = system_prompt.format(context=docs_text)

# Generate a response
questions = llm.invoke([SystemMessage(content=system_prompt_fmt),
                          HumanMessage(content=question)])

print(questions.content)  # Output the response