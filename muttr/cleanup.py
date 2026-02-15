"""Deterministic text cleanup using regex rules.

Slider levels:
    0  Light    - whitespace, repeated words, sentence case, punctuation,
                  paragraph/line-break commands, proper noun capitalization
    1  Moderate - all Light + filler word removal + list formatting
    2  Aggressive - all Moderate + false-start removal + stronger punctuation smoothing
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Proper-noun dictionaries (users can extend CUSTOM_PROPER_NOUNS)
# ---------------------------------------------------------------------------

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
COMMON_FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen", "Charles",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Andrew",
    "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley", "Dorothy",
    "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Melissa",
    "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia",
    "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela",
    "Emma", "Nicole", "Helen", "Samantha", "Katherine", "Christine",
    "Hannah", "Rachel", "Carolyn", "Janet", "Catherine", "Maria",
    "Heather", "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia",
    "Victoria", "Kelly", "Lauren", "Christina", "Joan", "Evelyn", "Judith",
    "Andrea", "Megan", "Cheryl", "Jacqueline", "Teresa",
    "Alice", "Martha", "Ann", "Gloria", "Kathryn", "Marie",
    "Peter", "Ryan", "Jason", "Gary", "Jeff", "Eric", "Stephen",
    "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel",
    "Raymond", "Gregory", "Frank", "Alexander", "Patrick", "Jack",
    "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Nathan", "Henry",
    "Adam", "Douglas", "Zachary", "Harold", "Carl", "Arthur",
    "Dylan", "Ethan", "Noah", "Logan", "Lucas", "Aiden", "Liam",
    "Mason", "Elijah", "Owen", "Sebastian", "Gabriel", "Carter",
    "Jayden", "Luke", "Isaac",
]

# Brand names / tech terms: mapping of lowercase -> correct casing
BRAND_NAMES = {
    "iphone": "iPhone",
    "ipad": "iPad",
    "ipod": "iPod",
    "imac": "iMac",
    "ios": "iOS",
    "ipados": "iPadOS",
    "macos": "macOS",
    "watchos": "watchOS",
    "tvos": "tvOS",
    "visionos": "visionOS",
    "airpods": "AirPods",
    "macbook": "MacBook",
    "google": "Google",
    "gmail": "Gmail",
    "youtube": "YouTube",
    "android": "Android",
    "chromebook": "Chromebook",
    "microsoft": "Microsoft",
    "windows": "Windows",
    "linkedin": "LinkedIn",
    "github": "GitHub",
    "gitlab": "GitLab",
    "chatgpt": "ChatGPT",
    "openai": "OpenAI",
    "claude": "Claude",
    "anthropic": "Anthropic",
    "amazon": "Amazon",
    "aws": "AWS",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "tesla": "Tesla",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "whatsapp": "WhatsApp",
    "snapchat": "Snapchat",
    "twitter": "Twitter",
    "uber": "Uber",
    "airbnb": "Airbnb",
    "slack": "Slack",
    "zoom": "Zoom",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "postgres": "Postgres",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "react": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "vue": "Vue",
    "angular": "Angular",
    "django": "Django",
    "flask": "Flask",
    "wordpress": "WordPress",
    "shopify": "Shopify",
    "photoshop": "Photoshop",
    "figma": "Figma",
    "notion": "Notion",
    "trello": "Trello",
    "jira": "Jira",
    "asana": "Asana",
    "safari": "Safari",
    "firefox": "Firefox",
    "chrome": "Chrome",
    "bluetooth": "Bluetooth",
    "wifi": "Wi-Fi",
    "wi-fi": "Wi-Fi",
    "usb": "USB",
    "api": "API",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "json": "JSON",
    "xml": "XML",
    "http": "HTTP",
    "https": "HTTPS",
    "url": "URL",
    "pdf": "PDF",
    "jpeg": "JPEG",
    "png": "PNG",
    "gif": "GIF",
    "svg": "SVG",
    "nasa": "NASA",
    "fbi": "FBI",
    "cia": "CIA",
    "nfl": "NFL",
    "nba": "NBA",
    "mlb": "MLB",
    "nhl": "NHL",
    "usa": "USA",
    "uk": "UK",
    "eu": "EU",
    "un": "UN",
}

COUNTRIES_AND_CITIES = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bangladesh", "Belgium", "Bolivia", "Brazil",
    "Bulgaria", "Cambodia", "Canada", "Chile", "China", "Colombia",
    "Croatia", "Cuba", "Cyprus", "Denmark", "Ecuador", "Egypt", "England",
    "Estonia", "Ethiopia", "Finland", "France", "Georgia", "Germany",
    "Ghana", "Greece", "Guatemala", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "Korea", "Kuwait",
    "Latvia", "Lebanon", "Libya", "Lithuania", "Luxembourg", "Malaysia",
    "Mexico", "Mongolia", "Morocco", "Nepal", "Netherlands", "Nigeria",
    "Norway", "Oman", "Pakistan", "Panama", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
    "Scotland", "Singapore", "Slovakia", "Slovenia", "Somalia",
    "Spain", "Sweden", "Switzerland", "Syria", "Taiwan", "Thailand",
    "Turkey", "Uganda", "Ukraine", "Uruguay", "Uzbekistan", "Venezuela",
    "Vietnam", "Wales", "Yemen", "Zimbabwe",
    "Africa", "Antarctica", "Asia", "Europe", "Oceania",
    "London", "Paris", "Tokyo", "Berlin", "Madrid", "Rome", "Beijing",
    "Shanghai", "Mumbai", "Delhi", "Bangkok", "Seoul", "Sydney",
    "Melbourne", "Toronto", "Vancouver", "Montreal", "Chicago",
    "Boston", "Seattle", "Denver", "Austin", "Dallas", "Houston",
    "Phoenix", "Atlanta", "Miami", "Orlando", "Portland", "Detroit",
    "Minneapolis", "Philadelphia", "Pittsburgh", "Baltimore", "Nashville",
    "Charlotte", "Raleigh", "Indianapolis", "Columbus", "Cleveland",
    "Cincinnati", "Milwaukee", "Sacramento", "Brooklyn", "Manhattan",
    "Dublin", "Edinburgh", "Amsterdam", "Brussels", "Vienna", "Prague",
    "Warsaw", "Budapest", "Copenhagen", "Stockholm", "Oslo", "Helsinki",
    "Lisbon", "Barcelona", "Munich", "Hamburg", "Milan", "Naples",
    "Istanbul", "Cairo", "Lagos", "Nairobi", "Johannesburg", "Dubai",
    "Singapore", "Taipei", "Osaka", "Kyoto", "Auckland", "Wellington",
    "Honolulu", "Alaska", "Hawaii", "California", "Texas", "Florida",
    "Massachusetts", "Connecticut", "Colorado", "Virginia", "Maryland",
    "Georgia", "Tennessee", "Carolina", "Illinois", "Michigan",
    "Minnesota", "Wisconsin", "Missouri", "Oregon", "Washington",
    "Arizona", "Nevada", "Utah", "Montana", "Idaho",
    "Mississippi", "Alabama", "Louisiana", "Kentucky", "Arkansas",
    "Oklahoma", "Kansas", "Nebraska", "Iowa",
    "New York", "Los Angeles", "San Francisco", "San Diego",
    "San Antonio", "San Jose", "Las Vegas", "New Orleans",
    "Salt Lake City", "Kansas City", "Oklahoma City", "New Jersey",
    "New Mexico", "New Hampshire", "Rhode Island", "South Dakota",
    "North Dakota", "South Carolina", "North Carolina", "West Virginia",
]

# Extensible user dictionary -- users can add entries at runtime
CUSTOM_PROPER_NOUNS: dict[str, str] = {}

# Build the lookup table: lowercase -> correct casing
_PROPER_NOUN_MAP: dict[str, str] = {}


def _rebuild_proper_noun_map() -> None:
    """Rebuild the internal lookup from all source lists."""
    _PROPER_NOUN_MAP.clear()
    for name in DAYS_OF_WEEK + MONTHS + COMMON_FIRST_NAMES:
        _PROPER_NOUN_MAP[name.lower()] = name
    for place in COUNTRIES_AND_CITIES:
        _PROPER_NOUN_MAP[place.lower()] = place
    _PROPER_NOUN_MAP.update(BRAND_NAMES)
    _PROPER_NOUN_MAP.update({k.lower(): v for k, v in CUSTOM_PROPER_NOUNS.items()})


_rebuild_proper_noun_map()


def add_proper_nouns(nouns: dict[str, str]) -> None:
    """Add user-defined proper nouns.  Keys are lowercase triggers, values are
    the desired casing.  E.g. ``{"muttr": "MuttR"}``."""
    CUSTOM_PROPER_NOUNS.update(nouns)
    _rebuild_proper_noun_map()


# ---------------------------------------------------------------------------
# Filler words
# ---------------------------------------------------------------------------

FILLER_WORDS = [
    r"\bum\b",
    r"\buh\b",
    r"\byou know\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bI mean\b",
    r"\bsort of\b",
    r"\bkind of\b",
]

FILLER_PATTERN = re.compile(
    r",?\s*(?:" + "|".join(FILLER_WORDS) + r")\s*,?\s*",
    re.IGNORECASE,
)

# "like" needs context-aware handling: filler ("I was like going") vs
# comparison ("looks like a cat") vs verb ("I like pizza").
# Strategy: protect known non-filler patterns, strip the rest, restore.
_LIKE_PROTECT = re.compile(
    r"\b(looks?|looking|feels?|felt|feeling|seems?|seemed|seeming"
    r"|sounds?|sounded|sounding|smells?|smelled|tastes?|tasted"
    r"|just|more|much"
    r"|something|anything|nothing|everything"
    r"|[Ii]|you|we|they|he|she|it)\s+(like)\b",
    re.IGNORECASE,
)
_LIKE_FILLER = re.compile(r",?\s*\blike\b\s*,?\s*", re.IGNORECASE)
_LIKE_SENTINEL = "\x00COMP\x00"

# ---------------------------------------------------------------------------
# Paragraph / line-break commands
# ---------------------------------------------------------------------------

# "period new paragraph" -> ". \n\n"
_PERIOD_NEW_PARA = re.compile(
    r"[.\s]*\b(?:period)\s+(?:new\s+paragraph)\b",
    re.IGNORECASE,
)
# "new paragraph" / "next paragraph"
_NEW_PARAGRAPH = re.compile(
    r"\s*\b(?:new|next)\s+paragraph\b\s*",
    re.IGNORECASE,
)
# "new line" / "next line"
_NEW_LINE = re.compile(
    r"\s*\b(?:new|next)\s+line\b\s*",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Bullet list patterns
# ---------------------------------------------------------------------------

# "bullet point one ... bullet point two ..."
# "bullet one ... bullet two ..."
# "bullet ..."  (single bullet at start)
_BULLET_ORDINALS = "|".join([
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
])
_BULLET_ITEM = re.compile(
    r"\s*\bbullet\s*(?:point)?\s*(?:(?:" + _BULLET_ORDINALS + r")\s+)?",
    re.IGNORECASE,
)

# "dash <text>" at start or after punctuation
_DASH_ITEM = re.compile(
    r"\s*\bdash\b\s*",
    re.IGNORECASE,
)

# "next item" as bullet separator
_NEXT_ITEM = re.compile(
    r"\s*\bnext\s+item\b\s*",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Numbered list patterns
# ---------------------------------------------------------------------------

# Spoken ordinals
_ORDINAL_MAP = {
    "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5",
    "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
}
# Spoken cardinals used in list contexts
_CARDINAL_MAP = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}

# "number one ... number two ..."
_NUMBER_WORD_ITEM = re.compile(
    r"\s*\bnumber\s+(" + "|".join(_CARDINAL_MAP.keys()) + r")\b[.,):\s]*",
    re.IGNORECASE,
)

# "number 1 ... number 2 ..."
_NUMBER_DIGIT_ITEM = re.compile(
    r"\s*\bnumber\s+(\d{1,2})\b[.,):\s]*",
    re.IGNORECASE,
)

# "first, ... second, ..."  (ordinals as list starters)
_ORDINAL_ITEM = re.compile(
    r"\s*\b(" + "|".join(_ORDINAL_MAP.keys()) + r")\b[.,):\s]*",
    re.IGNORECASE,
)

# "1. text" or "1) text" patterns (Whisper sometimes transcribes these)
_DIGIT_DOT_ITEM = re.compile(
    r"\s*(\d{1,2})\s*[.)]\s*",
)

# "one) text" patterns
_CARDINAL_PAREN_ITEM = re.compile(
    r"\s*\b(" + "|".join(_CARDINAL_MAP.keys()) + r")\s*\)\s*",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Proper-noun capitalization
# ---------------------------------------------------------------------------

# We match "word" tokens to check against the map.  Multi-word proper nouns
# (like "New York") need separate handling.
_MULTI_WORD_NOUNS = {k: v for k, v in _PROPER_NOUN_MAP.items() if " " in k}
_SINGLE_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")


def _capitalize_proper_nouns(text: str) -> str:
    """Replace known proper nouns with their correct casing."""
    # Multi-word nouns first (greedy, longest match first)
    for lc, correct in sorted(_MULTI_WORD_NOUNS.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(lc), re.IGNORECASE)
        text = pattern.sub(correct, text)

    def _replace_single(m: re.Match) -> str:
        word = m.group(0)
        lc = word.lower()
        if lc in _PROPER_NOUN_MAP and lc not in _MULTI_WORD_NOUNS:
            return _PROPER_NOUN_MAP[lc]
        return word

    text = _SINGLE_WORD_RE.sub(_replace_single, text)
    return text


# ---------------------------------------------------------------------------
# Structure formatting helpers
# ---------------------------------------------------------------------------

def _has_bullet_markers(text: str) -> bool:
    """Return True if text contains at least 2 spoken bullet-list markers."""
    bullet_count = len(_BULLET_ITEM.findall(text))
    dash_count = len(_DASH_ITEM.findall(text))
    return bullet_count >= 2 or dash_count >= 2


def _has_numbered_markers(text: str) -> bool:
    """Return True if text contains spoken numbered-list markers."""
    return bool(
        _NUMBER_WORD_ITEM.search(text)
        or _NUMBER_DIGIT_ITEM.search(text)
        or _ORDINAL_ITEM.search(text)
        or _DIGIT_DOT_ITEM.search(text)
        or _CARDINAL_PAREN_ITEM.search(text)
    )


def _format_bullet_list(text: str) -> str:
    """Convert spoken bullet markers into formatted bullet list."""
    # Split on bullet markers
    parts = _BULLET_ITEM.split(text)
    # Also split on "dash" and "next item"
    expanded = []
    for part in parts:
        sub = _DASH_ITEM.split(part)
        for s in sub:
            expanded.extend(_NEXT_ITEM.split(s))

    items = [p.strip().rstrip(",").strip() for p in expanded if p and p.strip()]
    if not items:
        return text

    if len(items) == 1:
        return text

    result_lines = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        # Sentence-case each item
        item = item[0].upper() + item[1:] if item else item
        # Remove trailing period for list items (we won't add one)
        item = item.rstrip(".")
        result_lines.append(f"- {item}")

    return "\n".join(result_lines)


def _format_numbered_list(text: str) -> str:
    """Convert spoken number markers into formatted numbered list."""
    items: list[tuple[int, str]] = []

    # Try "number <word>" pattern
    chunks = _NUMBER_WORD_ITEM.split(text)
    if len(chunks) > 1:
        # chunks = [preamble, "one", content1, "two", content2, ...]
        preamble = chunks[0].strip()
        result_parts = []
        if preamble:
            result_parts.append(preamble)
        i = 1
        while i < len(chunks) - 1:
            num_word = chunks[i].lower()
            content = chunks[i + 1].strip().rstrip(",").strip()
            num = _CARDINAL_MAP.get(num_word, num_word)
            if content:
                content = content[0].upper() + content[1:]
                content = content.rstrip(".")
                items.append((int(num), content))
            i += 2
        if items:
            if preamble:
                lines = [preamble]
            else:
                lines = []
            for num, content in items:
                lines.append(f"{num}. {content}")
            return "\n".join(lines)

    # Try "number <digit>" pattern
    chunks = _NUMBER_DIGIT_ITEM.split(text)
    if len(chunks) > 1:
        preamble = chunks[0].strip()
        i = 1
        while i < len(chunks) - 1:
            num = chunks[i]
            content = chunks[i + 1].strip().rstrip(",").strip()
            if content:
                content = content[0].upper() + content[1:]
                content = content.rstrip(".")
                items.append((int(num), content))
            i += 2
        if items:
            lines = [preamble] if preamble else []
            for num, content in items:
                lines.append(f"{num}. {content}")
            return "\n".join(lines)

    # Try ordinal pattern ("first ... second ... third ...")
    chunks = _ORDINAL_ITEM.split(text)
    if len(chunks) > 2:  # need at least 2 ordinals
        preamble = chunks[0].strip()
        i = 1
        counter = 0
        while i < len(chunks) - 1:
            ord_word = chunks[i].lower()
            content = chunks[i + 1].strip().rstrip(",").strip()
            num = _ORDINAL_MAP.get(ord_word)
            if num and content:
                counter += 1
                content = content[0].upper() + content[1:]
                content = content.rstrip(".")
                items.append((int(num), content))
            i += 2
        if items and len(items) >= 2:
            lines = [preamble] if preamble else []
            for num, content in items:
                lines.append(f"{num}. {content}")
            return "\n".join(lines)

    # Try "one) ... two) ..." pattern
    chunks = _CARDINAL_PAREN_ITEM.split(text)
    if len(chunks) > 1:
        preamble = chunks[0].strip()
        i = 1
        while i < len(chunks) - 1:
            num_word = chunks[i].lower()
            content = chunks[i + 1].strip().rstrip(",").strip()
            num = _CARDINAL_MAP.get(num_word, num_word)
            if content:
                content = content[0].upper() + content[1:]
                content = content.rstrip(".")
                items.append((int(num), content))
            i += 2
        if items:
            lines = [preamble] if preamble else []
            for num, content in items:
                lines.append(f"{num}. {content}")
            return "\n".join(lines)

    # Try "1. text  2. text" already-formatted patterns
    chunks = _DIGIT_DOT_ITEM.split(text)
    if len(chunks) > 2:
        preamble = chunks[0].strip()
        i = 1
        while i < len(chunks) - 1:
            num = chunks[i]
            content = chunks[i + 1].strip().rstrip(",").strip()
            if content:
                content = content[0].upper() + content[1:]
                content = content.rstrip(".")
                items.append((int(num), content))
            i += 2
        if items and len(items) >= 2:
            lines = [preamble] if preamble else []
            for num, content in items:
                lines.append(f"{num}. {content}")
            return "\n".join(lines)

    return text


# ---------------------------------------------------------------------------
# Paragraph / line-break processing
# ---------------------------------------------------------------------------

def _process_paragraph_commands(text: str) -> str:
    """Replace spoken paragraph/line commands with actual whitespace."""
    text = _PERIOD_NEW_PARA.sub(".\n\n", text)
    text = _NEW_PARAGRAPH.sub("\n\n", text)
    text = _NEW_LINE.sub("\n", text)
    return text


# ---------------------------------------------------------------------------
# Core cleanup stages
# ---------------------------------------------------------------------------

def _normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces (but preserve explicit newlines)."""
    lines = text.split("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    # Collapse more than 2 consecutive blank lines to 2
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _remove_repeated_words(text: str) -> str:
    """Collapse immediate repeated words: 'the the' -> 'the'."""
    return re.sub(r"\b(\w+)(\s+\1)+\b", r"\1", text, flags=re.IGNORECASE)


def _remove_false_starts(text: str) -> str:
    """Remove repeated short phrases: 'I was I was going' -> 'I was going'."""
    return re.sub(
        r"\b(\w+(?:\s+\w+)?)\s+\1\b", r"\1", text, flags=re.IGNORECASE
    )


def _remove_fillers(text: str) -> str:
    """Strip filler words with surrounding punctuation/whitespace."""
    text = FILLER_PATTERN.sub(" ", text)
    # Context-aware "like" removal: protect comparison/verb uses, strip filler.
    text = _LIKE_PROTECT.sub(lambda m: m.group(1) + " " + _LIKE_SENTINEL, text)
    text = _LIKE_FILLER.sub(" ", text)
    text = text.replace(_LIKE_SENTINEL, "like")
    return text


def _sentence_case(text: str) -> str:
    """Capitalize the first letter of each sentence in the text."""
    if not text:
        return text

    def _cap_after_break(t: str) -> str:
        # Capitalize after sentence-ending punctuation
        result = re.sub(
            r'([.!?])\s+([a-z])',
            lambda m: m.group(1) + " " + m.group(2).upper(),
            t,
        )
        return result

    # Capitalize first character of each paragraph
    lines = text.split("\n")
    processed = []
    for line in lines:
        line = line.strip()
        if line:
            line = line[0].upper() + line[1:]
            line = _cap_after_break(line)
        processed.append(line)

    return "\n".join(processed)


def _ensure_terminal_punctuation(text: str) -> str:
    """Add period at end if no sentence-ending punctuation present."""
    if not text:
        return text
    # Process each line for list items
    lines = text.split("\n")
    processed = []
    for line in lines:
        stripped = line.rstrip()
        if stripped and stripped.startswith(("- ", "* ")):
            # Don't force punctuation on bullet items
            processed.append(stripped)
        elif stripped and re.match(r"^\d+\.\s", stripped):
            # Don't force punctuation on numbered list items
            processed.append(stripped)
        elif stripped and stripped[-1] not in ".!?":
            processed.append(stripped + ".")
        else:
            processed.append(stripped)
    return "\n".join(processed)


def _stronger_punctuation_smoothing(text: str) -> str:
    """Fix common punctuation issues from speech-to-text."""
    # Remove double periods
    text = re.sub(r"\.{2,}", ".", text)
    # Fix space before punctuation
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)
    # Fix missing space after punctuation (but not in numbers like 3.14 or URLs)
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)
    # Fix comma-period combo
    text = re.sub(r",\.", ".", text)
    text = re.sub(r"\.,", ",", text)
    return text


