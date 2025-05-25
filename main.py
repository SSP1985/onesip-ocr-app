import streamlit as st
import os
import base64
import json
import time
from mistralai import Mistral
from dotenv import load_dotenv

# ----------------- CUSTOMIZE HERE --------------------
APP_TITLE = "OneSIP OCR"
APP_BRAND = "Made with ❤️ by OneSIP.in"
APP_DESC = """
Extract text from PDFs or images using Mistral OCR.
No key required: Secure API is built-in for OneSIP users!
"""
SIDEBAR_BG = "#F8FAFC"
PRIMARY_COLOR = "#3B82F6"
# ------------------------------------------------------

st.set_page_config(
    layout="wide",
    page_title=APP_TITLE,
    page_icon="📝"
)

load_dotenv()  # Ensure .env is loaded

# Read the API key from the environment
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    st.error("Missing API key! Please add your MISTRAL_API_KEY in a .env file.")
    st.stop()

st.markdown(
    f"<h1 style='color:{PRIMARY_COLOR};font-weight:bold;'>{APP_TITLE}</h1>", 
    unsafe_allow_html=True
)
st.markdown(
    f"<span style='font-size:20px;color:#555;'>{APP_BRAND}</span>", 
    unsafe_allow_html=True
)
with st.expander("About"):
    st.info(APP_DESC.strip())

# Sidebar styling
st.sidebar.markdown(
    f"<div style='background:{SIDEBAR_BG};padding:10px 15px;border-radius:15px;'>"
    "<h3>Welcome to OneSIP OCR</h3>"
    "<p>Fast, accurate OCR for your PDFs and images.<br>No manual API key needed.</p>"
    "</div>",
    unsafe_allow_html=True
)

# Initialize session state variables
if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = []
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = []
if "image_bytes" not in st.session_state:
    st.session_state["image_bytes"] = []

file_type = st.radio("Select file type", ("PDF", "Image"))
source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_files = []

if source_type == "URL":
    input_url = st.text_area("Enter one or multiple URLs (separate with new lines)")
else:
    uploaded_files = st.file_uploader(
        "Upload one or more files", 
        type=["pdf", "jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

# --- Add Process and Clear All buttons side by side ---
col_process, col_clear = st.columns([1, 1])
with col_process:
    process_clicked = st.button("Process", type="primary")
with col_clear:
    clear_clicked = st.button("Clear All")

# --- Clear session state if needed ---
if clear_clicked:
    st.session_state["ocr_result"] = []
    st.session_state["preview_src"] = []
    st.session_state["image_bytes"] = []
    st.experimental_rerun()

# --- Process logic ---
if process_clicked:
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        client = Mistral(api_key=api_key)
        st.session_state["ocr_result"] = []
        st.session_state["preview_src"] = []
        st.session_state["image_bytes"] = []

        sources = input_url.split("\n") if source_type == "URL" else uploaded_files

        for idx, source in enumerate(sources):
            if file_type == "PDF":
                if source_type == "URL":
                    document = {"type": "document_url", "document_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
                    document = {
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{encoded_pdf}"
                    }
                    preview_src = f"data:application/pdf;base64,{encoded_pdf}"
            else:
                if source_type == "URL":
                    document = {"type": "image_url", "image_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    mime_type = source.type
                    encoded_image = base64.b64encode(file_bytes).decode("utf-8")
                    document = {
                        "type": "image_url",
                        "image_url": f"data:{mime_type};base64,{encoded_image}"
                    }
                    preview_src = f"data:{mime_type};base64,{encoded_image}"
                    st.session_state["image_bytes"].append(file_bytes)

            with st.spinner(f"Processing {source if source_type == 'URL' else source.name}..."):
                try:
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document=document,
                        include_image_base64=True
                    )
                    time.sleep(1)
                    pages = ocr_response.pages if hasattr(ocr_response, "pages") else (ocr_response if isinstance(ocr_response, list) else [])
                    result_text = "\n\n".join(page.markdown for page in pages) or "No result found."
                except Exception as e:
                    result_text = f"Error extracting result: {e}"

                st.session_state["ocr_result"].append(result_text)
                st.session_state["preview_src"].append(preview_src)

# --- Display OCR Results ---
if st.session_state["ocr_result"]:
    for idx, result in enumerate(st.session_state["ocr_result"]):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(f"Input File {idx+1}")
            if file_type == "PDF":
                st.markdown(f"**[Download PDF]({st.session_state['preview_src'][idx]})**")
    st.info("PDF preview is blocked in Chrome. Click above to download and open the file.")
            else:
                if source_type == "Local Upload" and st.session_state["image_bytes"]:
                    st.image(st.session_state["image_bytes"][idx], use_column_width=True)
                else:
                    st.image(st.session_state["preview_src"][idx], use_column_width=True)
        with col2:
            st.subheader(f"OCR Text Output {idx+1}")

            st.text_area(
                "Extracted Text", 
                value=result, 
                height=400, 
                key=f"result_{idx}", 
                label_visibility="collapsed"
            )

            def create_download_link(data, filetype, filename):
                b64 = base64.b64encode(data.encode()).decode()
                href = f'<a href="data:{filetype};base64,{b64}" download="{filename}">Download {filename}</a>'
                st.markdown(href, unsafe_allow_html=True)

            create_download_link(result, "text/plain", f"OCR_Output_{idx+1}.txt")
            create_download_link(result, "text/markdown", f"OCR_Output_{idx+1}.md")
            json_data = json.dumps({"ocr_result": result}, ensure_ascii=False, indent=2)
            create_download_link(json_data, "application/json", f"OCR_Output_{idx+1}.json")

# --- Hide Streamlit branding (optional) ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .css-18e3th9 {padding-top: 1rem;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
