import json
import logging
import os
from typing import Any, Dict

from models import OutputType

logger = logging.getLogger("learnlens-gemini")

# ---------------------------------------------------------------------------
# Gemini / Vertex AI call
# ---------------------------------------------------------------------------

_SONG_SYSTEM = """You are an expert educational content creator who specialises in music-based learning.
Given a topic, return ONLY a JSON object (no markdown fences) with these keys:
- style: a detailed music style description suitable for an AI music generator (instruments, tempo, genre, energy)
- mood: emotional tone of the song
- lyrics_brief: 3-4 sentences of concrete lyrics content — key facts, a memorable chorus hook, and a closing line
- music_prompt: a single richly-detailed paragraph (80-120 words) written as a direct instruction to an AI music model; include instruments, tempo BPM estimate, genre, and educational feel
All field values MUST be written in the requested target language. Keep JSON keys in English.
"""

_VIDEO_SYSTEM = """You are an expert scriptwriter for short educational explainer videos.
Given a topic, return ONLY a JSON object (no markdown fences) with these keys:
- style: visual/narrative style (e.g. "animated explainer with warm colours")
- scenes: array of exactly 4 scene objects, each with:
    - title: short scene heading (5 words max)
    - visual: one sentence describing what is shown on screen
    - narration: 2-3 natural, conversational sentences of spoken narration for that scene (good for text-to-speech)
- full_narration: a single flowing 150-200 word narration script that covers the whole topic engagingly, written for text-to-speech delivery
All field values MUST be written in the requested target language. Keep JSON keys in English.
"""

_SONG_USER = (
    "Topic: {topic}\n"
    "Target language code: {language_code}\n"
    "Target language name: {language_name}\n\n"
    "Generate a rich, engaging educational song structure for this topic in the target language."
)
_VIDEO_USER = (
    "Topic: {topic}\n"
    "Target language code: {language_code}\n"
    "Target language name: {language_name}\n\n"
    "Generate a compelling educational video script in the target language."
)

_LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "zh": "Chinese",
    "hi": "Hindi",
    "de": "German",
    "it": "Italian",
}

_LOCALIZE_SYSTEM = """You are a localization engine for educational media prompts.
Translate ONLY the JSON values into the requested target language.
Do NOT translate JSON keys.
Do NOT change structure, field names, or array lengths.
Return ONLY valid JSON with the exact same shape.
"""

_LOCALIZE_USER = (
    "Target language code: {language_code}\n"
    "Target language name: {language_name}\n"
    "Output type: {output_type}\n\n"
    "Translate this JSON's values only:\n"
    "{payload_json}"
)


def _normalize_language(language: str | None) -> str:
    code = (language or "en").strip().lower()
    if code in _LANGUAGE_NAMES:
        return code
    return "en"