# ---------------------------------------------------------------------------
# Token preservation (URLs, emails, code-like tokens)
# ---------------------------------------------------------------------------

_PRESERVE_PATTERN = re.compile(
    r"(?:https?://\S+|www\.\S+|\S+@\S+\.\S+|`[^`]+`)"
)


def _extract_preserved(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace preserved tokens with placeholders; return modified text
    and mapping of placeholder->original."""
    tokens: list[tuple[str, str]] = []
    counter = 0

    def _replace(m: re.Match) -> str:
        nonlocal counter
        placeholder = f"\x00PRESERVE{counter}\x00"
        tokens.append((placeholder, m.group(0)))
        counter += 1
        return placeholder

    modified = _PRESERVE_PATTERN.sub(_replace, text)
    return modified, tokens


def _restore_preserved(text: str, tokens: list[tuple[str, str]]) -> str:
    """Put preserved tokens back."""
    for placeholder, original in tokens:
        text = text.replace(placeholder, original)
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_text(text: str, level: int = 1) -> str:
    """Apply cleanup rules based on slider level.

    Args:
        text: Raw transcript text.
        level: Cleanup aggressiveness (0=Light, 1=Moderate, 2=Aggressive).

    Returns:
        Cleaned text. Falls back to stripped raw text if cleaning would
        produce empty output.
    """
    if not text or not text.strip():
        return ""

    raw = text.strip()
    level = max(0, min(2, level))

    # Preserve URLs, emails, code tokens from destructive cleanup
    result, preserved = _extract_preserved(raw)

    # --- All levels: paragraph/line-break commands ---
    result = _process_paragraph_commands(result)

    # --- All levels: proper noun capitalization ---
    result = _capitalize_proper_nouns(result)

    # --- Level 0 (Light) ---
    result = _normalize_whitespace(result)
    result = _remove_repeated_words(result)

    # --- Level 1+ (Moderate) ---
    if level >= 1:
        result = _remove_fillers(result)

        # List formatting (only at moderate+)
        # Check for list markers before normalizing them away
        if _has_bullet_markers(result):
            result = _format_bullet_list(result)
        elif _has_numbered_markers(result):
            result = _format_numbered_list(result)

    # --- Level 2 (Aggressive) ---
    if level >= 2:
        result = _remove_false_starts(result)
        result = _stronger_punctuation_smoothing(result)

    # --- All levels: final touches ---
    result = _normalize_whitespace(result)
    result = _sentence_case(result)
    result = _ensure_terminal_punctuation(result)

    # Restore preserved tokens
    result = _restore_preserved(result, preserved)

    # Safety: never output empty when raw had content
    if not result.strip():
        return raw

    return result
