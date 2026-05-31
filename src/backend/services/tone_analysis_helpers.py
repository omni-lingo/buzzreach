"""Text analysis helpers for tone detection (FEAT-005).

Pure functions for computing reading level, marketing score,
and AI likelihood from raw text. No I/O, no HTTP, no logging.
"""

import re

# ---------------------------------------------------------------------------
# Marketing keywords — weighted by how "salesy" each phrase sounds
# ---------------------------------------------------------------------------

_MARKETING_HEAVY: list[str] = [
    "buy now", "act now", "act fast", "order now", "order today",
    "limited time", "limited offer", "exclusive deal", "exclusive offer",
    "don't miss out", "don't miss", "click here", "sign up now",
    "free trial", "free shipping", "money back", "guaranteed",
    "best price", "lowest price", "discount", "special offer",
    "hurry", "last chance", "once in a lifetime",
]

_MARKETING_MEDIUM: list[str] = [
    "amazing", "incredible", "unbelievable", "revolutionary",
    "game changer", "game-changer", "must have", "must-have",
    "transform", "skyrocket", "supercharge", "unleash",
    "powerful", "ultimate", "premium",
]

_MARKETING_LIGHT: list[str] = [
    "check out", "take a look", "worth trying",
    "highly recommend", "strongly recommend",
]

# ---------------------------------------------------------------------------
# AI-pattern signals — phrases/structures typical of LLM output
# ---------------------------------------------------------------------------

_AI_PHRASES: list[str] = [
    "it is important to note",
    "it is worth mentioning",
    "it's worth noting",
    "in conclusion",
    "furthermore",
    "moreover",
    "additionally",
    "aforementioned",
    "the broader context",
    "it should be noted",
    "comprehensive overview",
    "multifaceted",
    "in the context of",
    "navigate this",
    "navigating this",
    "delve into",
    "delving into",
    "it bears mentioning",
    "the implications of",
    "the ramifications of",
]


def count_syllables(word: str) -> int:
    """Estimate syllable count for an English word.

    Uses a vowel-group heuristic: count groups of consecutive vowels,
    subtract silent-e, enforce minimum of 1.
    """
    word = word.lower().strip()
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation boundaries."""
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def split_words(text: str) -> list[str]:
    """Extract word tokens from text."""
    return re.findall(r"[a-zA-Z']+", text)


def flesch_kincaid_grade(text: str) -> float:
    """Compute Flesch-Kincaid grade level.

    Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    Returns 0.0 for empty or degenerate text.
    """
    words = split_words(text)
    sentences = split_sentences(text)
    if not words or not sentences:
        return 0.0
    total_syllables = sum(count_syllables(w) for w in words)
    word_count = len(words)
    sentence_count = len(sentences)
    grade = (
        0.39 * (word_count / sentence_count)
        + 11.8 * (total_syllables / word_count)
        - 15.59
    )
    return max(grade, 0.0)


def compute_marketing_score(text: str) -> float:
    """Score how salesy/promotional the text sounds (0.0 to 1.0).

    Counts weighted keyword hits relative to word count.
    Weights: heavy=3, medium=2, light=1.
    """
    lower = text.lower()
    words = split_words(text)
    if not words:
        return 0.0
    score = 0.0
    score += _count_phrase_hits(lower, _MARKETING_HEAVY) * 3.0
    score += _count_phrase_hits(lower, _MARKETING_MEDIUM) * 2.0
    score += _count_phrase_hits(lower, _MARKETING_LIGHT) * 1.0
    exclamation_count = text.count("!")
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
    score += exclamation_count * 1.5
    score += caps_words * 1.0
    normalized = score / len(words)
    return min(normalized, 1.0)


def compute_ai_likelihood(text: str) -> float:
    """Estimate probability the text was AI-generated (0.0 to 1.0).

    Heuristic based on: AI-typical phrases, sentence uniformity,
    and transition word density.
    """
    lower = text.lower()
    words = split_words(text)
    if not words:
        return 0.0
    phrase_hits = _count_phrase_hits(lower, _AI_PHRASES)
    phrase_signal = min(phrase_hits / max(len(words) / 20, 1), 1.0)
    uniformity = _sentence_length_uniformity(text)
    transition_density = _transition_word_density(lower, words)
    raw = (
        phrase_signal * 0.50
        + uniformity * 0.25
        + transition_density * 0.25
    )
    return min(max(raw, 0.0), 1.0)


def _count_phrase_hits(lower_text: str, phrases: list[str]) -> float:
    """Count how many phrases from the list appear in the text."""
    return sum(1 for p in phrases if p in lower_text)


def _sentence_length_uniformity(text: str) -> float:
    """How uniform are sentence lengths (AI tends toward uniformity).

    Returns 0.0 (high variance = human) to 1.0 (uniform = AI-like).
    """
    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0.0
    lengths = [len(split_words(s)) for s in sentences]
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.0
    variance = sum((ln - mean) ** 2 for ln in lengths) / len(lengths)
    std_dev = variance ** 0.5
    cv = std_dev / mean
    return max(0.0, 1.0 - cv)


def _transition_word_density(
    lower_text: str, words: list[str]
) -> float:
    """Density of formal transition words (AI overuses these)."""
    transitions = [
        "furthermore", "moreover", "additionally", "consequently",
        "nevertheless", "nonetheless", "subsequently", "accordingly",
        "hence", "thus", "therefore", "whereby",
    ]
    hits = sum(1 for w in words if w.lower() in transitions)
    density = hits / len(words) if words else 0.0
    return min(density * 20, 1.0)
