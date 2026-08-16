#!/usr/bin/env python3
"""Run the Edge Brat generator with the original short-chunk grouping behavior."""

import importlib.util
import re
from pathlib import Path

BASE = Path(__file__).with_name("create_brat_lyrics_video.py")
spec = importlib.util.spec_from_file_location("brat_base", BASE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def legacy_build_sets(words, max_words):
    """Original behavior: punctuation/comma or a hard maximum word count."""
    limit = max_words if max_words and max_words > 0 else 6
    result = []
    start = 0
    for i, word in enumerate(words):
        shown = word["shown"]
        length = i - start + 1
        hard_break = bool(re.search(r"[.!?;:][\"'»”)]*$", shown))
        comma_break = bool(re.search(r",[\"'»”)]*$", shown)) and length >= 4
        word_break = length >= limit
        if hard_break or comma_break or word_break:
            result.append((start, i + 1))
            start = i + 1
    if start < len(words):
        result.append((start, len(words)))
    return result


module.build_sets = legacy_build_sets

if __name__ == "__main__":
    module.main()
