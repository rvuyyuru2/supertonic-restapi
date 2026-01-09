import re
from unicodedata import normalize
from typing import AsyncGenerator, Tuple, List, Optional
from app.api.schemas import NormalizationOptions

def clean_text(text: str) -> str:
    """
    Minimal text preprocessing as suggested by the example code.
    Replaces common symbols, removes emojis, and ensures basic punctuation.
    """
    # 1. Unicode normalization
    text = normalize("NFKD", text)

    # 2. Remove emojis (wide Unicode range)
    emoji_pattern = re.compile(
        "[\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f700-\U0001f77f"
        "\U0001f780-\U0001f7ff"
        "\U0001f800-\U0001f8ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\u2600-\u26ff"
        "\u2700-\u27bf"
        "\U0001f1e6-\U0001f1ff]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    # 3. Replace various dashes and symbols with simpler versions
    replacements = {
        "–": "-", "‑": "-", "—": "-", "¯": " ", "_": " ",
        "\u201C": '"', "\u201D": '"', "\u2018": "'", "\u2019": "'",
        "´": "'", "`": "'", "[": " ", "]": " ", "|": " ", "/": " ",
        "#": " ", "→": " ", "←": " ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # 4. Remove combining diacritics
    text = re.sub(
        r"[\u0302\u0303\u0304\u0305\u0306\u0307\u0308\u030A\u030B\u030C\u0327\u0328\u0329\u032A\u032B\u032C\u032D\u032E\u032F]",
        "", text,
    )

    # 5. Remove special symbols
    text = re.sub(r"[♥☆♡©\\]", "", text)

    # 6. Replace known expressions
    expr_replacements = {
        "@": " at ",
        "e.g.,": "for example, ",
        "i.e.,": "that is, ",
    }
    for k, v in expr_replacements.items():
        text = text.replace(k, v)

    # 7. Fix spacing around punctuation
    text = re.sub(r" ,", ",", text)
    text = re.sub(r" \.", ".", text)
    text = re.sub(r" !", "!", text)
    text = re.sub(r" \?", "?", text)
    text = re.sub(r" ;", ";", text)
    text = re.sub(r" :", ":", text)
    text = re.sub(r" '", "'", text)

    # 8. Remove duplicate quotes and spaces
    while '""' in text: text = text.replace('""', '"')
    while "''" in text: text = text.replace("''", "'")
    text = re.sub(r"\s+", " ", text).strip()

    # 9. Ensure ending punctuation
    if text and not re.search(r"[.!?;:,'\"')\]}…。」』】〉》›»]$", text):
        text += "."

    return text

async def smart_split(
    text: str,
    lang_code: str = "en",
    normalization_options: Optional[NormalizationOptions] = None
) -> AsyncGenerator[Tuple[str, List[int], Optional[float]], None]:
    """
    Split text into chunks by paragraphs and sentences using logic from Supertonic examples.
    Yields: (chunk_text, tokens, pause_duration_s)
    """
    # 1. Split by pause tags first to handle duration-based gaps
    parts = re.split(r'(\[pause:\d+\.?\d*\])', text)
    
    # Advanced sentence boundary regex that handles abbreviations
    sentence_pattern = r"(?<!Mr\.)(?<!Mrs\.)(?<!Ms\.)(?<!Dr\.)(?<!Prof\.)(?<!Sr\.)(?<!Jr\.)(?<!Ph\.D\.)(?<!etc\.)(?<!e\.g\.)(?<!i\.e\.)(?<!vs\.)(?<!Inc\.)(?<!Ltd\.)(?<!Co\.)(?<!Corp\.)(?<!St\.)(?<!Ave\.)(?<!Blvd\.)(?<!\b[A-Z]\.)(?<=[.!?])\s+"
    
    for part in parts:
        pause_match = re.match(r'\[pause:(\d+\.?\d*)\]', part)
        if pause_match:
            yield "", [], float(pause_match.group(1))
            continue
            
        if not part.strip():
            continue

        # 2. Split by paragraph (two or more newlines)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", part.strip()) if p.strip()]
        
        for paragraph in paragraphs:
            # 3. Split by sentence boundaries
            sentences = re.split(sentence_pattern, paragraph)
            
            # Combine sentences into chunks of reasonable length (e.g., 300 chars)
            current_chunk = ""
            max_len = 300
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk) + len(sentence) + 1 <= max_len:
                    current_chunk += (" " if current_chunk else "") + sentence
                else:
                    if current_chunk:
                        yield current_chunk.strip(), [], None
                    current_chunk = sentence
            
            if current_chunk:
                yield current_chunk.strip(), [], None
