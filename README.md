# Rhyming Dictionary with Emotion & Syllable Filters

A web-based rhyming dictionary that lets you filter rhymes by:
- **Syllable count** (1, 2, 3, 4+ syllables)
- **Emotion** (based on Plutchik's Wheel of Emotions)

## Features

- Find rhymes for any English word
- Filter by syllable count
- Filter by 8 emotion categories (color-coded):
  - Joy (Yellow)
  - Trust (Green)
  - Fear (Dark Green)
  - Surprise (Cyan)
  - Sadness (Blue)
  - Disgust (Purple)
  - Anger (Red)
  - Anticipation (Orange)
- Beautiful dark-themed UI with color-coded results

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python app.py
   ```

3. Open your browser to: http://localhost:5000

## How It Works

- **Rhyming**: Uses the CMU Pronouncing Dictionary (via the `pronouncing` library) to find words that rhyme based on phonetic endings
- **Syllable Counting**: Uses phonetic data from CMU dict, with a fallback algorithm for unknown words
- **Emotion Tagging**: Uses a curated emotion lexicon based on Plutchik's 8 primary emotions

## API Endpoints

- `GET /api/rhymes?word=<word>&syllables=<1|2|3|4+|all>&emotions=<emotion>` - Find rhymes with optional filters
- `GET /api/word-info?word=<word>` - Get syllable count and emotions for a word
- `GET /api/emotions` - Get list of emotions and their colors

## Expanding the Emotion Lexicon

To add more emotion-tagged words, edit `data/emotions.json`. Each emotion key contains an array of words associated with that emotion.
