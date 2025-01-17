import os
import requests
from bs4 import BeautifulSoup
from langchain_openai import OpenAIEmbeddings
#from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
#from langchain_community.document_loaders import TextLoader
import fitz
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter

def extract_text_from_url(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.content, 'html.parser')
  return soup.get_text()

def extract_text_from_pdf(pdf_path):
  pdf = fitz.open(pdf_path)

  for page_num in range(len(pdf)):
    page = pdf[page_num]
    text += page.get_text()

  return text

def main():

    # List of URLs
    urls = [
        "https://www.url1",
        "https://www.url2",
        "https://www.url3"
    ]
    
    # Ask a question that's related to the knowlege base you are providing?
    users_question = "your question goes here"

    # make sure to add your api key to env
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI()

    # File to write the URLs
    file_name = "knowledgebase.txt"

    # Open the file in write mode
    with open(file_name, 'w', encoding='utf-8') as file:
        # Loop through the list of URLs
        for url in urls:
            text = extract_text_from_url(url)
            text = text.replace('\n', '')
            file.write(text + "\n")

    # load the document
    with open(f'./{file_name}', encoding='utf-8') as f:
        text = f.read()

    # define the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap  = 100,
        length_function = len,
    )

    texts = text_splitter.create_documents([text])

    # define the embeddings model
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    # use the text chunks and the embeddings model to fill our vector store
    db = Chroma.from_documents(texts, embeddings)

    # use our vector store to find similar text chunks
    results = db.similarity_search(
        query=users_question,
        k=5
    )

    # define the prompt template
    context_template = """
    You are a chat bot who loves to help people! Given the following context sections, answer the
    question using only the given context. If you are unsure and the answer is not
    explicitly written in the documentation, say "Sorry, I don't know how to help with that."

    Context sections:
    {context}

    Question:
    {users_question}

    Answer:
    """

    # define the prompt template to test without the context provided in the knowledge base
    gpt_template = """
    You are a chat bot who loves to help people! Answer the
    question.

    Question:
    {users_question}

    Answer:
    """

    # define the LLM you want to use
    llm = OpenAI(temperature=1)

    prompt = PromptTemplate(template=context_template, input_variables=["context", "users_question"])

    # fill the prompt template
    prompt_text = prompt.format(context = results, users_question = users_question)
    
    # ask the defined LLM
    response = llm.invoke(prompt_text)
 
    print(users_question)
    print(response)

if __name__ == "__main__":
    main()
