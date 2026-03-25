# How to Tag Words with Emotions Using Claude API

This guide will walk you through using your Claude API subscription to automatically tag ~116,000 words with emotions from Plutchik's Wheel.

## Overview

- **What it does**: Sends batches of untagged words to Claude, which classifies them by emotion
- **Time required**: ~2-3 hours (can be paused and resumed)
- **Estimated cost**: ~$10-20 depending on the model used
- **Result**: An expanded `emotions.json` with many more tagged words

---

## Step 1: Get Your Anthropic API Key

1. Go to the Anthropic Console: **https://console.anthropic.com/**

2. Sign in with your account (the one you pay for Claude with)

3. Click on **"API Keys"** in the left sidebar

4. Click **"Create Key"**

5. Give it a name like "emotion-tagging" and click **Create**

6. **IMPORTANT**: Copy the key immediately! It looks like:
   ```
   sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   You won't be able to see it again after closing the dialog.

---

## Step 2: Install Python (if you don't have it)

### Check if Python is installed:
Open PowerShell and type:
```powershell
python --version
```

If you see a version number (like `Python 3.11.0`), skip to Step 3.

### If Python is not installed:

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow "Download Python" button
3. Run the installer
4. **IMPORTANT**: Check the box that says **"Add Python to PATH"** at the bottom!
5. Click "Install Now"
6. Close and reopen PowerShell

---

## Step 3: Install the Anthropic Package

Open PowerShell and run:
```powershell
pip install anthropic
```

You should see output showing the package being downloaded and installed.

---

## Step 4: Set Your API Key

In the **same PowerShell window**, set your API key as an environment variable.

**Replace `your-api-key-here` with your actual API key:**

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-your-actual-key-here"
```

> **Note**: This only lasts for the current PowerShell session. If you close the window, you'll need to set it again.

---

## Step 5: Navigate to the Project Folder

```powershell
cd C:\Users\chris\rhyming-dictionary
```

---

## Step 6: Run the Tagging Script

```powershell
python tag_emotions_with_claude.py
```

### What you'll see:

```
============================================================
Emotion Tagging Script
============================================================

Loading data...
  Total words in CMU dictionary: 126,052
  Currently tagged words: 10,557
  Words to process: 115,495

  Batches remaining: 1,155
  Estimated cost: ~$23.10
  Estimated time: ~57.8 minutes

============================================================
Continue? (y/n):
```

Type `y` and press Enter to start.

---

## Step 7: Wait (or Pause and Resume)

The script will process words in batches of 100:

```
Batch 1/1155: Processing 100 words...
  Tagged 45 words with emotions
Batch 2/1155: Processing 100 words...
  Tagged 52 words with emotions
...
```

### To pause:
Press **Ctrl+C** at any time. Your progress is saved automatically.

### To resume:
Just run the script again:
```powershell
python tag_emotions_with_claude.py
```
It will pick up where you left off.

---

## Step 8: Use the New Emotion Data

When the script finishes, it creates a file called `data/emotions_expanded.json`.

To use it in your rhyming dictionary:

1. **Backup the old file** (just in case):
   ```powershell
   copy data\emotions.json data\emotions_backup.json
   ```

2. **Replace with the new file**:
   ```powershell
   copy data\emotions_expanded.json data\emotions.json
   ```

3. **Deploy to Vercel**:
   ```powershell
   vercel --prod --yes
   ```

---

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"
You need to set the API key. Run this in PowerShell (with your actual key):
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"
```

### "pip is not recognized"
Python wasn't added to PATH. Reinstall Python and make sure to check "Add Python to PATH".

### "anthropic module not found"
Run: `pip install anthropic`

### Script seems stuck
The API has rate limits. If you're sending too many requests, it may slow down. The script waits 1 second between batches automatically.

### I closed PowerShell and lost my API key
That's normal - environment variables don't persist. Just set it again before running the script.

---

## Cost Breakdown

The script uses Claude claude-sonnet-4-20250514 by default:
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

For ~116,000 words in batches of 100:
- ~1,155 API calls
- ~$0.01-0.02 per call
- **Total estimate: $10-25**

You can monitor your usage at: https://console.anthropic.com/usage

---

## Questions?

If something isn't working, the error messages should tell you what's wrong. Common issues:
- API key not set or invalid
- Python not installed
- anthropic package not installed
- Not in the correct directory
