"""
Integrate NRC Emotion Lexicon with our existing emotions.json
"""
import json

NRC_FILE = "data/nrc/NRC-Emotion-Lexicon/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"
EXISTING_FILE = "data/emotions.json"
OUTPUT_FILE = "data/emotions.json"

PLUTCHIK_EMOTIONS = ["anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust"]

def parse_nrc_lexicon():
    """Parse NRC lexicon and extract word-emotion associations."""
    word_emotions = {}
    
    with open(NRC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 3:
                continue
            
            word, emotion, association = parts
            word = word.lower()
            
            if emotion not in PLUTCHIK_EMOTIONS:
                continue
            
            if association == '1':
                if word not in word_emotions:
                    word_emotions[word] = set()
                word_emotions[word].add(emotion)
    
    return word_emotions

def load_existing_emotions():
    """Load existing emotion lexicon."""
    with open(EXISTING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_lexicons(existing, nrc_words):
    """Merge NRC lexicon with existing lexicon."""
    merged = {emotion: set(words) for emotion, words in existing.items()}
    
    for word, emotions in nrc_words.items():
        for emotion in emotions:
            if emotion in merged:
                merged[emotion].add(word)
    
    return {emotion: sorted(list(words)) for emotion, words in merged.items()}

def main():
    print("Parsing NRC Emotion Lexicon...")
    nrc_words = parse_nrc_lexicon()
    
    nrc_word_count = len(nrc_words)
    total_associations = sum(len(e) for e in nrc_words.values())
    print(f"Found {nrc_word_count} words with {total_associations} emotion associations")
    
    print("\nNRC emotion distribution:")
    emotion_counts = {e: 0 for e in PLUTCHIK_EMOTIONS}
    for word, emotions in nrc_words.items():
        for e in emotions:
            emotion_counts[e] += 1
    
    for emotion, count in sorted(emotion_counts.items()):
        print(f"  {emotion}: {count} words")
    
    print("\nLoading existing lexicon...")
    existing = load_existing_emotions()
    existing_count = sum(len(words) for words in existing.values())
    print(f"Existing lexicon: {existing_count} word-emotion pairs")
    
    print("\nMerging lexicons...")
    merged = merge_lexicons(existing, nrc_words)
    
    merged_count = sum(len(words) for words in merged.values())
    print(f"Merged lexicon: {merged_count} word-emotion pairs")
    
    print("\nFinal emotion distribution:")
    for emotion in PLUTCHIK_EMOTIONS:
        print(f"  {emotion}: {len(merged[emotion])} words")
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)
    
    print("Done!")
    
    print("\nSample words for each emotion:")
    for emotion in PLUTCHIK_EMOTIONS:
        sample = merged[emotion][:10]
        print(f"  {emotion}: {', '.join(sample)}")

if __name__ == "__main__":
    main()
