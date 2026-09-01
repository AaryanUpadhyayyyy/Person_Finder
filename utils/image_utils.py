"""Image I/O helpers — download, upload, resize.

Every function is intentionally small, stateless, and uses streaming
so memory stays flat even for large images.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import requests

from .config import get_config

# ── constants ──────────────────────────────────────────────────────────
_DOWNLOAD_TIMEOUT = 15          # seconds
_UPLOAD_TIMEOUT = 30
_MAX_RETRIES = 2
_CHUNK_SIZE = 8192              # streaming download chunk

_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    """Reuse a single TCP session across all image I/O."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    return _SESSION


# ── download ───────────────────────────────────────────────────────────

def download_image(url: str, *, save_path: Optional[str] = None) -> np.ndarray:
    """Download an image URL and return it as a BGR ``numpy`` array.

    Parameters
    ----------
    url:
        HTTP(S) image URL.
    save_path:
        If given, write the raw bytes to this path as well.

    Returns
    -------
    numpy.ndarray   – OpenCV BGR image.

    Raises
    ------
    ValueError  – non-200 status or corrupt image data.
    """
    sess = _get_session()
    last_err: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = sess.get(url, timeout=_DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()
            buf = io.BytesIO()
            for chunk in resp.iter_content(_CHUNK_SIZE):
                buf.write(chunk)
            raw = buf.getvalue()
            break
        except requests.RequestException as exc:
            last_err = exc
            if attempt == _MAX_RETRIES:
                raise ValueError(f"Download failed after {_MAX_RETRIES + 1} attempts: {exc}") from exc

    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not decode image from {url}")

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        Path(save_path).write_bytes(raw)

    return img


# ── upload (imgbb primary, catbox fallback) ────────────────────────────

def upload_image(image_path: str) -> str:
    """Upload a local image and return a public URL.

    Tries ImgBB first (if ``IMGBB_API_KEY`` is set), then falls back to
    catbox.moe which needs no API key.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    cfg = get_config(skip_validation=True)
    imgbb_key = cfg.get("IMGBB_API_KEY", "")

    if imgbb_key:
        return _upload_imgbb(path, imgbb_key)
    return _upload_catbox(path)


def _upload_imgbb(path: Path, api_key: str) -> str:
    import base64
    sess = _get_session()
    b64 = base64.b64encode(path.read_bytes()).decode()
    resp = sess.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": b64},
        timeout=_UPLOAD_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"ImgBB upload failed: {data}")
    return data["data"]["url"]


def _upload_catbox(path: Path) -> str:
    sess = _get_session()
    with path.open("rb") as fh:
        resp = sess.post(
            "https://uguu.se/upload.php",
            files={"files[]": (path.name, fh)},
            timeout=_UPLOAD_TIMEOUT,
        )
    resp.raise_for_status()
    url = resp.json()["files"][0]["url"]
    if not url.startswith("http"):
        raise RuntimeError(f"Uguu upload failed: {url}")
    return url


# ── visual helpers ─────────────────────────────────────────────────────

def create_comparison_image(
    img_a: np.ndarray,
    img_b: np.ndarray,
    similarity: float,
    output_path: str,
) -> str:
    """Create a side-by-side comparison with similarity score overlay.

    Both images are resized to the same height before concatenation.
    """
    target_h = 400
    a = _resize_to_height(img_a, target_h)
    b = _resize_to_height(img_b, target_h)

    # 10-px grey divider
    divider = np.full((target_h, 10, 3), 40, dtype=np.uint8)
    canvas = np.hstack([a, divider, b])

    # overlay similarity text
    label = f"Similarity: {similarity:.2f}"
    colour = (0, 220, 0) if similarity >= 0.4 else (0, 0, 220)
    cv2.putText(canvas, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, colour, 2, cv2.LINE_AA)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, canvas)
    return output_path


def _resize_to_height(img: np.ndarray, h: int) -> np.ndarray:
    cur_h, cur_w = img.shape[:2]
    if cur_h == h:
        return img
    scale = h / cur_h
    new_w = max(1, int(cur_w * scale))
    return cv2.resize(img, (new_w, h), interpolation=cv2.INTER_AREA)
