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

# --- 2. Custom CSS for Professional SaaS Look ---
st.markdown("""
    <style>
    /* General Body */
    .stApp {background-color: #f4f6f9;}
    
    /* Input/Output Text Areas */
    .stTextArea textarea {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 8px;
        font-family: 'Arial', sans-serif;
        font-size: 16px;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 6px;
        padding: 12px;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    
    /* Login Box */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 30px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. Authentication System ---
def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Login UI
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'><h3>🔒 Secure Access</h3></div>", unsafe_allow_html=True)
        email_input = st.text_input("Email Address")
        password_input = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Verify Email and Password
            valid_email = "mdsohug781@gmail.com"
            try:
                valid_pass = st.secrets["APP_PASSWORD"]
            except:
                st.error("Setup Error: APP_PASSWORD not found in secrets.")
                return False

            if email_input.strip() == valid_email and password_input == valid_pass:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⛔ Access Denied: Invalid Email or Password.")
    
    return False

# --- 4. Text Chunking Logic (Bengali & English Support) ---
def smart_split_text(text, max_chars=4000):
    """
    Splits text while respecting Bengali (।) and English (.) punctuation.
    Prevents cutting sentences in half.
    """
    # Split by sentence delimiters (period, bengali dari, question marks, etc.)
    # This regex looks for delimiters and keeps them attached to the sentence
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

# --- 5. OpenRouter API Logic ---
def rewrite_segment(text_chunk, client, model):
    system_prompt = """
    You are an expert professional editor and paraphraser fluent in English and Bengali.
    
    YOUR TASK:
    Rewrite the provided text to be 100% unique, human-like, and plagiarism-free.
    
    RULES:
    1. **Language Detection:** If input is Bengali, output standard Bengali (প্রমিত বাংলা). If English, use professional English.
    2. **No Chat:** Do NOT answer questions. Do NOT start with "Here is the text". ONLY output the rewritten content.
    3. **Quality:** Change vocabulary and sentence structure but KEEP the original meaning.
    4. **Context:** Ensure smooth transitions between sentences.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_chunk}
            ],
            temperature=0.7, # Balanced creativity
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Error: {str(e)}]"

# --- 6. Main Application Layout ---
if check_authentication():
    # Setup OpenRouter Client
    try:
        or_key = st.secrets["OPENROUTER_API_KEY"]
        # OpenRouter uses the standard OpenAI SDK but with a different Base URL
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
            "openai/gpt-4o",              # Best Quality (Expensive)
            "anthropic/claude-3.5-sonnet", # Best for Human-like Writing
            "openai/gpt-4o-mini",         # Cheapest & Fastest
            "google/gemini-pro-1.5"       # Good Context
        ],
        index=0
    )

    # Input & Output Columns
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.subheader("📥 Input Text")
        input_text = st.text_area("Paste text here (Eng/Ban)", height=500, placeholder="Paste up to 30,000 words here...")
        in_words = len(input_text.split()) if input_text else 0
        st.caption(f"Word Count: {in_words}")

    # Process Button
    start_rewrite = False
    with col_in:
        if st.button("🚀 Rewrite Now"):
            start_rewrite = True

    # Output Logic
    with col_out:
        st.subheader("📤 Rewritten Result")
        output_box = st.empty()
        
        if start_rewrite and input_text:
            # 1. Split Text
            chunks = smart_split_text(input_text)
            total_chunks = len(chunks)
            
            # 2. Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            final_result = []
            
            # 3. Processing Loop
            for i, chunk in enumerate(chunks):
                status_text.markdown(f"**Processing Part {i+1} of {total_chunks}...**")
                
                # Call API
                rewritten_text = rewrite_segment(chunk, client, model_choice)
                final_result.append(rewritten_text)
                
                # Update Stream output dynamically
                current_full_text = "\n\n".join(final_result)
                output_box.text_area("Result", value=current_full_text, height=500)
                
                # Update progress
                progress_bar.progress((i + 1) / total_chunks)
            
            # 4. Final Polish
            status_text.success("✅ Completed successfully!")
            progress_bar.progress(100)
            st.session_state['last_result'] = "\n\n".join(final_result)
        
        elif start_rewrite and not input_text:
            st.warning("Please enter some text first.")
            
        # Persistence (Keep text after refresh)
        elif 'last_result' in st.session_state:
             output_box.text_area("Result", value=st.session_state['last_result'], height=500)
