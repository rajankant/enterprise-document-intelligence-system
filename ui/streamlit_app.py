import streamlit as st
import json
import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.src.pipeline import ExtractionPipeline
from rag.rag_service import RAGService

# Page config
st.set_page_config(
    page_title="Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📄 Enterprise Document Intelligence System")
st.markdown("Extract structured data from documents using AI + Rules + Validation")

# Sidebar
st.sidebar.header("⚙️ Configuration")
document_type = st.sidebar.selectbox(
    "Document Type",
    ["invoice", "bill", "receipt", "job_description"]
)

sample_dir = PROJECT_ROOT / "app" / "input"
demo_documents = sorted([p.name for p in sample_dir.glob("*.pdf")]) if sample_dir.exists() else []
use_demo_document = st.sidebar.checkbox("Use built-in demo PDF", value=True)
selected_demo = st.sidebar.selectbox(
    "Demo document",
    demo_documents or ["No demo PDF available"],
    index=0 if demo_documents else 0,
    disabled=not bool(demo_documents),
)

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ About")
st.sidebar.info(
    "This system uses OCR + Rule-based extraction + LLM validation to extract "
    "structured data from unstructured documents. The demo PDF option is ideal for testing without uploading a file."
)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf"
    )

with col2:
    st.subheader("⚙️ Processing Options")
    include_raw_text = st.checkbox("Include raw OCR text", value=False)
    enable_llm = st.checkbox("🤖 Enable AI (LLM) Extraction", value=False)

# RAG query section
st.markdown("---")
st.subheader("🔎 RAG Search")
rag_question = st.text_area(
    "Ask a question about the current document or the demo files",
    value="Who is the vendor or client in the document?",
    height=100,
)
if st.button("Run RAG Query"):
    rag_service = RAGService()
    files = []
    if use_demo_document and demo_documents:
        files = [str(sample_dir / selected_demo)]
    elif uploaded_file is not None:
        temp_path = sample_dir / uploaded_file.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(uploaded_file.getbuffer())
        files = [str(temp_path)]
    else:
        files = [str(path) for path in sorted(sample_dir.glob("*.pdf")) if path.is_file()]

    if files:
        rag_service.index_documents(files)
        results = rag_service.query(rag_question, top_k=3)
        if results:
            st.success("RAG retrieval complete")
            for item in results:
                with st.expander(f"Match score: {item['score']:.2f}"):
                    st.write(item["text"])
        else:
            st.warning("No relevant chunks were found for that question.")
    else:
        st.warning("No documents available for RAG search.")

