"""
Extract synonyms from the Complete Dictionary of Synonyms and Antonyms PDF
and use them to expand our emotion lexicon.
"""
import re
import json
from PyPDF2 import PdfReader

PDF_PATH = r"c:\Users\chris\Downloads\pdfcoffee.com_complete-dictionary-pdf-free.pdf"
EMOTIONS_FILE = "data/emotions.json"

def clean_word(word):
    """Clean a word for use."""
    word = word.strip().lower()
    word = re.sub(r'[^a-z]', '', word)
    return word

def is_valid_word(word):
    """Check if word is valid."""
    if not word or len(word) < 2 or len(word) > 20:
        return False
    if not word.isalpha():
        return False
    return True

def extract_pdf_text(pdf_path):
    """Extract all text from PDF using PyPDF2."""
    print(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    print(f"Total pages: {len(reader.pages)}")
    
    all_text = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            all_text += text + "\n"
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1} pages...")
    
    return all_text

def parse_synonyms(text):
    """Parse the extracted text and find synonyms."""
    text = re.sub(r'\s+', ' ', text)
    
    word_synonyms = {}
    
    pattern = r'([A-Z][a-z]+(?:ness|ment|tion|ity|ous|ive|ful|less|able|ing|ed|er|ly|ure|ance|ence)?)\s*\.\s*S[TY]N\s*\.?\s*([^A]*?)(?:ANT\s*\.|[A-Z][a-z]{2,}\.?\s*S[TY]N|$)'
    
    matches = re.findall(pattern, text)
    print(f"Found {len(matches)} synonym entries")
    
    for word, synonyms_text in matches:
        word = clean_word(word)
        if not is_valid_word(word):
            continue
        
        synonyms = []
        for syn in re.split(r'[,;.]+', synonyms_text):
            syn = clean_word(syn)
            if is_valid_word(syn) and syn != word:
                synonyms.append(syn)
        
        if synonyms:
            if word not in word_synonyms:
                word_synonyms[word] = set()
            word_synonyms[word].update(synonyms)
    
    word_synonyms = {k: list(v) for k, v in word_synonyms.items()}
    return word_synonyms

def load_emotions():
    """Load current emotion lexicon."""
    with open(EMOTIONS_FILE, 'r') as f:
        return json.load(f)

def expand_emotions_with_synonyms(emotions, synonyms):
    """Expand emotions using synonyms."""
    word_to_emotions = {}
    for emotion, words in emotions.items():
        for word in words:
            word_lower = word.lower()
            if word_lower not in word_to_emotions:
                word_to_emotions[word_lower] = set()
            word_to_emotions[word_lower].add(emotion)
    
    expanded = {emotion: set(words) for emotion, words in emotions.items()}
    
    new_words_added = 0
    
    for word, word_emotions in word_to_emotions.items():
        if word in synonyms:
            for syn in synonyms[word]:
                for emotion in word_emotions:
                    if syn not in expanded[emotion]:
                        expanded[emotion].add(syn)
                        new_words_added += 1
    
    for syn_word, syn_list in synonyms.items():
        for syn in syn_list:
            if syn in word_to_emotions:
                for emotion in word_to_emotions[syn]:
                    if syn_word not in expanded[emotion]:
                        expanded[emotion].add(syn_word)
                        new_words_added += 1
    
    print(f"Added {new_words_added} new word-emotion associations via synonyms")
    
    return {emotion: sorted(list(words)) for emotion, words in expanded.items()}

def main():
    print("Extracting synonyms from Complete Dictionary...")
    print("=" * 60)
    
    text = extract_pdf_text(PDF_PATH)
    print(f"\nExtracted {len(text)} characters of text")
    
    synonyms = parse_synonyms(text)
    
    print(f"\nExtracted synonyms for {len(synonyms)} words")
    total_synonyms = sum(len(s) for s in synonyms.values())
    print(f"Total synonym relationships: {total_synonyms}")
    
    if synonyms:
        print("\nSample entries:")
        for word in list(synonyms.keys())[:15]:
            syns = synonyms[word][:8]
            print(f"  {word}: {', '.join(syns)}")
    
    with open('data/synonyms.json', 'w') as f:
        json.dump(synonyms, f, indent=2)
    print(f"\nSaved synonyms to data/synonyms.json")
    
    print("\n" + "=" * 60)
    print("Expanding emotion lexicon with synonyms...")
    
    emotions = load_emotions()
    before_count = sum(len(words) for words in emotions.values())
    print(f"Emotions before: {before_count} word-emotion pairs")
    
    expanded = expand_emotions_with_synonyms(emotions, synonyms)
    after_count = sum(len(words) for words in expanded.values())
    print(f"Emotions after: {after_count} word-emotion pairs")
    
    with open(EMOTIONS_FILE, 'w') as f:
        json.dump(expanded, f, indent=2)
    print(f"\nSaved expanded emotions to {EMOTIONS_FILE}")
    
    print("\nFinal emotion distribution:")
    for emotion in sorted(expanded.keys()):
        print(f"  {emotion}: {len(expanded[emotion])} words")

if __name__ == "__main__":
    main()
