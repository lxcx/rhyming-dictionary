"""
Emotion Tagging Script using Claude API
========================================
This script sends untagged words to Claude for emotion classification
based on Plutchik's Wheel of Emotions.

Run with: python tag_emotions_with_claude.py
"""

import json
import os
import time
import sys

try:
    import anthropic
except ImportError:
    print("Error: The 'anthropic' package is not installed.")
    print("Please run: pip install anthropic")
    sys.exit(1)

# Configuration
BATCH_SIZE = 100  # Words per API call (to stay within token limits)
SAVE_INTERVAL = 5  # Save progress every N batches
OUTPUT_FILE = "data/emotions_expanded.json"
PROGRESS_FILE = "data/tagging_progress.json"

# Plutchik's 8 primary emotions
EMOTIONS = ["joy", "sadness", "trust", "disgust", "fear", "anger", "surprise", "anticipation"]

def load_current_emotions():
    """Load the existing emotion lexicon."""
    with open("data/emotions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_cmu_words():
    """Load all words from CMU dictionary."""
    words = set()
    with open("data/cmudict.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";;;"):
                continue
            parts = line.split(None, 1)
            if parts:
                word = parts[0].lower()
                # Remove variant markers like (1), (2)
                import re
                word = re.sub(r'\(\d+\)$', '', word)
                # Only include words that are alphabetic and reasonable length
                if word.isalpha() and 2 <= len(word) <= 15:
                    words.add(word)
    return words

def get_untagged_words(cmu_words, emotion_data):
    """Find words in CMU dict that aren't tagged with any emotion."""
    tagged_words = set()
    for emotion, words in emotion_data.items():
        for word in words:
            tagged_words.add(word.lower())
    
    return sorted(cmu_words - tagged_words)

def load_progress():
    """Load progress from previous run if it exists."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_count": 0, "results": {}}

def save_progress(progress):
    """Save current progress."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

def save_results(emotion_data, new_tags):
    """Merge new tags into emotion data and save."""
    # Merge new tags
    for word, emotions in new_tags.items():
        for emotion in emotions:
            if emotion in emotion_data:
                if word not in emotion_data[emotion]:
                    emotion_data[emotion].append(word)
    
    # Save expanded lexicon
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(emotion_data, f, indent=2)
    
    print(f"Saved expanded lexicon to {OUTPUT_FILE}")

def tag_words_with_claude(client, words):
    """Send a batch of words to Claude for emotion tagging."""
    
    words_list = "\n".join(words)
    
    prompt = f"""You are an expert at classifying words according to Plutchik's Wheel of Emotions.

For each word below, determine which of the 8 primary emotions it is associated with:
- joy (happiness, pleasure, delight)
- sadness (grief, sorrow, melancholy)  
- trust (acceptance, admiration, confidence)
- disgust (revulsion, contempt, loathing)
- fear (anxiety, terror, worry)
- anger (rage, irritation, hostility)
- surprise (amazement, astonishment, shock)
- anticipation (expectation, interest, vigilance)

Rules:
1. A word can have MULTIPLE emotions (e.g., "exciting" = joy + anticipation)
2. A word can have ZERO emotions if it's purely neutral (e.g., "table", "the")
3. Consider the word's PRIMARY/most common usage
4. Be conservative - only tag emotions that clearly apply

Respond in JSON format like this:
{{"word1": ["emotion1", "emotion2"], "word2": [], "word3": ["emotion1"]}}

Words to classify:
{words_list}

Respond ONLY with the JSON object, no other text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse JSON response
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        results = json.loads(response_text)
        
        # Validate emotions
        validated = {}
        for word, emotions in results.items():
            valid_emotions = [e for e in emotions if e in EMOTIONS]
            if valid_emotions:
                validated[word.lower()] = valid_emotions
        
        return validated
        
    except json.JSONDecodeError as e:
        print(f"  Warning: Failed to parse JSON response: {e}")
        print(f"  Response was: {response_text[:200]}...")
        return {}
    except Exception as e:
        print(f"  Error calling Claude API: {e}")
        return {}

def main():
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("=" * 60)
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("=" * 60)
        print("\nTo fix this:")
        print("1. Go to https://console.anthropic.com/")
        print("2. Create an API key")
        print("3. Set the environment variable:")
        print("\n   Windows (PowerShell):")
        print('   $env:ANTHROPIC_API_KEY = "your-api-key-here"')
        print("\n   Windows (Command Prompt):")
        print('   set ANTHROPIC_API_KEY=your-api-key-here')
        print("\n   Mac/Linux:")
        print('   export ANTHROPIC_API_KEY="your-api-key-here"')
        print("\n4. Run this script again")
        sys.exit(1)
    
    print("=" * 60)
    print("Emotion Tagging Script")
    print("=" * 60)
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Load data
    print("\nLoading data...")
    emotion_data = load_current_emotions()
    cmu_words = load_cmu_words()
    untagged = get_untagged_words(cmu_words, emotion_data)
    
    print(f"  Total words in CMU dictionary: {len(cmu_words):,}")
    print(f"  Currently tagged words: {sum(len(w) for w in emotion_data.values()):,}")
    print(f"  Words to process: {len(untagged):,}")
    
    if len(untagged) == 0:
        print("\nAll words are already tagged!")
        return
    
    # Load progress
    progress = load_progress()
    start_index = progress["processed_count"]
    all_results = progress["results"]
    
    if start_index > 0:
        print(f"\nResuming from word {start_index:,} (previously tagged {len(all_results):,} words)")
    
    # Calculate batches
    remaining = untagged[start_index:]
    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Estimate cost (rough estimate: ~0.003 per 1000 input tokens, ~0.015 per 1000 output tokens)
    # Each batch is roughly 500-1000 tokens in, 500-2000 tokens out
    estimated_cost = total_batches * 0.02  # ~$0.02 per batch
    
    print(f"\n  Batches remaining: {total_batches:,}")
    print(f"  Estimated cost: ~${estimated_cost:.2f}")
    print(f"  Estimated time: ~{total_batches * 3 / 60:.1f} minutes")
    
    # Confirm
    print("\n" + "=" * 60)
    response = input("Continue? (y/n): ").strip().lower()
    if response != "y":
        print("Aborted.")
        return
    
    print("\nStarting emotion tagging...")
    print("(Press Ctrl+C to stop - progress will be saved)\n")
    
    try:
        for i in range(0, len(remaining), BATCH_SIZE):
            batch_num = (start_index + i) // BATCH_SIZE + 1
            batch = remaining[i:i + BATCH_SIZE]
            
            print(f"Batch {batch_num}/{(start_index // BATCH_SIZE) + total_batches}: Processing {len(batch)} words...")
            
            results = tag_words_with_claude(client, batch)
            all_results.update(results)
            
            tagged_count = len(results)
            print(f"  Tagged {tagged_count} words with emotions")
            
            # Update progress
            progress["processed_count"] = start_index + i + len(batch)
            progress["results"] = all_results
            
            # Save periodically
            if (batch_num % SAVE_INTERVAL == 0) or (i + BATCH_SIZE >= len(remaining)):
                save_progress(progress)
                save_results(emotion_data.copy(), all_results)
                print(f"  Progress saved ({progress['processed_count']:,} words processed, {len(all_results):,} tagged)")
            
            # Rate limiting - wait between batches
            if i + BATCH_SIZE < len(remaining):
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted! Saving progress...")
        save_progress(progress)
        save_results(emotion_data.copy(), all_results)
        print(f"Progress saved. Run the script again to resume.")
        return
    
    # Final save
    save_results(emotion_data, all_results)
    
    # Clean up progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"\nTotal words processed: {len(untagged):,}")
    print(f"Words tagged with emotions: {len(all_results):,}")
    print(f"\nExpanded lexicon saved to: {OUTPUT_FILE}")
    print("\nTo use the new lexicon, rename it to emotions.json:")
    print(f"  copy {OUTPUT_FILE} data\\emotions.json")

if __name__ == "__main__":
    main()
