import json
import os
import re
from flask import Flask, render_template, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

app = Flask(__name__,
            template_folder=os.path.join(PROJECT_DIR, 'templates'),
            static_folder=os.path.join(PROJECT_DIR, 'static'))

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

# Global data stores
pronunciations = {}
rhyme_index = {}
emotion_words = {}
word_to_emotions = {}

def load_cmu_dict():
    """Load the CMU pronouncing dictionary."""
    global pronunciations, rhyme_index
    
    dict_path = os.path.join(PROJECT_DIR, 'data', 'cmudict.txt')
    
    with open(dict_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';;;'):
                continue
            
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            
            word = parts[0].lower()
            # Remove variant markers like (1), (2)
            word = re.sub(r'\(\d+\)$', '', word)
            phones = parts[1]
            
            if word not in pronunciations:
                pronunciations[word] = []
            pronunciations[word].append(phones)
            
            # Build rhyme index based on last stressed vowel to end
            rhyme_part = get_rhyme_part(phones)
            if rhyme_part:
                if rhyme_part not in rhyme_index:
                    rhyme_index[rhyme_part] = set()
                rhyme_index[rhyme_part].add(word)

def get_rhyme_part(phones):
    """Extract the rhyming part (last stressed vowel to end)."""
    phone_list = phones.split()
    
    # Find last stressed vowel (marked with 1 or 2)
    last_stressed = -1
    for i, phone in enumerate(phone_list):
        if any(c.isdigit() and c in '12' for c in phone):
            last_stressed = i
    
    if last_stressed == -1:
        # No stressed vowel, use last vowel
        for i, phone in enumerate(phone_list):
            if any(c.isdigit() for c in phone):
                last_stressed = i
    
    if last_stressed == -1:
        return None
    
    # Return phones from stressed vowel to end
    return ' '.join(phone_list[last_stressed:])

def get_syllable_count(word):
    """Count syllables based on vowel sounds in pronunciation."""
    word = word.lower()
    
    if word in pronunciations:
        phones = pronunciations[word][0]
        # Count phones with digits (vowels have stress markers)
        return sum(1 for phone in phones.split() if any(c.isdigit() for c in phone))
    
    # Fallback: estimate from spelling
    vowels = "aeiouy"
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

def get_rhymes(word):
    """Get rhyming words for the given word."""
    word = word.lower().strip()
    
    if word not in pronunciations:
        return []
    
    rhymes = set()
    for phones in pronunciations[word]:
        rhyme_part = get_rhyme_part(phones)
        if rhyme_part and rhyme_part in rhyme_index:
            rhymes.update(rhyme_index[rhyme_part])
    
    # Remove the word itself
    rhymes.discard(word)
    
    return sorted(list(rhymes))

def load_emotion_data():
    """Load emotion lexicon from JSON file."""
    global emotion_words, word_to_emotions
    
    data_path = os.path.join(PROJECT_DIR, 'data', 'emotions.json')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        emotion_words = json.load(f)
    
    for emotion, words in emotion_words.items():
        for word in words:
            word_lower = word.lower()
            if word_lower not in word_to_emotions:
                word_to_emotions[word_lower] = []
            word_to_emotions[word_lower].append(emotion)

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

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "words_loaded": len(pronunciations),
        "emotions_loaded": len(word_to_emotions)
    })

# Initialize data on module load
try:
    load_cmu_dict()
    load_emotion_data()
except Exception as e:
    print(f"Error loading data: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
