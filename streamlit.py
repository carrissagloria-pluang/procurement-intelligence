import streamlit as st
import pandas as pd

# display/layout configuration
st.set_page_config(layout="wide")
FIXED_HEIGHT = 500
logo_url = 'app/static/pluang.png'

# test case
report_id = 'A-1'
filename = 'CDN & App Security-Akamai'
title = "Akamai - CDN"
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


col1, col2 = st.columns([3, 2])

with col1:
    with st.container(height = FIXED_HEIGHT):
        with open(f'{filename}.md', "r") as f:
            markdown_content = f.read()
        st.markdown(markdown_content, unsafe_allow_html=True)

with col2:
    # 1. CREATE THE CONTAINER FIRST
    # This acts as the 'anchor' for all chat messages
    chat_container = st.container(height = FIXED_HEIGHT-80)

    # Initialize session state
    if "messages" not in st.session_state:
        try:
            chat_history = pd.read_csv("chat history example.csv")
            chat_history = chat_history[chat_history["report_id"] == report_id]
            st.session_state.messages = []
            for _, row in chat_history.iterrows():
                st.session_state.messages.append({"role": row["role"], "content": row["message"]})
        except:
            st.session_state.messages = []

    # 2. DISPLAY MESSAGES INSIDE THE CONTAINER
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 3. CHAT INPUT STAYS OUTSIDE (and therefore below) THE CONTAINER
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display the new message immediately in the container area
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Optional: Force rerun to ensure logic remains synchronized
        st.rerun()