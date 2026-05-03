import streamlit as st
import json
from pathlib import Path
from app.src.pipeline import ExtractionPipeline

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

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ About")
st.sidebar.info(
    "This system uses OCR + Rule-based extraction + LLM validation to extract "
    "structured data from unstructured documents."
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
    enable_llm = st.checkbox("Enable LLM (Coming Soon)", value=False, disabled=True)

# Process button
if uploaded_file:
    if st.button("🔍 Extract Data", use_container_width=True):
        with st.spinner("Processing document..."):
            # Save uploaded file temporarily
            temp_path = f"/tmp/{uploaded_file.name}"
            Path("/tmp").mkdir(exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Run pipeline
            pipeline = ExtractionPipeline()
            result = pipeline.process_document(temp_path, document_type)
            
            # Display results
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
            
            # Display extracted fields
            st.subheader("📋 Extracted Data")
            
            if result.extracted_fields:
                # Create a nice table view
                extraction_data = []
                for field_name, field in result.extracted_fields.items():
                    extraction_data.append({
                        "Field": field_name,
                        "Value": field.value,
                        "Confidence": f"{field.confidence:.0%}",
                        "Source": field.source.value
                    })
                
                st.dataframe(extraction_data, use_container_width=True)
                
                # JSON view
                with st.expander("📄 View as JSON"):
                    json_output = {
                        "document_name": result.document_name,
                        "overall_confidence": result.overall_confidence,
                        "fields": {
                            name: {
                                "value": field.value,
                                "confidence": field.confidence,
                                "source": field.source.value
                            }
                            for name, field in result.extracted_fields.items()
                        }
                    }
                    st.json(json_output)
                
                # Download button
                st.download_button(
                    label="📥 Download as JSON",
                    data=json.dumps(json_output, indent=2),
                    file_name=f"{Path(uploaded_file.name).stem}_extracted.json",
                    mime="application/json"
                )
            else:
                st.warning("⚠️ No fields extracted")
            
            # Raw text (if enabled)
            if include_raw_text and result.raw_text:
                with st.expander("📝 Raw OCR Text"):
                    st.text_area("Extracted text:", value=result.raw_text, height=200, disabled=True)
            
            # Errors (if any)
            if result.error:
                st.error(f"❌ Error: {result.error}")

else:
    st.info("👆 Upload a PDF file to get started")
