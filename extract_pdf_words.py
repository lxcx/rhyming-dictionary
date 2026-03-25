"""
Extract words from The Complete Rhyming Dictionary PDF.
"""
import re
import json
import pronouncing

def is_page_marker(line):
    """Check if line is a page marker like '-- 132 of 715 --'"""
    return bool(re.match(r'^--\s*\d+\s+of\s+\d+\s*--$', line.strip()))

def is_page_header(line):
    """Check if line is a pronunciation guide header."""
    line_lower = line.strip().lower()
    if 'ale, care, add' in line_lower:
        return True
    if 'old, or, odd' in line_lower or 'old, 6r, odd' in line_lower:
        return True
    if 'use, urn, up' in line_lower or 'use, flrn, up' in line_lower:
        return True
    if 'this, thin' in line_lower:
        return True
    return False

def is_section_header(line):
    """Check if line is a section header."""
    line = line.strip()
    if re.match(r'^\d+\s+[A-Z]+$', line):
        return True
    if re.match(r'^[A-Z]+\s*[-—]\s*[A-Z]+\s*\d+$', line):
        return True
    if re.match(r'^[A-Z]+\s+\d+$', line):
        return True
    if re.match(r'^\d+\s+[A-Z]+\s*[-—]', line):
        return True
    return False

def is_instruction_line(line):
    """Check if line is instructional text, not a word."""
    line = line.strip()
    if line.startswith('(See also'):
        return True
    if line.startswith('add -'):
        return True
    if line.startswith('appropriate'):
        return True
    if 'THE COMPLETE' in line.upper():
        return True
    if 'DICTIONARY' in line.upper() and 'RHYMING' in line.upper():
        return True
    return False

def looks_like_english_word(word):
    """Check if word looks like a plausible English word."""
    if len(word) < 2 or len(word) > 25:
        return False
    
    if not re.match(r"^[a-z][a-z'-]*[a-z]$|^[a-z]{1,2}$", word):
        return False
    
    if '--' in word or "''" in word or "'-" in word or "-'" in word:
        return False
    
    core = word.replace('-', '').replace("'", '')
    
    vowels = set('aeiouy')
    has_vowel = any(c in vowels for c in core)
    if not has_vowel and len(core) > 3:
        return False
    
    consonant_runs = re.findall(r'[^aeiouy]+', core)
    for run in consonant_runs:
        if len(run) > 4:
            return False
        weird = ['xq', 'qx', 'zx', 'xz', 'vq', 'qv', 'jx', 'xj', 'zq', 'qz',
                 'vx', 'xv', 'jq', 'qj', 'wq', 'qw', 'wx', 'xw', 'kq', 'qk',
                 'fq', 'qf', 'pq', 'qp', 'bx', 'xb', 'cx', 'xc', 'dx', 'gx',
                 'hx', 'jj', 'kk', 'qq', 'vv', 'ww', 'xx', 'zz', 'bq', 'cq',
                 'dq', 'fk', 'gq', 'hq', 'jk', 'kj', 'lq', 'mq', 'nq', 'pj',
                 'qb', 'qc', 'qd', 'qe', 'qg', 'qh', 'qi', 'qj', 'ql', 'qm',
                 'qn', 'qo', 'qp', 'qr', 'qs', 'qt', 'qy', 'rq', 'sq', 'tq',
                 'vb', 'vc', 'vd', 'vf', 'vg', 'vh', 'vj', 'vk', 'vl', 'vm',
                 'vn', 'vp', 'vr', 'vs', 'vt', 'vw', 'vz', 'wj', 'wk', 'wv',
                 'wz', 'xd', 'xf', 'xg', 'xh', 'xk', 'xl', 'xm', 'xn', 'xp',
                 'xr', 'xs', 'xt', 'xw', 'xy', 'yq', 'zb', 'zc', 'zd', 'zf',
                 'zg', 'zj', 'zk', 'zm', 'zn', 'zp', 'zr', 'zs', 'zt', 'zv', 'zw']
        for w in weird:
            if w in run:
                return False
    
    if len(core) >= 4:
        vowel_count = sum(1 for c in core if c in vowels)
        if vowel_count == 0:
            return False
        if len(core) > 8 and vowel_count < 2:
            return False
    
    return True

