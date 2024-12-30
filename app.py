import streamlit as st
from pathlib import Path
from langchain.agents import initialize_agent
from langchain_community.utilities import SQLDatabase  
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StdOutCallbackHandler
from langchain.tools import Tool
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy import create_engine
from config import config
from urllib.parse import quote  
from langchain_groq import ChatGroq
import os

st.set_page_config(page_title="LangChain: Postgres AI", page_icon="📚")
st.title("📚 LangChain: Postgres AI")


api_key = st.sidebar.text_input(label="Groq API Key", type="password")
if not api_key:
    st.error("Groq API Key not found. Please enter it in the sidebar.")
    st.stop()


llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-70b-versatile", streaming=True)



def configure_db():
    """Establish and return a connection to the PostgreSQL database using SQLAlchemy."""
    try:
        
        params = config()

        
        user = quote(params["user"])
        password = quote(params["password"])
        host = params["host"]
        port = params["port"]
        database = params["database"]

        
        connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        print(f"Connection string: {connection_string}")  

        
        engine = create_engine(connection_string)
        return SQLDatabase(engine)
    except KeyError as key_error:
        st.error(f"Missing database connection parameter: {key_error}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to configure the database: {e}")
        st.stop()






try:
    db = configure_db()
except Exception as e:
    st.error(f"Database configuration failed: {e}")
    st.stop()


def query_database(query):
    try:
        print(f"Executing query: {query}")  
        sanitized_query = query.strip().strip(";")
        return db.run(sanitized_query)
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        st.write("Please ensure your column names and query are correct. For example, use 'damages' instead of 'damage' if that is the correct column name.")
        return None



output_parser = JsonOutputParser()

description = """
Use this to query the table named vehicle_data from the database. 
The table contains the following columns:
- reg_n03: Vehicle registration number
- parts: Vehicle parts
- damages: Types of damages to the vehicle
- fleet: The fleet to which the vehicle belongs
- make: The make of the vehicle
- model: The model of the vehicle
- id: unique identifier 
"""



agent = initialize_agent(
    tools=[Tool(name="SQL Query Tool", func=query_database, description=description)],
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    output_parser=output_parser,
    handle_parsing_errors=True  
)


if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


user_query = st.chat_input(placeholder="Ask anything from the database")

few_shot_examples = """





"""

few_shot_prompt = f"{few_shot_examples}\nUser Query: {user_query}"

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        stdout_callback = StdOutCallbackHandler()
        try:
            response = agent.run(few_shot_prompt, callbacks=[stdout_callback])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)
        except Exception as e:
            st.error(f"Failed to process the query: {e}")