def _call_gemini(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call Gemini 2.0 Flash via the REST API directly using httpx."""
    import httpx

    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }

    resp = httpx.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown fences if the model wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ---------------------------------------------------------------------------
# Rich fallback templates (used when Gemini is unavailable)
# ---------------------------------------------------------------------------

def _song_fallback(topic: str, language: str = "en") -> Dict[str, Any]:
    lang = _normalize_language(language)
    language_name = _LANGUAGE_NAMES.get(lang, "English")

    song_text = {
        "en": {
            "style": "upbeat acoustic-pop educational song with piano and light percussion",
            "mood": "encouraging and clear",
            "lyrics": f"Verse 1 explains what {topic} is and why it matters. Chorus repeats one memorable key fact about {topic}. Verse 2 gives a simple step-by-step understanding. Ending recap reinforces the main takeaway.",
        },
        "es": {
            "style": "cancion educativa pop acustica alegre con piano y percusion suave",
            "mood": "motivador y claro",
            "lyrics": f"La primera estrofa explica que es {topic} y por que importa. El coro repite una idea clave facil de recordar sobre {topic}. La segunda estrofa muestra el proceso paso a paso. El cierre resume lo mas importante.",
        },
        "de": {
            "style": "fröhlicher akustischer Bildungs-Pop mit Klavier und leichter Percussion",
            "mood": "klar und motivierend",
            "lyrics": f"Die erste Strophe erklaert, was {topic} ist und warum es wichtig ist. Der Refrain wiederholt eine zentrale Kernidee zu {topic}. Die zweite Strophe erklaert den Ablauf in einfachen Schritten. Am Ende folgt eine kurze Zusammenfassung.",
        },
        "it": {
            "style": "canzone educativa pop acustica energica con pianoforte e percussioni leggere",
            "mood": "chiaro e coinvolgente",
            "lyrics": f"La prima strofa spiega che cos e {topic} e perche e importante. Il ritornello ripete un concetto chiave facile da ricordare su {topic}. La seconda strofa descrive il processo passo dopo passo. La chiusura riassume i punti principali.",
        },
        "zh": {
            "style": "轻快的教育流行风格，钢琴和轻打击乐",
            "mood": "清晰、积极、易记",
            "lyrics": f"第一段介绍什么是{topic}以及它为什么重要。副歌重复一个关于{topic}的关键知识点，方便记忆。第二段用简单步骤解释其运作方式。结尾做简短回顾，强化核心概念。",
        },
        "hi": {
            "style": "उत्साही शैक्षिक पॉप शैली, पियानो और हल्की ताल",
            "mood": "स्पष्ट और प्रेरक",
            "lyrics": f"पहला अंतरा बताता है कि {topic} क्या है और यह क्यों महत्वपूर्ण है। कोरस {topic} का एक मुख्य बिंदु यादगार तरीके से दोहराता है। दूसरा अंतरा प्रक्रिया को आसान चरणों में समझाता है। अंत में संक्षेप में मुख्य बात दोहराई जाती है।",
        },
    }[lang]

    return {
        "type": "song",
        "style": song_text["style"],
        "mood": song_text["mood"],
        "lyrics_brief": song_text["lyrics"],
        "music_prompt": (
            f"Create an educational song about {topic}. "
            f"Style: {song_text['style']}. Mood: {song_text['mood']}. "
            f"Lyrics theme: {song_text['lyrics']}. "
            f"Write lyrics in {language_name}."
        ),
    }


def _video_fallback(topic: str, language: str = "en") -> Dict[str, Any]:
    lang = _normalize_language(language)
    language_name = _LANGUAGE_NAMES.get(lang, "English")

    scene_text = {
        "en": {
            "titles": ["What is", "Why It Matters", "How It Works", "Quick Recap"],
            "intro": f"Have you ever wondered about {topic}? Today we break it down simply.",
            "why": f"{topic} matters because it appears in real situations around us.",
            "how": f"Let's go step by step to understand how {topic} works.",
            "recap": f"Quick recap: {topic} has key ideas you can now explain clearly.",
            "full": f"Welcome! Today we are learning about {topic}. We start with the core idea and why it matters. Next, we walk through the process in simple steps so each part is easy to remember. Finally, we review the main points so you can explain {topic} confidently.",
            "style": "friendly animated explainer with clear narration and warm colors",
        },
        "es": {
            "titles": ["Que es", "Por que importa", "Como funciona", "Resumen rapido"],
            "intro": f"Hoy vamos a aprender sobre {topic} de forma clara y sencilla.",
            "why": f"{topic} es importante porque aparece en situaciones reales todos los dias.",
            "how": f"Ahora veremos paso a paso como funciona {topic}.",
            "recap": f"Resumen rapido: ya conoces las ideas clave de {topic}.",
            "full": f"Bienvenidos. Hoy aprenderemos sobre {topic}. Primero veremos la idea principal y por que es importante. Despues explicaremos el proceso en pasos simples para que sea facil recordarlo. Al final haremos un resumen para reforzar los puntos clave y que puedas explicar {topic} con confianza.",
            "style": "video educativo animado, cercano y claro",
        },
        "de": {
            "titles": ["Was ist", "Warum es wichtig ist", "So funktioniert es", "Kurze Zusammenfassung"],
            "intro": f"Heute lernen wir {topic} klar und einfach.",
            "why": f"{topic} ist wichtig, weil es in vielen Alltagssituationen vorkommt.",
            "how": f"Nun schauen wir uns Schritt fuer Schritt an, wie {topic} funktioniert.",
            "recap": f"Kurze Zusammenfassung: Du kennst jetzt die wichtigsten Punkte zu {topic}.",
            "full": f"Willkommen. Heute geht es um {topic}. Zuerst klaeren wir die Grundidee und warum sie wichtig ist. Danach betrachten wir den Ablauf in einfachen Schritten, damit alles leicht nachvollziehbar ist. Zum Schluss wiederholen wir die Kernpunkte, damit du {topic} sicher erklaeren kannst.",
            "style": "freundlicher animierter Erklaervideo-Stil mit klarer Sprache",
        },
        "it": {
            "titles": ["Che cos e", "Perche e importante", "Come funziona", "Riepilogo veloce"],
            "intro": f"Oggi impariamo {topic} in modo semplice e chiaro.",
            "why": f"{topic} e importante perche compare in molte situazioni reali.",
            "how": f"Adesso vediamo passo dopo passo come funziona {topic}.",
            "recap": f"Riepilogo veloce: ora conosci i concetti principali di {topic}.",
            "full": f"Benvenuti. Oggi studiamo {topic}. Iniziamo dall idea principale e dal motivo per cui e importante. Poi analizziamo il processo in passaggi semplici, cosi da ricordarlo facilmente. Infine facciamo un breve riepilogo dei punti chiave per spiegare {topic} con sicurezza.",
            "style": "video educativo animato, amichevole e chiaro",
        },
        "zh": {
            "titles": ["什么是", "为什么重要", "如何运作", "快速回顾"],
            "intro": f"今天我们用简单清晰的方式学习{topic}。",
            "why": f"{topic}很重要，因为它在现实生活中经常出现。",
            "how": f"接下来我们一步一步看{topic}是如何运作的。",
            "recap": f"快速回顾：你已经掌握了{topic}的核心要点。",
            "full": f"欢迎来到今天的课程。我们将学习{topic}。先理解核心概念以及它为什么重要，然后用简单步骤讲清楚它的运行过程。最后做简要总结，帮助你自信地解释{topic}。",
            "style": "友好、清晰的动画讲解风格",
        },
        "hi": {
            "titles": ["क्या है", "यह क्यों महत्वपूर्ण है", "यह कैसे काम करता है", "त्वरित पुनरावलोकन"],
            "intro": f"आज हम {topic} को आसान और स्पष्ट तरीके से सीखेंगे।",
            "why": f"{topic} महत्वपूर्ण है क्योंकि यह वास्तविक जीवन में अक्सर दिखाई देता है।",
            "how": f"अब हम चरण दर चरण समझेंगे कि {topic} कैसे काम करता है।",
            "recap": f"संक्षेप में: अब आप {topic} के मुख्य विचार समझ चुके हैं।",
            "full": f"स्वागत है। आज का विषय {topic} है। पहले हम इसकी मूल अवधारणा और महत्व समझेंगे। फिर सरल चरणों में इसकी प्रक्रिया देखेंगे ताकि इसे याद रखना आसान हो। अंत में मुख्य बिंदुओं का पुनरावलोकन करेंगे ताकि आप {topic} को आत्मविश्वास से समझा सकें।",
            "style": "मित्रवत और स्पष्ट एनिमेटेड शैक्षिक शैली",
        },
    }[lang]

    return {
        "type": "video",
        "style": scene_text["style"],
        "scenes": [
            {
                "title": f"{scene_text['titles'][0]} {topic}",
                "visual": f"Bold title card with the words '{topic}' and a simple illustrative icon.",
                "narration": scene_text["intro"],
            },
            {
                "title": scene_text["titles"][1],
                "visual": f"Animated diagram showing the real-world impact of {topic}.",
                "narration": scene_text["why"],
            },
            {
                "title": scene_text["titles"][2],
                "visual": f"Step-by-step animated breakdown of the core mechanism behind {topic}.",
                "narration": scene_text["how"],
            },
            {
                "title": scene_text["titles"][3],
                "visual": "Three bullet-point summary cards appearing one by one.",
                "narration": scene_text["recap"],
            },
        ],
        "full_narration": scene_text["full"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def expand_topic_with_gemini(topic: str, output_type: OutputType, language: str = "en") -> Dict[str, Any]:
    """
    Use Gemini to generate a rich structured prompt for song or video generation.
    Falls back to improved static templates if Gemini is unavailable.
    """
    lang_code = _normalize_language(language)
    lang_name = _LANGUAGE_NAMES[lang_code]

    if output_type is OutputType.song:
        try:
            result = _call_gemini(
                _SONG_SYSTEM,
                _SONG_USER.format(topic=topic, language_code=lang_code, language_name=lang_name),
            )
            result["type"] = "song"
            result["language"] = lang_code
            logger.info("Gemini song prompt generated for: %s", topic)
            return result
        except Exception as exc:
            logger.warning("Gemini unavailable for song prompt (%s); using fallback.", exc)
            result = _song_fallback(topic, language=lang_code)
            result["language"] = lang_code
            return result

    # video
    try:
        result = _call_gemini(
            _VIDEO_SYSTEM,
            _VIDEO_USER.format(topic=topic, language_code=lang_code, language_name=lang_name),
        )
        result["type"] = "video"
        result["language"] = lang_code
        logger.info("Gemini video prompt generated for: %s", topic)
        return result
    except Exception as exc:
        logger.warning("Gemini unavailable for video prompt (%s); using fallback.", exc)
        result = _video_fallback(topic, language=lang_code)
        result["language"] = lang_code
        return result


def localize_prompt_struct(
    prompt_struct: Dict[str, Any],
    *,
    output_type: OutputType,
    language: str,
) -> Dict[str, Any]:
    """
    Ensure prompt values are in the requested target language.
    Uses Gemini as a value-only JSON localization pass.
    Falls back to original prompt_struct on any error.
    """
    lang_code = _normalize_language(language)
    if lang_code == "en":
        return prompt_struct

    lang_name = _LANGUAGE_NAMES[lang_code]
    try:
        localized = _call_gemini(
            _LOCALIZE_SYSTEM,
            _LOCALIZE_USER.format(
                language_code=lang_code,
                language_name=lang_name,
                output_type=output_type.value,
                payload_json=json.dumps(prompt_struct, ensure_ascii=False),
            ),
        )
        if isinstance(localized, dict):
            localized["language"] = lang_code
            return localized
    except Exception as exc:  # noqa: BLE001
        logger.warning("Localization pass failed (%s); using original prompt values.", exc)

    return prompt_struct
