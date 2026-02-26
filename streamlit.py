import requests
import streamlit as st
import pandas as pd
from google import genai

def get_file_from_supabase(bucket, file_path, project_url, service_key):
    # Construct the endpoint
    url = f"{project_url}/storage/v1/object/authenticated/{bucket}/{file_path}.md"

    headers = {
        "Authorization": f"Bearer {service_key}",
        "apiKey": service_key,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # File bytes are in response.content
        file_bytes = response.content
        return file_bytes.decode('utf-8')  # Return as string
    else:
        st.error(f"Failed to retrieve file: {response.status_code}")
        return "fail"

def get_chat_from_supabase(table, file_path, project_url, service_key):
    # Construct the endpoint
    url = f"{project_url}/rest/v1/{table}?report_id=eq.{file_path}"

    headers = {
        "Authorization": f"Bearer {service_key}",
        "apiKey": service_key,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, params={"select": "*"})

    if response.status_code == 200:
        data = response.json()
        # st.write(data, "a")
        data = pd.DataFrame(data)
        if data.empty:
            # make an empty default dataframe with the same structure as the chat table
            default_row = {
                "id": [None], 
                "report_id": [file_path], 
                "role": ["ai"], 
                "content": ["Chat history is empty. Start the conversation!"]
            }
            data = pd.DataFrame(default_row)
        return data

    else:
        st.error(f"Error: {response.status_code}")
        return "fail"
        # st.write(response.text)

def send_chat_to_supabase(table, file_path, role, message, project_url, service_key):
    url = f"{project_url}/rest/v1/{table}"

    new_row = {
        "report_id": file_path,
        "role": role,
        "content": message,
        "created_at": "now()" # PostgREST handles now() or you can use a string timestamp
    }

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" # Options: return=minimal (fastest) or return=representation (returns the created row)
    }

    response = requests.post(url, headers=headers, json=new_row)

    if response.status_code == 201: # 201 is the standard 'Created' status code
        # st.success("Row added successfully!")
        return True
    else:
        st.error(f"Failed to add row: {response.status_code} \n {response.text}")
        return False

def main():
    # display/layout configuration
    st.set_page_config(layout="wide")
    FIXED_HEIGHT = 500

    report_id = st.query_params.get("report_id")
    if not report_id:
        st.warning("No report_id provided in the URL. Please add ?report_id=your_report_id to the URL.")
        return
    # report_id = 'A-1' ?report_id=CDN%20%26%20App%20Security-Akamai
    # /?report_id=pt-privy-identitas-digital-verification-cost-2026-02-26

    # Reduce top padding
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 3rem !important;
                padding-bottom: 0rem !important;
            }
            [data-testid="stDecoration"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # add header
    # format the title name
    title = report_id.split("-")[:-3]
    title = " ".join([word.capitalize() for word in title])

    st.markdown(
        f"""
        <style>
        .header-container {{
            background-color: #003C3B;
            padding: 15px 20px;
            border-radius: 5px;
            color: #CEFE06;
            margin-bottom: 5px;
            text-align: center;
        }}
        </style>

        <div class="header-container">
            <h1 style='margin:0; padding:0; font-size: 1.8rem;'>{title}</h1>
            <p style='margin:0; opacity: 0.8;'>Procurement Intelligence Report Chat Bot</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # supabase configuration
    supabase_url = st.secrets.supabase["url"]
    supabase_service_key = st.secrets.supabase["service_key"]

    col1, col2 = st.columns([3, 2])

    # report display
    with col1:
        with st.container(height = FIXED_HEIGHT):
            # connect to supabase and fetch markdown content based on report_id
            try:
                bucket = st.secrets.supabase["report_bucket"]

                markdown_content = get_file_from_supabase(
                    bucket=bucket,
                    file_path=report_id,
                    project_url=supabase_url,
                    service_key=supabase_service_key
                )
                if(markdown_content != "fail"):
                    st.markdown(markdown_content, unsafe_allow_html=True)
                else:
                    st.warning("Report content not found.")

            except Exception as e:
                st.warning(f"Failed to load report content: {e}")

    # chat display
    with col2:
        chat_container = st.container(height = FIXED_HEIGHT-80)
        table_name = st.secrets.supabase["chat_table"]

        # Initialize session state
        if "messages" not in st.session_state:
            try:
                chat_history = get_chat_from_supabase(
                    table=table_name,
                    file_path=report_id,
                    project_url=supabase_url,
                    service_key=supabase_service_key
                )
                if isinstance(chat_history, pd.DataFrame):
                    st.session_state.messages = []
                    for _, row in chat_history.iterrows():
                        st.session_state.messages.append({"role": row["role"], "content": row["content"]})
                    
                    # display the message
                    with chat_container:
                        for message in st.session_state.messages:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])

                elif chat_history == "fail":
                    st.warning("Failed to load chat history.")

            except Exception as e:
                st.warning(f"Failed to load chat history: {e}")
                st.session_state.messages = []

        spinner_placeholder = st.empty()

        # chat input
        if prompt := st.chat_input("What is up?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display the new message immediately in the container area
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # # Optional: Force rerun to ensure logic remains synchronized
            # st.rerun()

            # send user message to supabase
            try:
                result = send_chat_to_supabase(
                    table=table_name,
                    file_path=report_id,
                    role="user",
                    message=prompt,
                    project_url=supabase_url,
                    service_key=supabase_service_key
                )
                if not result:
                    st.warning("Failed to send chat message to Supabase.")

            except Exception as e:
                st.warning(f"Failed to send chat message: {e}")
            
            # prompt gemini
            # status bar
            with spinner_placeholder:
                with st.spinner("Gemini is thinking...", show_time=True):

                    # initialize the model
                    api_key = st.secrets.gemini["api_key"]
                    client = genai.Client(api_key=api_key)
                    chat = client.chats.create(model="gemini-3-flash-preview")

                    # send the user message as a prompt to the model
                    try:
                        response = chat.send_message(prompt)
                    except Exception as e:
                        st.warning(f"Failed to get response from Gemini: {e}")
                        response = None
                        
            spinner_placeholder.empty()

            # add the model response to the chat history
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response.text})

                # Display the new message immediately in the container area
                with chat_container:
                    with st.chat_message("ai"):
                        st.markdown(response.text)
                    
                # send the model response to supabase
                try:
                    result = send_chat_to_supabase(
                        table=table_name,
                        file_path=report_id,
                        role="ai",
                        message=response.text,
                        project_url=supabase_url,
                        service_key=supabase_service_key
                    )
                    if not result:
                        st.warning("Failed to send chat message to Supabase.")

                except Exception as e:
                    st.warning(f"Failed to save chat message to Supabase: {e}")

if __name__ == "__main__":
    main()