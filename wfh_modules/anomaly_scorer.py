"""
anomaly_scorer.py - Native password anomaly scoring engine.

Implements a lightweight ensemble of anomaly detection algorithms inspired by
pyod (Zhao et al., 2019) to rank passwords by how unusual they are compared to
a reference corpus. All algorithms are reimplemented natively with no runtime
dependency on pyod or scikit-learn.

Algorithms included:
    - IsolationForest-lite: random partitioning depth score
    - HBOS-lite: histogram-based outlier score per feature dimension
    - Ensemble: mean of normalised scores from both algorithms

Features extracted per password:
    - length
    - digit ratio
    - upper ratio
    - lower ratio
    - special ratio
    - entropy (Shannon)
    - longest run of same char class
    - keyboard adjacency score (QWERTY)

Usage:
    from wfh_modules.anomaly_scorer import score_wordlist
    results = score_wordlist("path/to/wordlist.txt", top_n=100)
    for pw, score in results:
        print(f"{score:.4f}  {pw}")

Author: Andre Henrique (@mrhenrike) | Uniao Geek - https://github.com/Uniao-Geek
Version: 1.0.0
"""
from __future__ import annotations

import math
import random
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

__version__ = "1.0.0"

# QWERTY adjacency map (row/column neighbours only, lowercase)
_QWERTY_ADJ: Dict[str, str] = {
    "q": "wa", "w": "qeas", "e": "wrds", "r": "etdf", "t": "ryfg",
    "y": "tugh", "u": "yihj", "i": "uojk", "o": "ipkl", "p": "ol",
    "a": "qwsz", "s": "wedxza", "d": "erfcxs", "f": "rtgvcd", "g": "tyhbvf",
    "h": "yugnbg", "i": "uojk", "j": "uikmnh", "k": "iolmj", "l": "opk",
    "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb", "b": "vghn",
    "n": "bhjm", "m": "njk",
}


def _extract_features(password: str) -> List[float]:
    """Extract numeric feature vector from a password.

    Returns:
        8-dimensional feature vector [length, digit_ratio, upper_ratio,
        lower_ratio, special_ratio, entropy, longest_run, keyboard_adj_score].
    """
    if not password:
        return [0.0] * 8

    n = len(password)
    digits = sum(c.isdigit() for c in password)
    uppers = sum(c.isupper() for c in password)
    lowers = sum(c.islower() for c in password)
    specials = n - digits - uppers - lowers

    # Shannon entropy
    freq: Dict[str, int] = {}
    for c in password:
        freq[c] = freq.get(c, 0) + 1
    entropy = -sum((v / n) * math.log2(v / n) for v in freq.values())

    # Longest run of same character class
    def char_class(c: str) -> int:
        if c.isdigit():
            return 0
        if c.isupper():
            return 1
        if c.islower():
            return 2
        return 3

    max_run = 1
    run = 1
    for i in range(1, n):
        if char_class(password[i]) == char_class(password[i - 1]):
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1

    # Keyboard adjacency score: fraction of consecutive pairs that are adjacent
    adj_pairs = 0
    total_pairs = n - 1
    for i in range(total_pairs):
        a, b = password[i].lower(), password[i + 1].lower()
        if b in _QWERTY_ADJ.get(a, ""):
            adj_pairs += 1
    kbd_score = adj_pairs / total_pairs if total_pairs > 0 else 0.0

    return [
        float(n),
        digits / n,
        uppers / n,
        lowers / n,
        specials / n,
        entropy,
        float(max_run) / n,
        kbd_score,
    ]


# ---------------------------------------------------------------------------
# IsolationForest-lite
# ---------------------------------------------------------------------------

class _IsoNode:
    """Node in an isolation tree."""

    __slots__ = ("feature_idx", "split_value", "left", "right", "size")

    def __init__(self) -> None:
        self.feature_idx: int = 0
        self.split_value: float = 0.0
        self.left: Optional["_IsoNode"] = None
        self.right: Optional["_IsoNode"] = None
        self.size: int = 0


def _build_iso_tree(
    data: List[List[float]],
    indices: List[int],
    current_depth: int,
    max_depth: int,
    rng: random.Random,
) -> _IsoNode:
    node = _IsoNode()
    node.size = len(indices)

    if current_depth >= max_depth or len(indices) <= 1:
        return node

    n_features = len(data[0])
    feat_idx = rng.randint(0, n_features - 1)
    values = [data[i][feat_idx] for i in indices]
    min_v, max_v = min(values), max(values)

    if min_v == max_v:
        return node

    split = rng.uniform(min_v, max_v)
    left_idx = [i for i in indices if data[i][feat_idx] < split]
    right_idx = [i for i in indices if data[i][feat_idx] >= split]

    node.feature_idx = feat_idx
    node.split_value = split
    node.left = _build_iso_tree(data, left_idx, current_depth + 1, max_depth, rng)
    node.right = _build_iso_tree(data, right_idx, current_depth + 1, max_depth, rng)
    return node


