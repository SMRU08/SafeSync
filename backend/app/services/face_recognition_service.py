"""
face_recognition_service.py — RAKSHYA VISION
Singleton service that wraps the face_recognition (dlib) library.
Falls back to placeholder/demo mode when the library is not installed.
"""

import os
import json
import logging
import base64
import numpy as np
from typing import Optional, List, Tuple, Dict
from datetime import datetime, date, timezone
from pathlib import Path

logger = logging.getLogger("face_recognition_service")


class FaceRecognitionService:
    """
    Singleton that manages face embedding extraction and matching.

    Usage:
        svc = FaceRecognitionService.get_instance()
        embedding = svc.extract_embedding_from_base64(b64_string)
        match    = svc.match_face(embedding, known_pairs)
    """

    _instance = None
    FACE_IMAGES_DIR = Path("data/face_images")
    TOLERANCE = 0.5  # Lower = more strict matching

    # ------------------------------------------------------------------
    # Singleton constructor
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "FaceRecognitionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self.FACE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        self._fr_available: bool = False
        self._fr_module = None
        self._try_load_fr()

    # ------------------------------------------------------------------
    # Library loader
    # ------------------------------------------------------------------

    def _try_load_fr(self) -> None:
        try:
            import face_recognition as fr

            self._fr_module = fr
            self._fr_available = True
            logger.info(
                "[FaceRecognition] face_recognition library loaded successfully."
            )
        except ImportError:
            logger.warning(
                "[FaceRecognition] face_recognition library not available. "
                "Using placeholder mode."
            )
            self._fr_available = False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True when the real face_recognition library is active."""
        return self._fr_available

    # ------------------------------------------------------------------
    # Embedding extraction
    # ------------------------------------------------------------------

    def extract_embedding_from_base64(
        self, image_b64: str
    ) -> Optional[List[float]]:
        """
        Extract a 128-d face embedding from a base64-encoded image string.

        Accepts both bare base64 and data-URL prefixed strings
        (e.g. ``data:image/jpeg;base64,<data>``).

        Returns:
            A list of 128 floats, or ``None`` if no face was detected.
        """
        if not self._fr_available:
            # Return a placeholder random embedding for demo / development
            logger.debug(
                "Placeholder mode: returning random 128-d embedding."
            )
            return list(np.random.rand(128).astype(float))

        try:
            import face_recognition as fr
            import cv2

            # Decode base64 → numpy array
            raw_b64 = (
                image_b64.split(",")[-1] if "," in image_b64 else image_b64
            )
            img_bytes = base64.b64decode(raw_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            bgr_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if bgr_frame is None:
                logger.warning("Failed to decode image from base64.")
                return None

            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            face_locations = fr.face_locations(rgb_frame, model="hog")

            if not face_locations:
                logger.warning("No face detected in the provided image.")
                return None

            encodings = fr.face_encodings(rgb_frame, face_locations)
            if not encodings:
                return None

            # Return the encoding of the largest detected face
            largest_idx = 0
            if len(face_locations) > 1:
                areas = [
                    (b - t) * (r - l) for (t, r, b, l) in face_locations
                ]
                largest_idx = areas.index(max(areas))

            return encodings[largest_idx].tolist()

        except Exception as e:
            logger.error("Error extracting face embedding: %s", e)
            return None

    def extract_embedding_from_frame(
        self, bgr_frame: np.ndarray
    ) -> Optional[List[float]]:
        """
        Extract a 128-d face embedding from an OpenCV BGR numpy array.

        Returns:
            A list of 128 floats, or ``None`` if no face was detected.
        """
        if not self._fr_available:
            logger.debug(
                "Placeholder mode: returning random 128-d embedding."
            )
            return list(np.random.rand(128).astype(float))

        try:
            import face_recognition as fr

            # BGR → RGB (face_recognition expects RGB)
            rgb_frame = bgr_frame[:, :, ::-1]
            face_locations = fr.face_locations(rgb_frame, model="hog")

            if not face_locations:
                return None

            encodings = fr.face_encodings(rgb_frame, face_locations)
            return encodings[0].tolist() if encodings else None

        except Exception as e:
            logger.error("Error extracting embedding from frame: %s", e)
            return None

    # ------------------------------------------------------------------
    # Face matching
    # ------------------------------------------------------------------

    def match_face(
        self,
        query_embedding: List[float],
        known_embeddings: List[Tuple[str, List[float]]],
    ) -> Optional[Tuple[str, float]]:
        """
        Match a query embedding against a list of ``(worker_id, embedding)``
        tuples.

        Args:
            query_embedding:  128-d embedding to search for.
            known_embeddings: List of ``(worker_id, embedding)`` pairs loaded
                              from the database.

        Returns:
            ``(best_worker_id, distance)`` if a match is found within
            ``TOLERANCE``, otherwise ``None``.
        """
        if not known_embeddings:
            return None

        try:
            if self._fr_available:
                import face_recognition as fr

                query_arr = np.array(query_embedding)
                known_arrs = [np.array(e) for _, e in known_embeddings]
                distances = fr.face_distance(known_arrs, query_arr)
            else:
                query_arr = np.array(query_embedding)
                distances = [
                    np.linalg.norm(np.array(e) - query_arr)
                    for _, e in known_embeddings
                ]

            min_idx = int(np.argmin(distances))
            min_dist = float(distances[min_idx])

            if min_dist <= self.TOLERANCE:
                return known_embeddings[min_idx][0], min_dist

            return None

        except Exception as e:
            logger.error("Error in face matching: %s", e)
            return None

    # ------------------------------------------------------------------
    # Image persistence
    # ------------------------------------------------------------------

    def save_face_image(
        self, worker_id: str, image_b64: str
    ) -> Optional[str]:
        """
        Decode a base64 image and save it to ``FACE_IMAGES_DIR``.

        Returns:
            The absolute file path as a string, or ``None`` on failure.
        """
        try:
            raw_b64 = (
                image_b64.split(",")[-1] if "," in image_b64 else image_b64
            )
            img_bytes = base64.b64decode(raw_b64)
            filename = (
                f"{worker_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            filepath = self.FACE_IMAGES_DIR / filename

            with open(filepath, "wb") as f:
                f.write(img_bytes)

            logger.info("Saved face image: %s", filepath)
            return str(filepath)

        except Exception as e:
            logger.error("Error saving face image: %s", e)
            return None
