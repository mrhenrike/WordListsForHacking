"""
benchmark_suite.py — Wordlist quality benchmarking suite.

Measures the effectiveness of generated wordlists against reference datasets
using metrics from academic research (MAYA, PCWQ, CMU PGS).

Metrics:
  - Hit Rate: % of reference passwords matched
  - Coverage: unique matches / reference size
  - Efficiency: hits / total candidates (no duplicates)
  - Duplicate Rate: % of duplicate candidates
  - Diversity Index: Shannon entropy of character distribution
  - Length Distribution: coverage per password length
  - Estimated Crack Time: based on hash rate assumptions

Inspired by MAYA (IEEE S&P 2026) benchmarking framework.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

HASH_RATES = {
    "md5":       60_000_000_000,
    "sha1":      20_000_000_000,
    "sha256":     8_000_000_000,
    "ntlm":     100_000_000_000,
    "bcrypt_5":          50_000,
    "bcrypt_10":          1_500,
    "scrypt":            10_000,
    "argon2":             2_000,
    "wpa2":             800_000,
}


def _shannon_entropy(text_sample: str) -> float:
    """Compute Shannon entropy of a character distribution."""
    if not text_sample:
        return 0.0
    freq = Counter(text_sample)
    total = len(text_sample)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _jaccard_index(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity index between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


class BenchmarkResult:
    """Container for benchmark metrics."""

    def __init__(self) -> None:
        self.total_candidates: int = 0
        self.unique_candidates: int = 0
        self.duplicate_count: int = 0
        self.reference_size: int = 0
        self.hits: int = 0
        self.hit_rate: float = 0.0
        self.efficiency: float = 0.0
        self.duplicate_rate: float = 0.0
        self.diversity_index: float = 0.0
        self.length_coverage: dict[int, dict] = {}
        self.charset_coverage: dict[str, float] = {}
        self.crack_time_estimates: dict[str, str] = {}
        self.top_hits: list[str] = []
        self.top_misses: list[str] = []
        self.elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "total_candidates": self.total_candidates,
            "unique_candidates": self.unique_candidates,
            "duplicate_count": self.duplicate_count,
            "duplicate_rate": round(self.duplicate_rate, 4),
            "reference_size": self.reference_size,
            "hits": self.hits,
            "hit_rate": round(self.hit_rate, 4),
            "efficiency": round(self.efficiency, 6),
            "diversity_index": round(self.diversity_index, 4),
            "length_coverage": self.length_coverage,
            "charset_coverage": self.charset_coverage,
            "crack_time_estimates": self.crack_time_estimates,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }

    def describe(self) -> str:
        """Return human-readable benchmark report."""
        lines = [
            "=" * 60,
            "  WORDLIST QUALITY BENCHMARK REPORT",
            "=" * 60,
            "",
            f"  Candidates (total)    : {self.total_candidates:>12,}",
            f"  Candidates (unique)   : {self.unique_candidates:>12,}",
            f"  Duplicates            : {self.duplicate_count:>12,}  ({self.duplicate_rate * 100:.1f}%)",
            "",
            f"  Reference set size    : {self.reference_size:>12,}",
            f"  Hits (matches)        : {self.hits:>12,}",
            f"  HIT RATE              : {self.hit_rate * 100:>11.2f}%",
            f"  EFFICIENCY            : {self.efficiency * 100:>11.4f}%  (hits / unique candidates)",
            f"  DIVERSITY (Shannon)   : {self.diversity_index:>11.4f} bits",
            "",
        ]

        if self.length_coverage:
            lines.append("  Coverage by length:")
            for length in sorted(self.length_coverage.keys()):
                data = self.length_coverage[length]
                lines.append(
                    f"    len={length:2d}: {data['hits']:>6,}/{data['total']:>6,}"
                    f"  ({data['rate'] * 100:5.1f}%)"
                )
            lines.append("")

        if self.charset_coverage:
            lines.append("  Coverage by charset:")
            for cs, rate in sorted(self.charset_coverage.items(), key=lambda x: -x[1]):
                lines.append(f"    {cs:20s}: {rate * 100:5.1f}%")
            lines.append("")

        if self.crack_time_estimates:
            lines.append("  Estimated time to exhaust wordlist:")
            for algo, est in self.crack_time_estimates.items():
                lines.append(f"    {algo:12s}: {est}")
            lines.append("")

        lines.append(f"  Benchmark completed in {self.elapsed_seconds:.2f}s")
        lines.append("=" * 60)
        return "\n".join(lines)


def _classify_charset(password: str) -> str:
    """Classify a password by its character composition."""
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    parts = []
    if has_lower:
        parts.append("lower")
    if has_upper:
        parts.append("upper")
    if has_digit:
        parts.append("digit")
    if has_special:
        parts.append("special")

    return "+".join(parts) if parts else "empty"


def _format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 0.001:
        return "< 1ms"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}min"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    if seconds < 86400 * 365:
        return f"{seconds / 86400:.1f} days"
    return f"{seconds / (86400 * 365):.1f} years"


def benchmark(
    wordlist_path: str,
    reference_path: str,
    max_candidates: int = 0,
    max_reference: int = 0,
    sample_diversity: int = 100_000,
) -> BenchmarkResult:
    """Run a full benchmark of a wordlist against a reference set.

    Args:
        wordlist_path: Path to the generated wordlist to evaluate.
        reference_path: Path to the reference password set (ground truth).
        max_candidates: Max lines to read from wordlist (0 = all).
        max_reference: Max lines to read from reference (0 = all).
        sample_diversity: Characters to sample for diversity calculation.

    Returns:
        BenchmarkResult with all metrics.
    """
    result = BenchmarkResult()
    start = time.time()

    ref_set: set[str] = set()
    ref_by_length: dict[int, set[str]] = defaultdict(set)
    ref_by_charset: dict[str, set[str]] = defaultdict(set)

    ref_path = Path(reference_path)
    with ref_path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if not pw:
                continue
            if ":" in pw:
                pw = pw.split(":", 1)[-1]
            ref_set.add(pw)
            ref_by_length[len(pw)].add(pw)
            ref_by_charset[_classify_charset(pw)].add(pw)
            if max_reference and len(ref_set) >= max_reference:
                break

    result.reference_size = len(ref_set)

    seen: set[str] = set()
    hits: set[str] = set()
    hits_by_length: dict[int, int] = defaultdict(int)
    hits_by_charset: dict[str, int] = defaultdict(int)
    diversity_sample: list[str] = []
    total = 0

    wl_path = Path(wordlist_path)
    with wl_path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            candidate = line.rstrip("\n\r")
            if not candidate:
                continue
            total += 1

            if candidate in seen:
                result.duplicate_count += 1
            else:
                seen.add(candidate)
                if candidate in ref_set and candidate not in hits:
                    hits.add(candidate)
                    hits_by_length[len(candidate)] += 1
                    hits_by_charset[_classify_charset(candidate)] += 1

                if len(diversity_sample) < sample_diversity:
                    diversity_sample.append(candidate)

            if max_candidates and total >= max_candidates:
                break

    result.total_candidates = total
    result.unique_candidates = len(seen)
    result.hits = len(hits)
    result.hit_rate = result.hits / result.reference_size if result.reference_size else 0.0
    result.efficiency = result.hits / result.unique_candidates if result.unique_candidates else 0.0
    result.duplicate_rate = result.duplicate_count / total if total else 0.0

    all_chars = "".join(diversity_sample[:sample_diversity])
    result.diversity_index = _shannon_entropy(all_chars)

    for length, ref_passwords in sorted(ref_by_length.items()):
        h = hits_by_length.get(length, 0)
        t = len(ref_passwords)
        result.length_coverage[length] = {
            "hits": h, "total": t,
            "rate": h / t if t else 0.0,
        }

    for cs, ref_passwords in sorted(ref_by_charset.items()):
        h = hits_by_charset.get(cs, 0)
        t = len(ref_passwords)
        result.charset_coverage[cs] = h / t if t else 0.0

    for algo, rate in HASH_RATES.items():
        if result.unique_candidates > 0:
            secs = result.unique_candidates / rate
            result.crack_time_estimates[algo] = _format_duration(secs)

    result.elapsed_seconds = time.time() - start
    return result


def benchmark_generator(
    generator: Generator[str, None, None],
    reference_path: str,
    max_candidates: int = 0,
    max_reference: int = 0,
) -> BenchmarkResult:
    """Benchmark a generator directly without writing to file.

    Args:
        generator: Password candidate generator.
        reference_path: Path to reference password set.
        max_candidates: Max candidates to consume (0 = all).
        max_reference: Max reference lines (0 = all).

    Returns:
        BenchmarkResult.
    """
    result = BenchmarkResult()
    start = time.time()

    ref_set: set[str] = set()
    ref_by_length: dict[int, set[str]] = defaultdict(set)

    ref_path = Path(reference_path)
    with ref_path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if not pw:
                continue
            if ":" in pw:
                pw = pw.split(":", 1)[-1]
            ref_set.add(pw)
            ref_by_length[len(pw)].add(pw)
            if max_reference and len(ref_set) >= max_reference:
                break

    result.reference_size = len(ref_set)

    seen: set[str] = set()
    hits: set[str] = set()
    hits_by_length: dict[int, int] = defaultdict(int)
    total = 0

    for candidate in generator:
        total += 1
        if candidate in seen:
            result.duplicate_count += 1
        else:
            seen.add(candidate)
            if candidate in ref_set and candidate not in hits:
                hits.add(candidate)
                hits_by_length[len(candidate)] += 1
        if max_candidates and total >= max_candidates:
            break

    result.total_candidates = total
    result.unique_candidates = len(seen)
    result.hits = len(hits)
    result.hit_rate = result.hits / result.reference_size if result.reference_size else 0.0
    result.efficiency = result.hits / result.unique_candidates if result.unique_candidates else 0.0
    result.duplicate_rate = result.duplicate_count / total if total else 0.0

    for length, ref_passwords in sorted(ref_by_length.items()):
        h = hits_by_length.get(length, 0)
        t = len(ref_passwords)
        result.length_coverage[length] = {
            "hits": h, "total": t,
            "rate": h / t if t else 0.0,
        }

    for algo, rate in HASH_RATES.items():
        if result.unique_candidates > 0:
            result.crack_time_estimates[algo] = _format_duration(result.unique_candidates / rate)

    result.elapsed_seconds = time.time() - start
    return result


def handle_benchmark(args, ctx: dict) -> Optional[Generator[str, None, None]]:
    """CLI handler for wordlist benchmarking.

    Args:
        args: Parsed CLI arguments.
        ctx: Global execution context.

    Returns:
        Generator yielding the benchmark report, or None.
    """
    wordlist = getattr(args, "wordlist", None)
    reference = getattr(args, "reference", None)

    if not wordlist or not reference:
        logger.error("Both --wordlist and --reference are required")
        return None

    wl_path = Path(wordlist)
    ref_path = Path(reference)

    if not wl_path.exists():
        logger.error("Wordlist not found: %s", wordlist)
        return None
    if not ref_path.exists():
        logger.error("Reference set not found: %s", reference)
        return None

    result = benchmark(
        str(wl_path), str(ref_path),
        max_candidates=getattr(args, "max_candidates", 0) or 0,
        max_reference=getattr(args, "max_reference", 0) or 0,
    )

    output_json = getattr(args, "json_output", None)
    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8") as fh:
            json.dump(result.to_dict(), fh, indent=2, ensure_ascii=False)
        logger.info("JSON report saved: %s", output_json)

    return iter([result.describe()])
