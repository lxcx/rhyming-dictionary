"""
Expand the emotion lexicon by extracting common words from CMU dictionary
and preparing them for emotion classification.
"""
import json
import pronouncing

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

def get_common_words():
    """Get all words from CMU dictionary that are likely common English words."""
    pronouncing.init_cmu()
    all_entries = pronouncing.pronunciations
    
    common_words = set()
    
    for entry in all_entries:
        word = entry[0]
        word_lower = word.lower()
        
        if not word_lower.replace("'", "").replace("-", "").isalpha():
            continue
        if len(word_lower) < 3:
            continue
        if len(word_lower) > 15:
            continue
        if '(' in word:
            continue
        if word_lower.startswith("'"):
            continue
            
        common_words.add(word_lower)
    
    return sorted(common_words)

def load_existing_emotions():
    """Load the existing emotion lexicon."""
    with open('data/emotions.json', 'r') as f:
        data = json.load(f)
    
    tagged_words = set()
    for emotion, words in data.items():
        for word in words:
            tagged_words.add(word.lower())
    
    return tagged_words

def main():
    print("Loading CMU dictionary words...")
    all_words = get_common_words()
    print(f"Total words in CMU dictionary: {len(all_words)}")
    
    print("\nLoading existing emotion lexicon...")
    tagged_words = load_existing_emotions()
    print(f"Words already tagged: {len(tagged_words)}")
    
    untagged = [w for w in all_words if w not in tagged_words]
    print(f"Words needing emotion tags: {len(untagged)}")
    
    word_freq_score = {}
    short_common_patterns = ['ing', 'tion', 'ness', 'ment', 'able', 'ful', 'less', 
                              'ous', 'ive', 'ly', 'er', 'ed', 'es']
    
    for word in untagged:
        score = 0
        if 4 <= len(word) <= 8:
            score += 2
        elif len(word) <= 10:
            score += 1
        
        for pattern in short_common_patterns:
            if word.endswith(pattern):
                score += 1
                break
        
        word_freq_score[word] = score
    
    priority_words = sorted(untagged, key=lambda w: -word_freq_score[w])
    
    print(f"\nSample of high-priority words to tag (first 200):")
    for word in priority_words[:200]:
        print(f"  {word}")
    
    output = {
        "total_cmu_words": len(all_words),
        "already_tagged": len(tagged_words),
        "needing_tags": len(untagged),
        "priority_words": priority_words[:5000],
        "all_untagged": untagged
    }
    
    with open('data/words_to_tag.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved {len(priority_words[:5000])} priority words to data/words_to_tag.json")
    print("You can use this list to batch-classify words with emotions.")

if __name__ == "__main__":
    main()
