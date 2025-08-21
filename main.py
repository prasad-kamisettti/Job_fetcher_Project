# main.py (Updated with NLP Keyword Extraction)
import docx
import fitz      # PyMuPDF
import spacy     # NEW: Import spaCy

# --- NEW: Load the spaCy language model ---
# We do this once at the start so it's ready to use.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model not found. Please run 'python -m spacy download en_core_web_sm'")
    exit() # Exit the script if the model isn't downloaded

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a given PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except FileNotFoundError:
        return f"Error: The file '{pdf_path}' was not found."
    except Exception as e:
        print(f"An unexpected error occurred while reading the PDF.\nDETAILS: {e}")
        return ""

def extract_text_from_docx(docx_path):
    """Extracts all text from a given DOCX file."""
    try:
        doc = docx.Document(docx_path)
        all_paragraphs = [para.text for para in doc.paragraphs]
        return "\n".join(all_paragraphs)
    except FileNotFoundError:
        return f"Error: The file '{docx_path}' was not found."
    except Exception as e:
        print(f"An unexpected error occurred while reading the DOCX.\nDETAILS: {e}")
        return ""

# --- NEW: Function to extract keywords using spaCy ---
def extract_keywords(text):
    """
    Extracts key skills and technologies from the resume text.
    """
    # A set is used to automatically handle duplicates
    keywords = set()
    
    # Process the entire text with spaCy
    doc = nlp(text)
    
    # Iterate through the recognized entities in the text
    # Entities are things like names, organizations, locations, etc.
    # We will also look for nouns and proper nouns.
    for token in doc:
        # We're interested in Nouns (like 'python', 'analysis') 
        # and Proper Nouns (like 'Amazon', 'SQL')
        if token.pos_ in ['NOUN', 'PROPN']:
            # Clean the token: lowercase and remove leading/trailing spaces
            cleaned_token = token.text.strip().lower()
            # Add to our set of keywords
            keywords.add(cleaned_token)
            
    return list(keywords) # Convert the set back to a list

# --- Main part of the script ---
if __name__ == "__main__":
    
    # --- CONFIGURATION ---
    resume_filename = "Vara_Prasad-Resume.pdf"  # <--- MAKE SURE THIS IS CORRECT
    
    print(f"--- Step 1: Reading Resume: {resume_filename} ---")
    if resume_filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_filename)
    elif resume_filename.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_filename)
    else:
        resume_text = ""
        print("Error: Unsupported file type. Please use a .pdf or .docx file.")

    if resume_text:
        # print("\n--- RESUME TEXT EXTRACTED ---")
        # print(resume_text) # We can comment this out to keep the output clean
        
        print("\n--- Step 2: Extracting Keywords using NLP ---")
        keywords = extract_keywords(resume_text)
        
        print("\n--- Found Keywords ---")
        # Let's format them nicely in a comma-separated list
        print(", ".join(keywords))
        print("--- End of Keywords ---")
    else:
        print("\nCould not read resume. Cannot proceed to keyword extraction.")