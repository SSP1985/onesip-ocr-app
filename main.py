import streamlit as st

# --------- PAGE CONFIGURATION (MUST BE FIRST) ----------
st.set_page_config(
    layout="wide",
    page_title="OneSIP OCR",
    page_icon="📝"
)
# -------------------------------------------------------
# Now you can display your image
st.image("https://drive.google.com/uc?id=1gTnx6qQB54f6KeF3bEP67-HOnhY4INPN", width=120, caption="Sudheer Patibandla")

# ...rest of your imports and code


import os
import base64
import json
import time
from mistralai import Mistral
from dotenv import load_dotenv

APP_TITLE = "OneSIP OCR"
APP_BRAND = "Made with ❤️ by OneSIP.in"
APP_DESC = """
Extract text from PDFs using Mistral OCR.
No key required: Secure API is built-in for OneSIP users!
"""
SIDEBAR_BG = "#F8FAFC"
PRIMARY_COLOR = "#3B82F6"
MAX_UPLOAD_MB = 20

st.set_page_config(
    layout="wide",
    page_title=APP_TITLE,
    page_icon="📝"
)

# ✨ Important notice for mobile users
st.info("**Mobile Upload Tip:** If file upload doesn't work, try using Firefox (Android) or Safari (iOS). Chrome may not support file upload on some devices.")

st.markdown(f"<p style='color:red;font-size:13px;'>Maximum PDF file size allowed: {MAX_UPLOAD_MB} MB per file.</p>", unsafe_allow_html=True)

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    st.error("Missing API key! Please add your MISTRAL_API_KEY in a .env file or Streamlit Cloud secrets.")
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

st.sidebar.markdown(
    f"<div style='background:{SIDEBAR_BG};padding:10px 15px;border-radius:15px;'>"
    "<h3>Welcome to OneSIP OCR</h3>"
    "<p>Fast, accurate OCR for your PDFs.<br>No manual API key needed.</p>"
    "</div>",
    unsafe_allow_html=True
)

if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = []
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = []
if "reset_uploader" not in st.session_state:
    st.session_state["reset_uploader"] = 0

source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_files = []

if source_type == "URL":
    input_url = st.text_area("Paste PDF URLs here (one per line)")
else:
    uploaded_files = st.file_uploader(
        f"Upload PDFs (max {MAX_UPLOAD_MB} MB each)",
        type=["pdf"],
        accept_multiple_files=True,
        key=st.session_state["reset_uploader"]
    )

col_process, col_clear = st.columns([1, 1])
with col_process:
    process_clicked = st.button("Process", type="primary")
with col_clear:
    clear_clicked = st.button("Clear All")

if clear_clicked:
    st.session_state["ocr_result"] = []
    st.session_state["preview_src"] = []
    st.session_state["reset_uploader"] += 1

if process_clicked:
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid PDF URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one PDF file.")
    else:
        client = Mistral(api_key=api_key)
        st.session_state["ocr_result"] = []
        st.session_state["preview_src"] = []

        sources = input_url.split("\n") if source_type == "URL" else uploaded_files

        for idx, source in enumerate(sources):
            if source_type == "Local Upload":
                file_bytes = source.read()
                file_size_mb = len(file_bytes) / (1024 * 1024)
                if file_size_mb > MAX_UPLOAD_MB:
                    st.warning(f"{source.name} exceeds the max upload size of {MAX_UPLOAD_MB} MB. Skipped.")
                    continue
                encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
                document = {
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{encoded_pdf}"
                }
                preview_src = f"data:application/pdf;base64,{encoded_pdf}"
            else:
                document = {"type": "document_url", "document_url": source.strip()}
                preview_src = source.strip()

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

if st.session_state["ocr_result"]:
    for idx, result in enumerate(st.session_state["ocr_result"]):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(f"Input File {idx+1}")
            pdf_src = st.session_state["preview_src"][idx]
            if pdf_src.startswith("http"):
                st.markdown(
                    f'<a href="{pdf_src}" target="_blank" '
                    f'style="font-size:18px;font-weight:bold;color:{PRIMARY_COLOR};text-decoration:underline;">'
                    '📄 Open PDF in New Tab</a>',
                    unsafe_allow_html=True
                )
                st.info("Click above to view or download the PDF in a new tab.")
            else:
                st.info(
                    "For security reasons, browsers block the preview and download of uploaded PDFs. "
                    "Please save your file after upload, or use a PDF reader on your computer."
                )
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

# (No risky CSS for input[type='file']!)

