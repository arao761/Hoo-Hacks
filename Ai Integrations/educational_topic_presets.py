"""Curated structured prompts for testing and demo — tuned for clarity with the shared template."""

from __future__ import annotations

from structured_image_prompt import StructuredImagePrompt

# Shared negatives: T2I loves fake text — tell it explicitly to back off.
_CLARITY_NEGATIVE = (
    "blurry, low resolution, watermark, logo, qr code, text, letters, words, typography, "
    "caption, subtitle, lorem ipsum, gibberish font, illegible text, tiny fonts, "
    "crowded composition, multiple unrelated scenes, photorealistic blood or gore, "
    "nsfw, distorted anatomy, extra limbs, mangled hands, chartjunk, busy 3d glass tubes"
)


def get_preset(slug: str) -> StructuredImagePrompt:
    key = slug.strip().lower().replace(" ", "_")
    if key not in PRESETS:
        raise KeyError(f"unknown topic preset {slug!r}; try one of {sorted(PRESETS)}")
    return PRESETS[key]


PRESETS: dict[str, StructuredImagePrompt] = {
    "photosynthesis": StructuredImagePrompt(
        topic="Photosynthesis",
        scene_description=(
            "Wordless children's science book painting: one large green leaf fills most of the frame, "
            "soft sunlight from upper left, visible veins and round chloroplast-like dots inside the leaf. "
            "Tiny pale blue dots drift toward the leaf edge; tiny bright bubbles drift away — purely visual metaphor, "
            "no arrows with tails that could become fake text, no boxes."
        ),
        visual_style=(
            "Flat gouache / print illustration, matte paper texture, gentle gradients, not a 3D render, "
            "not an infographic layout, not glass or plastic tubes"
        ),
        educational_framing=(
            "Composition only: sun + leaf + subtle particle motion; large empty margin so the product UI can show "
            "real English labels later. No glyphs, no pseudo-chemistry strings."
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
    "black_holes": StructuredImagePrompt(
        topic="Black holes and event horizons",
        scene_description=(
            "Cross-section diagram beside a stylized accretion disk: central dark sphere (event horizon), "
            "bent light paths as curved guide lines, distant stars as small points — conceptual not Hollywood."
        ),
        visual_style=(
            "NASA-explainer aesthetic: deep blues and purples, thin white line art, high contrast, "
            "minimal glow, clean negative space — purely visual, no annotations"
        ),
        educational_framing=(
            "Distinguish parts by shape: dark central disk, bright ring, bent light as thin curved guides; "
            "optional small inset with grid-sheet metaphor using warped grid lines only — zero text."
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
    "world_war_ii": StructuredImagePrompt(
        topic="World War II — European theater overview (1940s)",
        scene_description=(
            "Simplified map of Europe with neutral tones: arrows for major fronts, "
            "small ship/plane icons as abstract symbols (no battle gore), timeline strip along bottom."
        ),
        visual_style=(
            "Academic map infographic: parchment or muted paper palette, crisp borders, "
            "restrained iconography — no legend text, use three muted fill colors for sides only"
        ),
        educational_framing=(
            "Three territory tints (e.g. gray / tan / neutral) and arrow directions only; "
            "small abstract ship and plane icons; empty margin at top for UI caption later; no graphic violence"
        ),
        negative_prompt=_CLARITY_NEGATIVE + ", swastikas, hate symbols, graphic violence, war photography",
        aspect_ratio="16:9",
    ),
    "dna_replication": StructuredImagePrompt(
        topic="DNA replication (semi-conservative model)",
        scene_description=(
            "Double helix opening at a replication fork: two daughter strands forming, "
            "enzymes as simple colored blobs (not molecular ball-and-stick soup, no base letters on the image)."
        ),
        visual_style=(
            "Clean biology diagram: four distinct pastel colors for base pairs (no A/T/C/G glyphs), "
            "white background, bold outlines, consistent scale between parent and daughter strands"
        ),
        educational_framing=(
            "Use fork geometry and arrow direction along strands; lagging side shows short fragment dashes; "
            "no words — color distinguishes old vs new strand if helpful"
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
    "semiconductor_chips": StructuredImagePrompt(
        topic="Semiconductor chips — from sand to silicon wafer to packaged CPU",
        scene_description=(
            "Left-to-right flow diagram: silicon crystal → wafer disc → lithography pattern (abstract grids) "
            "→ finished chip package; icons simple and aligned on a baseline."
        ),
        visual_style=(
            "Tech explainer infographic: slate and silver palette, cyan accents, "
            "isometric-lite icons, plenty of whitespace between steps"
        ),
        educational_framing=(
            "Four equal-width stages left-to-right: crystal chunk, wafer disc, grid pattern square, packaged chip; "
            "connect with a simple horizontal path; no titles or numerals in-image — schematic only"
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
    "mitosis": StructuredImagePrompt(
        topic="Mitosis — stages of cell division",
        scene_description=(
            "Horizontal strip of six panels (interphase → telophase): one cell silhouette per stage, "
            "chromosomes as distinct X shapes, spindle as thin lines, cytokinesis in final panel."
        ),
        visual_style=(
            "High-school biology poster: flat color fills, white background, consistent cell size, "
            "strong panel dividers"
        ),
        educational_framing=(
            "Six panels left-to-right; same chromosome color in every panel; spindle as thin lines; "
            "distinct cell outlines per stage — no stage titles in the image"
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
    "water_cycle": StructuredImagePrompt(
        topic="The water cycle",
        scene_description=(
            "Circular diagram: ocean/lake at bottom, sun and evaporation arrows up, cloud formation, "
            "rain over mountains, runoff/rivers returning to sea — continuous loop."
        ),
        visual_style=(
            "Friendly but precise textbook diagram: soft sky blues, green land, simple textures, "
            "no photoreal storm chaos"
        ),
        educational_framing=(
            "Circular flow with arrows only; vary arrow color along the loop (e.g. rising vs falling vs surface); "
            "no words — clouds, rain streaks, and river shape carry meaning"
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="1:1",
    ),
    "newtons_laws": StructuredImagePrompt(
        topic="Newton’s laws of motion — forces on objects",
        scene_description=(
            "Three small vignettes on one canvas: (1) ball at rest vs pushed, (2) cart with equal/opposite arrows, "
            "(3) skateboarder + wall with action/reaction arrows — simple blocks and spheres."
        ),
        visual_style=(
            "Physics classroom diagram: black vector arrows on light gray grid, bold object silhouettes, "
            "minimal shading"
        ),
        educational_framing=(
            "Three side-by-side vignettes separated by whitespace; equal-and-opposite arrows as matching pairs; "
            "consistent arrowhead style; no letters on arrows or panels — use color pairs to show force pairs"
        ),
        negative_prompt=_CLARITY_NEGATIVE,
        aspect_ratio="16:9",
    ),
}

PRESET_SLUGS: tuple[str, ...] = tuple(sorted(PRESETS))
