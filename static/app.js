const EMOTION_COLORS = {
    joy: '#FFEB3B',
    trust: '#8BC34A',
    fear: '#4CAF50',
    surprise: '#00BCD4',
    sadness: '#2196F3',
    disgust: '#9C27B0',
    anger: '#F44336',
    anticipation: '#FF9800'
};

const wordInput = document.getElementById('word-input');
const searchBtn = document.getElementById('search-btn');
const resultsContainer = document.getElementById('results');
const resultsCount = document.getElementById('results-count');
const wordInfo = document.getElementById('word-info');
const clearEmotionsBtn = document.getElementById('clear-emotions');

let currentWord = '';

function init() {
    searchBtn.addEventListener('click', performSearch);
    wordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            chip.querySelector('input').checked = true;
            if (currentWord) performSearch();
        });
    });

    document.querySelectorAll('.emotion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');
            chip.querySelector('input').checked = chip.classList.contains('active');
            if (currentWord) performSearch();
        });
    });

    clearEmotionsBtn.addEventListener('click', () => {
        document.querySelectorAll('.emotion-chip').forEach(chip => {
            chip.classList.remove('active');
            chip.querySelector('input').checked = false;
        });
        if (currentWord) performSearch();
    });
}

async function performSearch() {
    const word = wordInput.value.trim();
    if (!word) return;

    currentWord = word;
    showLoading();

    const syllables = document.querySelector('input[name="syllables"]:checked').value;
    const emotions = Array.from(document.querySelectorAll('input[name="emotions"]:checked'))
        .map(input => input.value);

    try {
        const infoResponse = await fetch(`/api/word-info?word=${encodeURIComponent(word)}`);
        const infoData = await infoResponse.json();
        showWordInfo(infoData);

        let url = `/api/rhymes?word=${encodeURIComponent(word)}&syllables=${syllables}`;
        emotions.forEach(e => url += `&emotions=${e}`);

        const response = await fetch(url);
        const data = await response.json();

        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = '<p class="no-results">Error fetching rhymes. Please try again.</p>';
    }
}

function showLoading() {
    resultsContainer.innerHTML = '<div class="loading"></div>';
    resultsCount.textContent = '';
}

function showWordInfo(data) {
    if (data.error) {
        wordInfo.classList.add('hidden');
        return;
    }

    const emotionBadges = data.emotions.length > 0
        ? data.emotions.map(e => 
            `<span style="color: ${EMOTION_COLORS[e]}; font-weight: 600;">${e}</span>`
          ).join(', ')
        : '<span style="color: #a0a0a0;">no emotion tags</span>';

    wordInfo.innerHTML = `
        <strong>"${data.word}"</strong> — 
        ${data.syllables} syllable${data.syllables !== 1 ? 's' : ''} — 
        ${emotionBadges}
    `;
    wordInfo.classList.remove('hidden');
}

function displayResults(data) {
    if (data.error) {
        resultsContainer.innerHTML = `<p class="no-results">${data.error}</p>`;
        resultsCount.textContent = '';
        return;
    }

    if (data.results.length === 0) {
        const hasFilters = document.querySelector('.emotion-chip.active') || 
                          document.querySelector('input[name="syllables"]:checked').value !== 'all';
        
        if (hasFilters && data.total_rhymes > 0) {
            resultsContainer.innerHTML = `
                <p class="no-results">
                    No rhymes match your filters.<br>
                    <small>${data.total_rhymes} total rhymes found - try adjusting your filters.</small>
                </p>
            `;
        } else {
            resultsContainer.innerHTML = `<p class="no-results">${data.message || 'No rhymes found.'}</p>`;
        }
        resultsCount.textContent = '';
        return;
    }

    resultsCount.textContent = `Showing ${data.filtered_count} of ${data.total_rhymes} rhymes`;

    resultsContainer.innerHTML = data.results.map((result, index) => {
        const emotions = result.emotions || [];
        const hasEmotions = emotions.length > 0;
        
        const primaryEmotion = emotions[0] || null;
        const borderColor = primaryEmotion ? EMOTION_COLORS[primaryEmotion] : 'transparent';
        
        const emotionDots = emotions.map(e => 
            `<span class="emotion-dot" style="background-color: ${EMOTION_COLORS[e]};" title="${e}"></span>`
        ).join('');

        return `
            <div class="word-chip ${hasEmotions ? 'has-emotions' : ''}" 
                 style="border-left-color: ${borderColor}; animation-delay: ${index * 0.03}s;">
                <span class="word-text">${result.word}</span>
                <span class="syllable-badge">${result.syllables}</span>
                ${hasEmotions ? `<span class="emotion-dots">${emotionDots}</span>` : ''}
            </div>
        `;
    }).join('');
}

document.addEventListener('DOMContentLoaded', init);
