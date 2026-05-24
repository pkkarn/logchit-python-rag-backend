import io
from pypdf import PdfReader

def extract_chunks_from_pdf(file_bytes: bytes, chunk_size_words: int = 200, overlap_words: int = 20) -> list[dict]:
    """
    Extracts text from PDF bytes page-by-page and splits it into chunks of ~200 words.
    Returns a list of dicts: [{"page_number": int, "chunk_index": int, "text": str}]
    """
    # 1. Load the PDF from memory using BytesIO
    reader = PdfReader(io.BytesIO(file_bytes))
    chunks = []
    
    # 2. Process page-by-page
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text()
        if not text:
            continue
            
        words = text.split()
        num_words = len(words)
        
        # 3. Slide the window over the words
        start_idx = 0
        chunk_idx = 0
        while start_idx < num_words:
            end_idx = min(start_idx + chunk_size_words, num_words)
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "page_number": page_num,
                "chunk_index": chunk_idx,
                "text": chunk_text
            })
            
            chunk_idx += 1
            # Move the window forward, keeping the overlap
            start_idx += (chunk_size_words - overlap_words)
            
            # Safety check: prevent infinite loop if word count is tiny
            if start_idx >= num_words or (chunk_size_words - overlap_words) <= 0:
                break
                
    return chunks