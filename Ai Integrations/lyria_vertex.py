"""Google Lyria 2 text-to-music on Vertex AI.

Matches Model Garden / Colab pattern: ``PredictionServiceClient`` with the **global**
API hostname ``aiplatform.googleapis.com`` (not ``{region}-aiplatform.googleapis.com``).
The resource path still includes ``locations/{location}`` (e.g. ``us-central1``).

Docs:
  https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/lyria-music-generation

Environment:
  GOOGLE_CLOUD_PROJECT
  GOOGLE_CLOUD_LOCATION  (e.g. us-central1 — used in the model resource path)
  Optional: VERTEX_AI_PLATFORM_API_ENDPOINT (default: aiplatform.googleapis.com)

Auth: Application Default Credentials.

Output: WAV, 48 kHz, ~30 s instrumental clips per prediction.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

from progress_events import MusicProgressCallback, emit_music_progress

DEFAULT_MODEL = os.environ.get("VERTEX_LYRIA_MODEL", "lyria-002")
# Global endpoint per Google’s Lyria sample (“lyria-002 makes no regionalization guarantees”).
DEFAULT_API_HOST = os.environ.get(
    "VERTEX_AI_PLATFORM_API_ENDPOINT",
    "aiplatform.googleapis.com",
)


@dataclass(frozen=True)
class LyriaMusicResult:
    """One or more clips from a single Lyria request."""

    samples: tuple[bytes, ...]
    mime_type: str
    model: str

    @property
    def audio_bytes(self) -> bytes:
        return self.samples[0]


def _model_endpoint_path(project: str, location: str, model: str) -> str:
    return (
        f"projects/{project}/locations/{location}/publishers/google/models/{model}"
    )


def _prediction_to_dict(pred: Any) -> dict[str, Any]:
    """Gapic may return dict-like MapComposite or protobuf messages."""
    if isinstance(pred, dict):
        return pred
    if isinstance(pred, Mapping):
        return dict(pred)
    return json_format.MessageToDict(pred)


def generate_music_vertex(
    prompt: str,
    *,
    project: Optional[str] = None,
    location: Optional[str] = None,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    sample_count: int = 1,
    timeout_seconds: float = 300.0,
    api_host: Optional[str] = None,
    on_progress: Optional[MusicProgressCallback] = None,
) -> LyriaMusicResult:
    """
    Text-to-music via Lyria. Returns WAV byte strings (one or more, see ``sample_count``).

    API rule: do not pass ``seed`` together with ``sample_count`` > 1.
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    proj = (project or os.environ.get("GOOGLE_CLOUD_PROJECT", "")).strip()
    loc = (location or os.environ.get("GOOGLE_CLOUD_LOCATION", "")).strip()
    if not proj:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set")
    if not loc:
        raise RuntimeError("GOOGLE_CLOUD_LOCATION is not set")

    mid = (model or DEFAULT_MODEL).strip()
    host = (api_host or DEFAULT_API_HOST).strip()

    emit_music_progress(
        on_progress,
        "prompted",
        model=mid,
        prompt_chars=len(prompt.strip()),
    )

    if seed is not None and sample_count > 1:
        raise ValueError("Lyria API: use either seed or sample_count>1, not both")

    instance_dict: dict[str, Any] = {"prompt": prompt.strip()}
    if negative_prompt:
        instance_dict["negative_prompt"] = negative_prompt.strip()
    if seed is not None:
        instance_dict["seed"] = int(seed)

    parameters_dict: dict[str, Any] = {}
    if seed is None and sample_count > 1:
        parameters_dict["sample_count"] = int(sample_count)

    instance = json_format.ParseDict(instance_dict, Value())
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = _model_endpoint_path(proj, loc, mid)

    client = aiplatform.gapic.PredictionServiceClient(
        client_options={"api_endpoint": host},
    )

    emit_music_progress(
        on_progress,
        "generating",
        model=mid,
        endpoint=host,
    )

    response = client.predict(
        endpoint=endpoint,
        instances=[instance],
        parameters=parameters,
        timeout=timeout_seconds,
    )

    raw_preds = list(response.predictions)
    if not raw_preds:
        raise RuntimeError("Lyria returned no predictions")

    emit_music_progress(
        on_progress,
        "decoding",
        model=mid,
        prediction_count=len(raw_preds),
    )

    def _audio_b64_from_prediction(d: dict[str, Any]) -> str | None:
        # Colab samples use audioContent; Vertex predict may return bytesBase64Encoded.
        for key in (
            "audioContent",
            "audio_content",
            "bytesBase64Encoded",
            "bytes_base64_encoded",
        ):
            v = d.get(key)
            if v:
                return v if isinstance(v, str) else str(v)
        return None

    decoded: list[bytes] = []
    mime = "audio/wav"
    for pred in raw_preds:
        d = _prediction_to_dict(pred)
        b64 = _audio_b64_from_prediction(d)
        if not b64:
            keys = ", ".join(sorted(d))
            raise RuntimeError(
                f"Lyria prediction has no known audio base64 field (keys: {keys})"
            )
        decoded.append(base64.b64decode(b64))
        mime = d.get("mimeType") or d.get("mime_type") or mime

    return LyriaMusicResult(samples=tuple(decoded), mime_type=mime, model=mid)
