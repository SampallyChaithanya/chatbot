import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Excel Chatbot (OpenRouter)", page_icon="📊")
st.title("🤖 Chat with Your Excel or CSV File")

# Sidebar for API and model
with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("🔑 Enter your OpenRouter API Key", type="password")
    model = st.selectbox(
        "🤖 Choose a model",
        [
        "meta-llama/llama-3-70b-instruct",       # 🧠 Very powerful open-source model
        "mistralai/mixtral-8x7b",                # ⚡ Fast, efficient
        "mistralai/mistral-7b-instruct",         # ⚡ Small, good for quick replies
        "cohere/command-r",                      # 📊 Excellent for structured data
        "cohere/command-r-plus",                 # 📊 Enhanced version
        "anthropic/claude-3-haiku:beta",         # 💡 Fastest Claude model
        "openchat/openchat-3.5-1210",            # 🗨️ Chat-tuned model
        "nousresearch/nous-capybara-7b",         # 🐹 Balanced LLM
        "gryphe/mythomist-7b",                   # 📚 Creative reasoning model
        "google/gemma-7b-it" 
        ]
    )

# Upload the file
uploaded_file = st.file_uploader("📂 Upload an Excel or CSV file", type=["xlsx", "csv"])

df = None
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet = st.selectbox("📄 Select a sheet", xls.sheet_names)
            df = pd.read_excel(xls, sheet_name=sheet)

        st.success("✅ File loaded successfully!")
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"❌ Failed to read the file: {e}")

# Session memory
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful data analyst assistant. Answer questions based only on the provided dataset."}
    ]

# Show previous messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
query = st.chat_input("Ask a question about your data...")

if query and df is not None and api_key:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state["messages"].append({"role": "user", "content": query})

    # Convert dataset to CSV (limited length)
    max_chars = 8000
    csv_data = df.to_csv(index=False)
    if len(csv_data) > max_chars:
        csv_data = csv_data[:max_chars] + "\n...(truncated)"

    # Create prompt
    prompt = f"""
The user uploaded the following dataset sample (as CSV):

--- BEGIN DATA SAMPLE ---
{csv_data}
--- END DATA SAMPLE ---

Now answer this question based only on the data:
{query}
"""

    # Send to OpenRouter
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
        else:
            st.error(f"❌ OpenRouter API error: {response.status_code}\n{response.text}")

    except Exception as e:
        st.error(f"❌ Request failed: {e}")

elif query and not uploaded_file:
    st.warning("📁 Please upload a file before asking a question.")
elif query and not api_key:
    st.warning("🔑 Please enter your OpenRouter API key in the sidebar.")
