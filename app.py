import json
import os
from flask import Flask, render_template, jsonify, request
import pronouncing

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

EMOTION_COLORS = {
    "joy": "#FFEB3B",
    "trust": "#8BC34A", 
    "fear": "#4CAF50",
    "surprise": "#00BCD4",
    "sadness": "#2196F3",
    "disgust": "#9C27B0",
    "anger": "#F44336",
    "anticipation": "#FF9800"
}

emotion_words = {}
word_to_emotions = {}

def load_emotion_data():
    """Load emotion lexicon from JSON file."""
    global emotion_words, word_to_emotions
    
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'emotions.json')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        emotion_words = json.load(f)
    
    for emotion, words in emotion_words.items():
        for word in words:
            word_lower = word.lower()
            if word_lower not in word_to_emotions:
                word_to_emotions[word_lower] = []
            word_to_emotions[word_lower].append(emotion)
    
    print(f"Loaded {len(word_to_emotions)} emotion-tagged words")

def get_syllable_count(word):
    """Get the number of syllables in a word using CMU dictionary."""
    pronunciations = pronouncing.phones_for_word(word.lower())
    if pronunciations:
        return pronouncing.syllable_count(pronunciations[0])
    
    vowels = "aeiouy"
    word = word.lower()
    count = 0
    prev_is_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    
    if word.endswith('e') and count > 1:
        count -= 1
    
    return max(1, count)

def normalize_reduced_vowels(phones):
    """Normalize reduced/unstressed vowels that sound similar.
    In unstressed positions, AH0, IH0, and AX0 are nearly indistinguishable."""
    reduced_vowels = {'AH0', 'IH0', 'AX0', 'IX0'}
    return ' '.join('AH0' if p in reduced_vowels else p for p in phones.split())

def get_rhyming_part(phones):
    """Extract the rhyming part (from last stressed vowel to end) and normalize it."""
    phone_list = phones.split()
    # Find the last stressed vowel (ends with 1 or 2)
    last_stress_idx = -1
    for i, phone in enumerate(phone_list):
        if phone[-1] in '12':
            last_stress_idx = i
    
    if last_stress_idx == -1:
        # No stress found, use whole pronunciation
        rhyme_part = phones
    else:
        rhyme_part = ' '.join(phone_list[last_stress_idx:])
    
    return normalize_reduced_vowels(rhyme_part)

# Build rhyme lookup table at startup for fast flexible matching
rhyme_lookup = {}

def build_rhyme_lookup():
    """Build a lookup table mapping normalized rhyme endings to words."""
    global rhyme_lookup
    print("Building flexible rhyme lookup table...")
    
    all_words = pronouncing.search('.*')
    for word in all_words:
        phones = pronouncing.phones_for_word(word)
        if phones:
            rhyme_part = get_rhyming_part(phones[0])
            if rhyme_part not in rhyme_lookup:
                rhyme_lookup[rhyme_part] = []
            rhyme_lookup[rhyme_part].append(word)
    
    print(f"Built rhyme lookup with {len(rhyme_lookup)} unique rhyme patterns")

def get_rhymes(word):
    """Get rhyming words for the given word with improved matching.
    Uses flexible matching for reduced vowels in unstressed syllables."""
    word = word.lower().strip()
    
    # Get pronunciation for target word
    pronunciations = pronouncing.phones_for_word(word)
    if not pronunciations:
        # Fall back to standard if word not in dictionary
        return pronouncing.rhymes(word)
    
    # Get normalized rhyming part
    target_rhyme = get_rhyming_part(pronunciations[0])
    
    # Look up all words with matching normalized rhyme
    matches = rhyme_lookup.get(target_rhyme, [])
    
    # Remove the input word itself
    return [w for w in matches if w != word]

def get_word_emotions(word):
    """Get the emotions associated with a word."""
    return word_to_emotions.get(word.lower(), [])

def filter_rhymes(rhymes, syllable_filter=None, emotion_filter=None):
    """Filter rhymes by syllable count and/or emotion."""
    results = []
    
    for word in rhymes:
        syllables = get_syllable_count(word)
        emotions = get_word_emotions(word)
        
        if syllable_filter and syllable_filter != "all":
            if syllable_filter == "4+":
                if syllables < 4:
                    continue
            elif syllables != int(syllable_filter):
                continue
        
        if emotion_filter and len(emotion_filter) > 0:
            if not any(e in emotions for e in emotion_filter):
                continue
        
        results.append({
            "word": word,
            "syllables": syllables,
            "emotions": emotions
        })
    
    results.sort(key=lambda x: (x["syllables"], x["word"]))
    
    return results

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', colors=EMOTION_COLORS)

@app.route('/api/rhymes')
def api_rhymes():
    """API endpoint to get rhymes with optional filtering."""
    word = request.args.get('word', '').strip()
    syllables = request.args.get('syllables', 'all')
    emotions = request.args.getlist('emotions')
    
    if not word:
        return jsonify({"error": "Please provide a word", "results": []})
    
    rhymes = get_rhymes(word)
    
    if not rhymes:
        return jsonify({
            "word": word,
            "message": f"No rhymes found for '{word}'",
            "results": []
        })
    
    filtered = filter_rhymes(rhymes, syllables, emotions if emotions else None)
    
    return jsonify({
        "word": word,
        "total_rhymes": len(rhymes),
        "filtered_count": len(filtered),
        "results": filtered
    })

@app.route('/api/word-info')
def api_word_info():
    """Get information about a specific word."""
    word = request.args.get('word', '').strip()
    
    if not word:
        return jsonify({"error": "Please provide a word"})
    
    return jsonify({
        "word": word,
        "syllables": get_syllable_count(word),
        "emotions": get_word_emotions(word)
    })

@app.route('/api/emotions')
def api_emotions():
    """Get the list of emotions and their colors."""
    return jsonify(EMOTION_COLORS)

try:
    load_emotion_data()
    build_rhyme_lookup()
except Exception as e:
    print(f"Error loading data: {e}")

@app.route('/health')
def health():
    """Health check endpoint for debugging."""
    import sys
    return jsonify({
        "status": "ok",
        "emotion_words_loaded": len(word_to_emotions),
        "base_dir": BASE_DIR,
        "python_version": sys.version,
        "data_path_exists": os.path.exists(os.path.join(BASE_DIR, 'data', 'emotions.json')),
        "templates_path_exists": os.path.exists(os.path.join(BASE_DIR, 'templates'))
    })

@app.route('/test')
def test():
    """Simple test endpoint."""
    return "Hello from Flask!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