def _path_length(node: _IsoNode, x: List[float], current_depth: int) -> float:
    """Return path length for sample x in isolation tree."""
    if node.left is None and node.right is None:
        n = node.size
        if n <= 1:
            return float(current_depth)
        # Expected path length for n samples
        c = 2.0 * (math.log(n - 1) + 0.5772156649) - (2.0 * (n - 1) / n)
        return current_depth + c

    if x[node.feature_idx] < node.split_value:
        return _path_length(node.left, x, current_depth + 1)
    return _path_length(node.right, x, current_depth + 1)


def _iso_forest_scores(
    features: List[List[float]],
    n_estimators: int = 50,
    max_samples: int = 128,
    seed: int = 42,
) -> List[float]:
    """Compute IsolationForest anomaly scores (0=normal, 1=anomaly)."""
    rng = random.Random(seed)
    n = len(features)
    if n == 0:
        return []

    sample_size = min(max_samples, n)
    max_depth = math.ceil(math.log2(sample_size)) if sample_size > 1 else 1

    trees = []
    for _ in range(n_estimators):
        sample_idx = rng.sample(range(n), sample_size)
        tree = _build_iso_tree(features, sample_idx, 0, max_depth, rng)
        trees.append(tree)

    c_n = 2.0 * (math.log(sample_size - 1) + 0.5772156649) - (2.0 * (sample_size - 1) / sample_size) if sample_size > 1 else 1.0

    scores = []
    for x in features:
        avg_path = sum(_path_length(t, x, 0) for t in trees) / n_estimators
        score = 2.0 ** (-avg_path / c_n)
        scores.append(score)

    return scores


# ---------------------------------------------------------------------------
# HBOS-lite
# ---------------------------------------------------------------------------

def _hbos_scores(features: List[List[float]], n_bins: int = 10) -> List[float]:
    """Compute Histogram-Based Outlier Scores (0=normal, higher=anomaly).

    Each feature dimension gets an independent histogram. The per-sample
    score is the sum of negative log-probabilities across dimensions.
    """
    if not features:
        return []

    n_features = len(features[0])
    n_samples = len(features)

    # Build per-feature histograms
    histograms: List[Tuple[List[float], List[float]]] = []
    for f_idx in range(n_features):
        col = [features[i][f_idx] for i in range(n_samples)]
        col_min, col_max = min(col), max(col)
        if col_min == col_max:
            histograms.append(([], []))
            continue

        bin_width = (col_max - col_min) / n_bins
        counts = [0.0] * n_bins
        for v in col:
            b = min(int((v - col_min) / bin_width), n_bins - 1)
            counts[b] += 1.0

        # Normalise to density
        densities = [c / (n_samples * bin_width) for c in counts]
        edges = [col_min + i * bin_width for i in range(n_bins + 1)]
        histograms.append((edges, densities))

    scores = []
    for i in range(n_samples):
        score = 0.0
        for f_idx in range(n_features):
            edges, densities = histograms[f_idx]
            if not edges:
                continue
            v = features[i][f_idx]
            bin_width = edges[1] - edges[0]
            b = min(int((v - edges[0]) / bin_width), len(densities) - 1)
            b = max(b, 0)
            density = densities[b] if densities[b] > 0 else 1e-10
            score += -math.log(density + 1e-10)
        scores.append(score)

    return scores


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def _normalise(scores: List[float]) -> List[float]:
    """Min-max normalise a list of scores to [0, 1]."""
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi == lo:
        return [0.5] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_passwords(passwords: Sequence[str]) -> List[Tuple[str, float]]:
    """Score a sequence of passwords by anomaly level.

    Higher score = more unusual compared to the rest of the input.

    Args:
        passwords: Sequence of password strings.

    Returns:
        List of (password, score) tuples, unsorted.
    """
    if not passwords:
        return []

    features = [_extract_features(pw) for pw in passwords]

    iso_raw = _iso_forest_scores(features)
    hbos_raw = _hbos_scores(features)

    iso_norm = _normalise(iso_raw)
    hbos_norm = _normalise(hbos_raw)

    ensemble = [(a + b) / 2.0 for a, b in zip(iso_norm, hbos_norm)]

    return list(zip(passwords, ensemble))


def score_wordlist(
    path: str,
    top_n: int = 0,
    max_lines: int = 100_000,
    encoding: str = "utf-8",
) -> List[Tuple[str, float]]:
    """Load a wordlist file and score each entry by anomaly level.

    Args:
        path: Path to a wordlist file (one entry per line).
        top_n: Return only the top-N most anomalous entries. 0 = all.
        max_lines: Maximum lines to read from the file.
        encoding: File encoding.

    Returns:
        List of (password, score) sorted descending by score.

    Raises:
        FileNotFoundError: If the wordlist file does not exist.
    """
    fpath = Path(path)
    if not fpath.exists():
        raise FileNotFoundError(f"Wordlist not found: {fpath}")

    passwords: List[str] = []
    with open(fpath, encoding=encoding, errors="replace") as fh:
        for i, line in enumerate(fh):
            if i >= max_lines:
                break
            pw = line.rstrip("\n\r")
            if pw:
                passwords.append(pw)

    results = score_passwords(passwords)
    results.sort(key=lambda t: t[1], reverse=True)

    if top_n > 0:
        return results[:top_n]
    return results