# Process button
if uploaded_file or (use_demo_document and demo_documents):
    if st.button("🔍 Extract Data", use_container_width=True):
        with st.spinner("Processing document..."):
            if use_demo_document and demo_documents:
                temp_path = str(sample_dir / selected_demo)
            else:
                temp_path = str(Path(tempfile.gettempdir()) / uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Run pipeline
            pipeline = ExtractionPipeline(use_llm=enable_llm)
            result = pipeline.process_document(temp_path, document_type)
            
            # Display results
            if result.error:
                st.error(f"❌ Processing failed: {result.error}")
            else:
                st.success("✅ Processing complete!")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Confidence", f"{result.overall_confidence:.0%}")
            with col2:
                st.metric("Pages Processed", result.page_count)
            with col3:
                st.metric("Fields Extracted", len(result.extracted_fields))
            with col4:
                st.metric("Processing Time", f"{result.processing_time}s")
            
            # Tabbed interface for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Extracted Fields", "📝 Raw OCR Text", "🔍 All Attempts", "💾 Downloads"])
            
            with tab1:
                st.subheader("Extracted Fields")
                if result.extracted_fields:
                    # Create a nice table view
                    extraction_data = []
                    for field_name, field in result.extracted_fields.items():
                        extraction_data.append({
                            "Field": field_name,
                            "Value": str(field.value)[:100],  # Truncate for display
                            "Confidence": f"{field.confidence:.0%}",
                            "Source": field.source.value
                        })
                    
                    st.dataframe(extraction_data, use_container_width=True)
                    
                    # Expandable details
                    for field_name, field in result.extracted_fields.items():
                        with st.expander(f"📌 {field_name} - {field.confidence:.0%}"):
                            col_left, col_right = st.columns(2)
                            with col_left:
                                st.write(f"**Value:** {field.value}")
                                st.write(f"**Confidence:** {field.confidence:.2%}")
                            with col_right:
                                st.write(f"**Source:** {field.source.value}")
                                if field.raw_text:
                                    st.write(f"**Raw Text:** {field.raw_text[:200]}")
                else:
                    st.warning("⚠️ No fields extracted")
            
            with tab2:
                st.subheader("Raw OCR Text (Full Document)")
                if result.raw_text:
                    # Show statistics
                    col_left, col_middle, col_right = st.columns(3)
                    with col_left:
                        st.metric("Total Characters", len(result.raw_text))
                    with col_middle:
                        num_lines = len(result.raw_text.split('\n'))
                        st.metric("Total Lines", num_lines)
                    with col_right:
                        num_words = len(result.raw_text.split())
                        st.metric("Total Words", num_words)
                    
                    # Text area with full content
                    st.text_area(
                        "Full extracted text from all pages:",
                        value=result.raw_text,
                        height=400,
                        disabled=True
                    )
                else:
                    st.info("No raw text available")
            
            with tab3:
                st.subheader("Extraction Attempts (All Fields Tried)")
                extraction_attempts = getattr(result, 'all_extraction_attempts', None) or {}
                if extraction_attempts:
                    for field_name, attempts in extraction_attempts.items():
                        if attempts:
                            with st.expander(f"🔍 {field_name} ({len(attempts)} attempts)"):
                                for i, attempt in enumerate(attempts, 1):
                                    if attempt.get("matched"):
                                        st.success(f"**Attempt {i}** ✓")
                                        st.write(f"Value: `{attempt.get('value', 'N/A')}`")
                                        st.write(f"Confidence: {attempt.get('confidence', 0):.0%}")
                                        st.write(f"Pattern: `{attempt.get('pattern', 'N/A')[:80]}`")
                                    else:
                                        st.info(f"**Attempt {i}** - No match found")
                                    st.divider()
                else:
                    st.info("No extraction attempts data available")
            
            with tab4:
                st.subheader("Download Raw Data")
                
                # Prepare comprehensive JSON output with safe attribute access
                extraction_attempts = getattr(result, 'all_extraction_attempts', {}) or {}
                raw_ocr_data = getattr(result, 'raw_ocr_data', {}) or {}
                
                comprehensive_data = {
                    "document_name": result.document_name,
                    "processing_metadata": {
                        "page_count": result.page_count,
                        "processing_time_seconds": result.processing_time,
                        "overall_confidence": result.overall_confidence
                    },
                    "extracted_fields": {
                        name: {
                            "value": field.value,
                            "confidence": field.confidence,
                            "source": field.source.value,
                            "raw_text": field.raw_text
                        }
                        for name, field in result.extracted_fields.items()
                    },
                    "all_extraction_attempts": extraction_attempts,
                    "raw_ocr_data": raw_ocr_data
                }
                
                # Download options
                col_down1, col_down2, col_down3 = st.columns(3)
                
                with col_down1:
                    # Download extracted fields only (clean JSON)
                    clean_json = {
                        "document_name": result.document_name,
                        "fields": {
                            name: {
                                "value": field.value,
                                "confidence": field.confidence,
                                "source": field.source.value
                            }
                            for name, field in result.extracted_fields.items()
                        }
                    }
                    st.download_button(
                        label="📥 Fields Only (JSON)",
                        data=json.dumps(clean_json, indent=2),
                        file_name=f"{Path(uploaded_file.name).stem}_fields.json",
                        mime="application/json"
                    )
                
                with col_down2:
                    # Download comprehensive data
                    st.download_button(
                        label="📥 All Data (JSON)",
                        data=json.dumps(comprehensive_data, indent=2),
                        file_name=f"{Path(uploaded_file.name).stem}_complete.json",
                        mime="application/json"
                    )
                
                with col_down3:
                    # Download raw OCR text
                    st.download_button(
                        label="📥 Raw OCR Text",
                        data=result.raw_text,
                        file_name=f"{Path(uploaded_file.name).stem}_raw_ocr.txt",
                        mime="text/plain"
                    )
                
                st.divider()
                st.subheader("Data Preview")
                st.write("**Comprehensive JSON Structure:**")
                st.json(comprehensive_data)

else:
    st.info("👆 Upload a PDF file to get started")