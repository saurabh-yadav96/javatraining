from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from prompts import build_prompt

def generate_manual(frs, code, query):

    full_text = frs + "\n" + code

    # Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200
    )

    docs = splitter.split_text(full_text)

    # Embeddings (LOCAL)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = FAISS.from_texts(docs, embeddings)

    # Retrieval
    relevant_docs = db.similarity_search(query, k=5)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    # Local LLM
    llm = Ollama(model="mistral")

    prompt = build_prompt(context, query)

    response = llm.invoke(prompt)

    return response