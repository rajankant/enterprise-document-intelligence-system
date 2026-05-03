from app.src.ocr import extract_text_from_pdf

text = extract_text_from_pdf(r"C:\Users\kashy\Projects\AI Projects\ai-document-intelligence\enterprise-document-intelligence-system\app\input\JD-AIPython (1).pdf")

print(text[:1000])
