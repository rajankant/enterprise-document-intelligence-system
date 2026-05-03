from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pathlib import Path

from app.models.schemas import ExtractionResponse, DocumentExtraction, ExtractionRequest
from app.src.pipeline import ExtractionPipeline

# Initialize app
app = FastAPI(
    title="Enterprise Document Intelligence API",
    description="Extract structured data from documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = ExtractionPipeline()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Document Intelligence API"}


@app.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    document_type: str = "invoice"
):
    """
    Extract structured data from a document
    
    Args:
        file: PDF file to process
        document_type: Type of document (invoice, bill, receipt, job_description)
        
    Returns:
        ExtractionResponse with extracted data or error
    """
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Process document
            result: DocumentExtraction = pipeline.process_document(tmp_path, document_type)
            
            if result.error:
                return ExtractionResponse(
                    success=False,
                    data=result,
                    error=result.error,
                    message="Error processing document"
                )
            
            return ExtractionResponse(
                success=True,
                data=result,
                error=None,
                message="Document processed successfully"
            )
        
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@app.post("/extract-batch")
async def extract_batch(files: list[UploadFile] = File(...)):
    """
    Extract data from multiple documents
    
    Args:
        files: List of PDF files
        
    Returns:
        List of extraction results
    """
    results = []
    
    for file in files:
        if file.content_type != "application/pdf":
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "Only PDF files supported"
            })
            continue
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name
            
            try:
                result = pipeline.process_document(tmp_path)
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "data": result.dict()
                })
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}


@app.get("/document-types")
async def get_document_types():
    """Get list of supported document types"""
    return {
        "types": [
            "invoice",
            "bill",
            "receipt",
            "job_description"
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "message": "Request failed"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
