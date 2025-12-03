import streamlit as st
import openai
import re

# --- 1. Page Configuration (Must be first) ---
st.set_page_config(
    page_title="Pro Rewrite Tool",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS (Fixed for Mobile Dark Mode) ---
st.markdown("""
    <style>
    /* Force Light Mode Appearance */
    :root {
        color-scheme: light !important;
    }
    
    /* General Body - Force Light Background */
    .stApp {
        background-color: #f4f6f9 !important;
        color: #000000 !important;
    }
    
    /* Text Area - FORCE BLACK TEXT regardless of Dark Mode */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Mobile Dark Mode Fix */
        caret-color: #000000 !important;
        border: 1px solid #ced4da !important;
        border-radius: 8px;
        font-family: 'Arial', sans-serif;
        font-size: 16px;
        font-weight: 600;
    }
    
    /* Placeholder Text */
    .stTextArea textarea::placeholder {
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
        opacity: 1;
    }
    
    /* All Labels and Headers */
    label, h1, h2, h3, .stMarkdown, p, .stCaption {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        background-color: #2563eb !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        border-radius: 6px;
        padding: 12px;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. Text Chunking Logic ---
def smart_split_text(text, max_chars=4000):
    sentences = re.split(r'(?<=[.।?!])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# --- 4. OpenRouter API Logic ---
def rewrite_segment(text_chunk, client, model):
    system_prompt = """
    You are an expert professional editor and paraphraser fluent in English and Bengali.
    YOUR TASK: Rewrite the provided text to be 100% unique, human-like, and plagiarism-free.
    RULES:
    1. If input is Bengali, output standard Bengali. If English, use professional English.
    2. Do NOT answer questions. ONLY output the rewritten content.
    3. Change vocabulary and structure but KEEP the meaning.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_chunk}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Error: {str(e)}]"

# --- 5. Main Application Logic ---

# Setup OpenRouter Client
try:
    or_key = st.secrets["OPENROUTER_API_KEY"]
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=or_key,
    )
except:
    st.error("⚠️ Setup Error: OPENROUTER_API_KEY missing in secrets.")
    st.stop()

st.markdown("<h2 style='text-align: center;'>✍️ AI Bulk Text Rewriter (Pro)</h2>", unsafe_allow_html=True)

# Model Selector
model_choice = st.selectbox(
    "Select AI Model (OpenRouter)",
    [
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "google/gemini-pro-1.5"
    ],
    index=0
)

# Layout
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("📥 Input Text")
    input_text = st.text_area("Paste text here (Eng/Ban)", height=500, placeholder="Paste up to 30,000 words here...")
    in_words = len(input_text.split()) if input_text else 0
    st.caption(f"Word Count: {in_words}")

start_rewrite = False
with col_in:
    if st.button("🚀 Rewrite Now"):
        start_rewrite = True

with col_out:
    st.subheader("📤 Rewritten Result")
    output_box = st.empty()
    
    if start_rewrite and input_text:
        chunks = smart_split_text(input_text)
        total_chunks = len(chunks)
        progress_bar = st.progress(0)
        status_text = st.empty()
        final_result = []
        
        for i, chunk in enumerate(chunks):
            status_text.markdown(f"**Processing Part {i+1} of {total_chunks}...**")
            rewritten_text = rewrite_segment(chunk, client, model_choice)
            final_result.append(rewritten_text)
            current_full_text = "\n\n".join(final_result)
            output_box.text_area("Result", value=current_full_text, height=500)
            progress_bar.progress((i + 1) / total_chunks)
        
        status_text.success("✅ Completed successfully!")
        progress_bar.progress(100)
        st.session_state['last_result'] = "\n\n".join(final_result)
    
    elif start_rewrite and not input_text:
        st.warning("Please enter some text first.")
        
    elif 'last_result' in st.session_state:
        output_box.text_area("Result", value=st.session_state['last_result'], height=500)
