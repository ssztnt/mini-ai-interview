"""Classic (non-LLM) text analysis used as a deterministic baseline.

- **Sentiment**: VADER, a lexicon- and rule-based model tuned for short,
  informal text. Each answer gets a compound score in [-1, 1].
- **Keywords**: YAKE, an unsupervised statistical extractor (no training data,
  no external calls).

Showing this next to the LLM's reading makes their differences visible, e.g.
VADER often misreads sarcasm or "I love it, but…" style answers.
"""

from functools import lru_cache
from statistics import mean

import yake
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models import ClassicAnalysis, SentimentLabel

# VADER's recommended thresholds for neutral vs polar text
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


@lru_cache
def _vader() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def label_for(scores: list[float]) -> SentimentLabel:
    overall = mean(scores) if scores else 0.0
    has_positive = any(s >= POSITIVE_THRESHOLD for s in scores)
    has_negative = any(s <= NEGATIVE_THRESHOLD for s in scores)
    if has_positive and has_negative and abs(overall) < 0.3:
        return "mixed"
    if overall >= POSITIVE_THRESHOLD:
        return "positive"
    if overall <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def extract_keywords(text: str, top: int = 8) -> list[str]:
    extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.7, top=top)
    # YAKE scores: lower = more relevant; results arrive sorted.
    return [kw.lower() for kw, _score in extractor.extract_keywords(text)]


def analyze_answers(answers: list[str]) -> ClassicAnalysis:
    scores = [round(_vader().polarity_scores(a)["compound"], 3) for a in answers]
    return ClassicAnalysis(
        sentiment_label=label_for(scores),
        sentiment_score=round(mean(scores), 3) if scores else 0.0,
        answer_scores=scores,
        keywords=extract_keywords("\n".join(answers)),
    )