def clean_word(word):
    """Clean a word for use in our dictionary."""
    word = word.strip()
    word = word.rstrip('*')
    word = word.replace('£', 'e').replace('§', 'e').replace('6', 'o')
    word = re.sub(r'[éèêë]', 'e', word)
    word = re.sub(r'[àâä]', 'a', word)
    word = re.sub(r'[îïì]', 'i', word)
    word = re.sub(r'[ôöò]', 'o', word)
    word = re.sub(r'[ûüù]', 'u', word)
    word = re.sub(r'[ç]', 'c', word)
    word = re.sub(r'[ñ]', 'n', word)
    word = re.sub(r'[^a-zA-Z\'-]', '', word)
    word = word.lower()
    word = word.strip('-').strip("'")
    return word

def extract_words_from_pdf_text(pdf_path, start_line=4800, end_line=85500):
    """Extract words from the PDF text file."""
    words = set()
    
    print(f"Reading PDF: {pdf_path}")
    
    with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    print(f"Processing lines {start_line} to {min(end_line, len(lines))}")
    
    lines_processed = 0
    words_found = 0
    
    for i in range(start_line, min(end_line, len(lines))):
        line = lines[i].strip()
        
        if is_page_marker(line):
            continue
        if is_page_header(line):
            continue
        if is_section_header(line):
            continue
        if is_instruction_line(line):
            continue
        if not line:
            continue
        if len(line) > 100:
            continue
            
        lines_processed += 1
        
        parts = re.split(r'[\s,;]+', line)
        for part in parts:
            if part:
                cleaned = clean_word(part)
                if cleaned and looks_like_english_word(cleaned):
                    words.add(cleaned)
                    words_found += 1
    
    print(f"Processed {lines_processed} lines")
    print(f"Found {words_found} word instances")
    return sorted(words)

def is_likely_real_word(word):
    """Strict check - is this likely a real English word not in CMU?"""
    if len(word) < 4:
        return False
    if "'" in word:
        return False
    if "-" in word:
        return False
    
    common_endings = ['ing', 'tion', 'sion', 'ness', 'ment', 'able', 'ible', 
                      'ful', 'less', 'ous', 'ious', 'eous', 'ive', 'ative',
                      'ical', 'ally', 'erly', 'ling', 'ward', 'wise', 'like',
                      'ette', 'ling', 'ster', 'let', 'kin']
    common_starts = ['un', 're', 'dis', 'mis', 'pre', 'non', 'over', 'under',
                     'out', 'super', 'semi', 'anti', 'inter', 'multi', 'trans']
    
    has_good_ending = any(word.endswith(e) for e in common_endings)
    has_good_start = any(word.startswith(s) for s in common_starts)
    
    if not (has_good_ending or has_good_start):
        return False
    
    vowels = 'aeiouy'
    vowel_count = sum(1 for c in word if c in vowels)
    cons_count = sum(1 for c in word if c.isalpha() and c not in vowels)
    
    if cons_count == 0:
        return False
    ratio = vowel_count / cons_count
    if ratio < 0.25 or ratio > 2.0:
        return False
    
    return True

def validate_against_cmu(words):
    """Only keep words that are in CMU dictionary and look like real words."""
    cmu_words = set()
    
    for word in words:
        if len(word) < 3:
            continue
        if not word.isalpha():
            continue
        if pronouncing.phones_for_word(word):
            cmu_words.add(word)
    
    return cmu_words, set()

def main():
    pdf_path = r"c:\Users\chris\Downloads\pdfcoffee.com-clement-wooded-the-complete-rhyming-dictionary-revised-pdf.pdf"
    
    print("Extracting words from The Complete Rhyming Dictionary...")
    print("=" * 60)
    
    words = extract_words_from_pdf_text(pdf_path)
    
    print(f"\nExtracted {len(words)} unique candidate words")
    
    print("\nValidating against CMU dictionary...")
    cmu_words, _ = validate_against_cmu(words)
    
    print(f"  Validated words: {len(cmu_words)}")
    
    output = {
        "source": "The Complete Rhyming Dictionary by Clement Wood",
        "total_words": len(cmu_words),
        "words": sorted(cmu_words)
    }
    
    output_path = "data/pdf_words.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {output_path}")
    
    txt_path = "data/pdf_words.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(cmu_words)))
    print(f"Also saved to {txt_path}")
    
    print("\n" + "=" * 60)
    print("Sample words (first 100):")
    for word in sorted(cmu_words)[:100]:
        print(f"  {word}")

if __name__ == "__main__":
    main()
