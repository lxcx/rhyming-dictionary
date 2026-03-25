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
const randomBtn = document.getElementById('random-btn');
const resultsContainer = document.getElementById('results');
const resultsCount = document.getElementById('results-count');
const wordInfo = document.getElementById('word-info');
const clearEmotionsBtn = document.getElementById('clear-emotions');

// Modal elements
const modal = document.getElementById('word-modal');
const modalWord = document.getElementById('modal-word');
const modalInfo = document.getElementById('modal-info');
const modalClose = document.querySelector('.modal-close');
const modalSearchBtn = document.getElementById('modal-search');
const linkDictionary = document.getElementById('link-dictionary');
const linkThesaurus = document.getElementById('link-thesaurus');
const linkWiktionary = document.getElementById('link-wiktionary');
const linkRhymezone = document.getElementById('link-rhymezone');

let currentWord = '';
let currentModalWord = '';

function init() {
    searchBtn.addEventListener('click', performSearch);
    wordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    randomBtn.addEventListener('click', getRandomWord);

    // Syllable filter chips
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            chip.querySelector('input').checked = true;
            if (currentWord) performSearch();
        });
    });

    // Emotion filter chips
    document.querySelectorAll('.emotion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const input = chip.querySelector('input');
            chip.classList.toggle('active');
            input.checked = chip.classList.contains('active');
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

    // Modal event listeners
    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    modalSearchBtn.addEventListener('click', () => {
        wordInput.value = currentModalWord;
        closeModal();
        performSearch();
    });

    // Keyboard shortcut to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

function getSelectedFilters() {
    const syllables = document.querySelector('input[name="syllables"]:checked').value;
    const emotions = Array.from(document.querySelectorAll('.emotion-chip.active'))
        .map(chip => chip.dataset.emotion);
    return { syllables, emotions };
}

async function performSearch() {
    const word = wordInput.value.trim();
    if (!word) return;

    currentWord = word;
    showLoading();

    const { syllables, emotions } = getSelectedFilters();

    try {
        const infoResponse = await fetch(`/api/word-info?word=${encodeURIComponent(word)}`);
        const infoData = await infoResponse.json();
        showWordInfo(infoData);

        let url = `/api/rhymes?word=${encodeURIComponent(word)}&syllables=${syllables}`;
        emotions.forEach(e => url += `&emotions=${encodeURIComponent(e)}`);

        const response = await fetch(url);
        const data = await response.json();

        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = '<p class="no-results">Error fetching rhymes. Please try again.</p>';
    }
}

async function getRandomWord() {
    const { syllables, emotions } = getSelectedFilters();
    
    let url = `/api/random?syllables=${syllables}`;
    emotions.forEach(e => url += `&emotions=${encodeURIComponent(e)}`);

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        // Show the random word in the modal
        showWordModal(data.word, data.syllables, data.emotions);
    } catch (error) {
        console.error('Error:', error);
        alert('Error getting random word. Please try again.');
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
        const { syllables, emotions } = getSelectedFilters();
        const hasFilters = emotions.length > 0 || syllables !== 'all';
        
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
                 style="border-left-color: ${borderColor}; animation-delay: ${index * 0.03}s;"
                 data-word="${result.word}"
                 data-syllables="${result.syllables}"
                 data-emotions="${emotions.join(',')}">
                <span class="word-text">${result.word}</span>
                <span class="syllable-badge">${result.syllables}</span>
                ${hasEmotions ? `<span class="emotion-dots">${emotionDots}</span>` : ''}
            </div>
        `;
    }).join('');

    // Add click handlers to word chips
    document.querySelectorAll('.word-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const word = chip.dataset.word;
            const syllables = parseInt(chip.dataset.syllables);
            const emotions = chip.dataset.emotions ? chip.dataset.emotions.split(',').filter(e => e) : [];
            showWordModal(word, syllables, emotions);
        });
    });
}

function showWordModal(word, syllables, emotions) {
    currentModalWord = word;
    
    modalWord.textContent = word;
    
    const emotionBadges = emotions.length > 0
        ? emotions.map(e => 
            `<span style="color: ${EMOTION_COLORS[e]}; font-weight: 600;">${e}</span>`
          ).join(', ')
        : '<span style="color: #a0a0a0;">no emotion tags</span>';
    
    modalInfo.innerHTML = `${syllables} syllable${syllables !== 1 ? 's' : ''} — ${emotionBadges}`;
    
    // Set external link URLs
    linkDictionary.href = `https://www.dictionary.com/browse/${encodeURIComponent(word)}`;
    linkThesaurus.href = `https://www.thesaurus.com/browse/${encodeURIComponent(word)}`;
    linkWiktionary.href = `https://en.wiktionary.org/wiki/${encodeURIComponent(word)}`;
    linkRhymezone.href = `https://www.rhymezone.com/r/rhyme.cgi?Word=${encodeURIComponent(word)}`;
    
    modal.classList.remove('hidden');
}

function closeModal() {
    modal.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', init);
