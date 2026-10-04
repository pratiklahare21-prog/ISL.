"""
Single source of truth for sign labels on the Python side.

IMPORTANT: This list must stay in sync with
packages/shared/src/constants/signs.ts (ALL_SIGN_LABELS). If you add or
remove a label here, update that file too, and vice versa — the model's
output layer size and the dataset tool both depend on this exact order
and count.
"""

ALPHABET_SIGNS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
DIGIT_SIGNS = [str(d) for d in range(10)]

WORD_SIGNS = [
    "HELLO",
    "THANK_YOU",
    "PLEASE",
    "YES",
    "NO",
    "SORRY",
    "HELP",
    "WATER",
    "FOOD",
    "NAME",
    "HOW_ARE_YOU",
    "GOOD",
    "BAD",
    "STOP",
    "GO",
    "COME",
    "WAIT",
    "UNDERSTAND",
    "NOT_UNDERSTAND",
    "MY",
    "YOU",
    "WHERE",
    "WHAT",
    "WHEN",
    "TOILET",
    "HOME",
    "SCHOOL",
    "WORK",
    "FRIEND",
    "FAMILY",
]

ALL_SIGN_LABELS = ALPHABET_SIGNS + DIGIT_SIGNS + WORD_SIGNS

# Static signs = single hand-shape, classified frame-by-frame (fast path).
# Dynamic signs = motion over a window of frames, need the sequence model.
STATIC_SIGNS = set(ALPHABET_SIGNS + DIGIT_SIGNS)
DYNAMIC_SIGNS = set(WORD_SIGNS)

LABEL_TO_INDEX = {label: i for i, label in enumerate(ALL_SIGN_LABELS)}
INDEX_TO_LABEL = {i: label for i, label in enumerate(ALL_SIGN_LABELS)}

NUM_CLASSES = len(ALL_SIGN_LABELS)
