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


def get_all_face_embeddings(image_input) -> List[np.ndarray]:
    """Return L2-normalised embeddings for ALL detected faces.

    Used for multi-face candidate scoring — when a candidate image
    contains a group photo, we compare against every face and take
    the best match instead of just the largest face.

    Returns an empty list if no faces are detected (no exception).
    """
    img = _load_image(image_input)
    app = _get_app()
    faces = app.get(img)
    return [f.normed_embedding for f in faces if f.normed_embedding is not None]


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


def crop_and_save_face(
    image_input,
    output_path: str,
    *,
    select: str = "largest",
    margin_ratio: float = 0.5
) -> str:
    """Crop the selected face with a margin and save it.
    
    This forces search engines to focus on the face rather than the background.
    """
    img = _load_image(image_input)
    app = _get_app()
    faces = app.get(img)

    if not faces:
        raise ValueError("No face detected to crop.")

    face = _pick_face(faces, select)
    x1, y1, x2, y2 = face.bbox[:4]
    
    w = x2 - x1
    h = y2 - y1
    
    # Add margin
    margin_w = w * margin_ratio
    margin_h = h * margin_ratio
    
    img_h, img_w = img.shape[:2]
    
    cx1 = max(0, int(x1 - margin_w))
    cy1 = max(0, int(y1 - margin_h))
    cx2 = min(img_w, int(x2 + margin_w))
    cy2 = min(img_h, int(y2 + margin_h))
    
    cropped = img[cy1:cy2, cx1:cx2]
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, cropped)
    return output_path


# ── internal helpers ───────────────────────────────────────────────────

def _load_image(src) -> np.ndarray:
    """Accept a path *or* an already-loaded ndarray.
    
    Applies preprocessing:
      - EXIF auto-orient (fixes rotated phone photos)
      - CLAHE histogram equalization (improves low-light images)
      - Upscale tiny images to at least 640px on shortest side
    """
    if isinstance(src, np.ndarray):
        return src
    path = str(src)
    if not Path(path).is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    
    # --- EXIF auto-orient ---
    try:
        from PIL import Image
        from PIL.ExifTags import Base as ExifBase
        pil_img = Image.open(path)
        # ImageOps.exif_transpose handles all EXIF rotation cases
        from PIL import ImageOps
        pil_img = ImageOps.exif_transpose(pil_img)
        # Convert PIL -> OpenCV BGR
        import numpy as _np
        img = _np.array(pil_img)
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    except Exception:
        # Fallback to plain OpenCV if PIL fails
        img = cv2.imread(path)
    
    if img is None:
        raise ValueError(f"OpenCV could not decode: {path}")
    
    # --- Upscale tiny images ---
    h, w = img.shape[:2]
    min_dim = min(h, w)
    if min_dim < 640:
        scale = 640 / min_dim
        img = cv2.resize(img, (int(w * scale), int(h * scale)), 
                         interpolation=cv2.INTER_CUBIC)
    
    # --- CLAHE enhancement (adaptive histogram equalization) ---
    try:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    except Exception:
        pass  # Non-critical; continue with unenhanced image
    
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
