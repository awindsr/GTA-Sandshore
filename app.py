import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template, hide_st_style, footer
from langchain.llms import HuggingFaceHub
from matplotlib import style

# Define the path to the PDF document
PDF_PATH = 'Assets/test.pdf'

# Function to extract text from a PDF
def get_pdf_text(pdf_path):
    text = ""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to split text into chunks
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create a vector store from text chunks
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# Function to create a conversation chain
def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

# Function to handle user input and generate responses
def handle_userinput(user_question, vectorstore):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

    # Recreate the vector store with updated texts
    user_input_text = user_question
    bot_response_text = response['chat_history'][-1].content  # Get the bot's last response
    updated_texts = [user_input_text, bot_response_text]
    vectorstore = get_vectorstore(updated_texts)

# Main function
def main():
    load_dotenv()
    st.set_page_config(page_title="Electric Substation Bot",
                    page_icon="icon.png")
    st.write(css, unsafe_allow_html=True)

    # Initialize session state variables
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("ChatBot for Substation")

    with st.spinner("Processing"):
        raw_text = get_pdf_text(PDF_PATH)
        text_chunks = get_text_chunks(raw_text)
        vectorstore = get_vectorstore(text_chunks)
        st.session_state.conversation = get_conversation_chain(vectorstore)
        st.success("Ready to answer your questions")

    user_question = st.text_input("Ask a question:")

    if user_question:
        handle_userinput(user_question, vectorstore)

    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.markdown(footer, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
