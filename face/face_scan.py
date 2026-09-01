"""InsightFace wrapper — face detection + 512-d embedding extraction.

Initialises the ``FaceAnalysis`` pipeline **once** (lazy singleton) so
repeated calls reuse the same ONNX sessions and model weights.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

# ── lazy singleton ─────────────────────────────────────────────────────
_app = None                           # type: ignore[assignment]


def _get_app():
    """Initialise FaceAnalysis once, on first call."""
    global _app
    if _app is not None:
        return _app

    from insightface.app import FaceAnalysis

    _app = FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    # ctx_id < 0  → CPU;  det_size None → Auto (128 + 640 dual pass)
    _app.prepare(ctx_id=-1, det_size=None)
    return _app


# ── public API ─────────────────────────────────────────────────────────

def get_face_embedding(
    image_input,
    *,
    select: str = "largest",
) -> Tuple[np.ndarray, Dict]:
    """Detect the most prominent face and return its embedding.

    Parameters
    ----------
    image_input:
        File-system path (``str | Path``) **or** a BGR ``numpy`` array
        already loaded by OpenCV.
    select:
        ``"largest"`` picks the face with the biggest bounding-box area
        (default).  ``"first"`` picks the highest-confidence detection.

    Returns
    -------
    (embedding, metadata)
        *embedding* — 512-dim L2-normalised ``float32`` vector.
        *metadata*  — dict with ``bbox``, ``det_score``, ``age``,
        ``gender``, ``num_faces``.

    Raises
    ------
    FileNotFoundError – image path does not exist.
    ValueError        – no face detected.
    """
    img = _load_image(image_input)
    app = _get_app()
    faces = app.get(img)

    if not faces:
        raise ValueError(
            "No face detected. Use a clear, front-facing photo with "
            "adequate lighting."
        )

    face = _pick_face(faces, select)
    emb: np.ndarray = face.normed_embedding          # already L2-normed

    meta: Dict = {
        "bbox": face.bbox.tolist(),
        "det_score": round(float(face.det_score), 4),
        "age": int(face.age) if face.age is not None else None,
        "gender": face.sex if face.sex is not None else None,
        "num_faces": len(faces),
    }
    return emb, meta


def save_annotated_image(
    image_input,
    output_path: str,
) -> str:
    """Draw bounding boxes on all detected faces and write the result.

    Returns the *output_path* for convenience.
    """
    img = _load_image(image_input)
    app = _get_app()
    faces = app.get(img)
    drawn = app.draw_on(img, faces)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, drawn)
    return output_path


# ── internal helpers ───────────────────────────────────────────────────

def _load_image(src) -> np.ndarray:
    """Accept a path *or* an already-loaded ndarray."""
    if isinstance(src, np.ndarray):
        return src
    path = str(src)
    if not Path(path).is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"OpenCV could not decode: {path}")
    return img


def _pick_face(faces: list, mode: str):
    """Select one face from the detection list."""
    if mode == "largest":
        return max(faces, key=lambda f: _bbox_area(f.bbox))
    # default: highest confidence (list is already sorted by det_model)
    return faces[0]


def _bbox_area(bbox) -> float:
    x1, y1, x2, y2 = bbox[:4]
    return max(0.0, float(x2 - x1)) * max(0.0, float(y2 - y1))
