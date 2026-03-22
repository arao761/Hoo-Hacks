"""Named progress events for worker ↔ WebSocket layer (Person 4).

Lyria has no streaming token progress; events mark logical phases so UIs can show status.
Order for lesson audio + storage:
``prompted`` → ``generating`` → ``decoding`` → ``narrating`` → ``mixing`` → ``uploading`` → ``done``.
Generation-only omits ``uploading`` (and may omit ``narrating``/``mixing`` if no TTS).
"""

from __future__ import annotations

from typing import Any, Callable, Literal, Optional

# Aligns with infra plan: prompted → generating → uploading → done (decoding.inserted for Lyria)
MusicProgressPhase = Literal[
    "prompted",
    "generating",
    "decoding",
    "narrating",
    "mixing",
    "uploading",
    "done",
]

MusicProgressCallback = Callable[[MusicProgressPhase, dict[str, Any]], None]


def emit_music_progress(
    callback: Optional[MusicProgressCallback],
    phase: MusicProgressPhase,
    **payload: Any,
) -> None:
    if callback is None:
        return
    callback(phase, payload)


VideoProgressPhase = Literal[
    "submitted",
    "generating",
    "downloading",
    "merging",
    "uploading",
    "done",
]

VideoProgressCallback = Callable[[VideoProgressPhase, dict[str, Any]], None]


def emit_video_progress(
    callback: Optional[VideoProgressCallback],
    phase: VideoProgressPhase,
    **payload: Any,
) -> None:
    if callback is None:
        return
    callback(phase, payload)
