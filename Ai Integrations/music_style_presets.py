"""Lyria-ready prompts tuned for LearnLens demo genres (US English per Google docs)."""

from __future__ import annotations

from typing import Final

# Shared: instrumental only, no vocals (Lyria is instrumental-first; negative_prompt reinforces).
INSTRUMENTAL_NEGATIVE: Final = (
    "vocals, singing, lyrics, speech, rap, voice, choir, humming"
)


def _neg(extra: str = "") -> str:
    if not extra.strip():
        return INSTRUMENTAL_NEGATIVE
    return f"{INSTRUMENTAL_NEGATIVE}, {extra.strip()}"


STYLE_PRESETS: dict[str, tuple[str, str]] = {
    "educational_jingle": (
        (
            "Short bright educational jingle, major key, catchy simple melody, "
            "acoustic guitar and light glockenspiel or piano, steady 100 bpm, "
            "clean mix, optimistic classroom energy, instrumental only"
        ),
        _neg("heavy metal, dark mood, slow ballad, distorted guitar"),
    ),
    "lo_fi": (
        (
            "Lo-fi study beat, relaxed 82 bpm, dusty rhodes piano chords, soft brushed drums, "
            "warm tape saturation feel, mellow and focused, no lead vocal, instrumental hip-hop groove"
        ),
        _neg("orchestra, epic, loud, aggressive, EDM drops, fast tempo"),
    ),
    "epic_orchestral": (
        (
            "Epic cinematic orchestral piece, slow to medium build, full string section and brass stabs, "
            "timpani and subtle choir pads as texture only (no words), wide hall reverb, "
            "heroic adventure trailer mood, instrumental"
        ),
        _neg("electronic drums, synth bass, lo-fi crackle, vocals, speech, rap"),
    ),
    # Learning-concept beds: genre + teaching context in the prompt (Lyria: US English).
    "science_explorer": (
        (
            "Curious science documentary underscore, medium tempo 96 bpm, sparkling arpeggiated synth "
            "and warm piano, light pulsing bass, sense of discovery and wonder, "
            "clean mix for voiceover about experiments, space, or biology, instrumental only"
        ),
        _neg("vocals, dark horror, heavy metal, chaotic noise, sad minor ballad"),
    ),
    "history_story": (
        (
            "Warm historical narrative underscore, slow to medium 88 bpm, gentle strings and soft harp, "
            "subtle wooden percussion, thoughtful classroom tone for timelines and civilizations, "
            "no period-specific clichés, restrained and clear, instrumental"
        ),
        _neg("EDM, dubstep, aggressive drums, modern trap, vocals, battle sfx"),
    ),
    "math_focus": (
        (
            "Sparse ambient study music, slow steady tempo around 72 bpm, soft sustained pads and mellow electric piano, "
            "gentle understated motion, calm clear headspace for deep work, instrumental only, no percussion hits"
        ),
        _neg("catchy pop hook, loud brass, vocals, speech, chaotic solos, epic trailer"),
    ),
    "language_practice": (
        (
            "Cheerful language-learning bed, bright 100 bpm, light marimba and plucked nylon guitar, "
            "soft claps on two and four, friendly classroom repetition vibe, clear simple harmony, instrumental"
        ),
        _neg("heavy distortion, orchestral epic, slow sad ballad, vocals, rap"),
    ),
    "quiz_energy": (
        (
            "Upbeat quiz-show energy, major key, 118 bpm, punchy indie pop-rock instrumental, "
            "driving drums and bright electric guitar stabs, positive competitive fun for review games, "
            "no announcer voice, instrumental only"
        ),
        _neg("lo-fi crackle, sleepy ambient, funeral march, vocals, speech, dark mood"),
    ),
    "coding_tutorial": (
        (
            "Modern tech tutorial underscore, medium 92 bpm, clean subtle synth plucks and light arpeggio, "
            "soft sidechain pad, focused neutral mood for programming or CS explainers, instrumental electronic"
        ),
        _neg("orchestra fanfare, country twang, vocals, heavy dubstep, chaotic glitch"),
    ),
}

# Original three demo genres (fast smoke).
CORE_STYLE_SLUGS: tuple[str, ...] = (
    "educational_jingle",
    "lo_fi",
    "epic_orchestral",
)

# Extra presets aimed at specific learning contexts.
LEARNING_CONCEPT_STYLE_SLUGS: tuple[str, ...] = (
    "science_explorer",
    "history_story",
    "math_focus",
    "language_practice",
    "quiz_energy",
    "coding_tutorial",
)

STYLE_PRESET_SLUGS: tuple[str, ...] = tuple(sorted(STYLE_PRESETS))


def adapt_style_prompt_for_eleven_music(positive: str, negative: str) -> tuple[str, str | None]:
    """
    Presets are written for Lyria (instrumental). Eleven Music expects sung songs:
    remove anti-vocal negative terms and soften instrumental-only wording in the positive.
    """
    p = positive.strip()
    for old, new in (
        ("instrumental only", "with clear lead vocals and catchy hooks"),
        ("instrumental hip-hop groove", "vocal hip-hop groove"),
        ("no lead vocal, ", ""),
        ("as texture only (no words), ", ""),
        ("heroic adventure trailer mood, instrumental", "heroic adventure trailer mood, with vocals"),
        ("instrumental", "with vocals"),
        ("underscore,", "song—"),
        ("underscore ", "song "),
        ("for voiceover about", "with lyrics about"),
    ):
        p = p.replace(old, new)
    p = (
        f"{p.strip()} Full song with intelligible sung lyrics aligned to the lesson topic; "
        "radio-friendly mix."
    )

    ban_bits = {x.strip().lower() for x in INSTRUMENTAL_NEGATIVE.split(",")}
    neg_parts = [x.strip() for x in negative.split(",") if x.strip()]
    kept = [x for x in neg_parts if x.lower() not in ban_bits]
    neg_out = ", ".join(kept) if kept else None
    return p, neg_out


def get_style_prompt(slug: str) -> tuple[str, str]:
    """
    Return (positive_prompt, negative_prompt) for Lyria.

    Slugs include core demo styles plus ``LEARNING_CONCEPT_STYLE_SLUGS``
    (science, history, math, language, quiz, coding beds).
    """
    key = slug.strip().lower().replace("-", "_")
    if key not in STYLE_PRESETS:
        raise KeyError(
            f"unknown music style {slug!r}; use one of {list(STYLE_PRESETS)}"
        )
    return STYLE_PRESETS[key]
