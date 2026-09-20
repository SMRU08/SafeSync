import argparse
import logging
from pathlib import Path
import cv2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("generate_samples")

CANONICAL_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke"
}

CLASS_COLORS = {
    0: (255, 120, 0),     # person - blue-orange
    1: (0, 255, 0),       # helmet - bright green
    2: (0, 215, 255),     # safety_vest - yellow-amber
    3: (255, 0, 255),     # gloves - magenta
    4: (180, 105, 255),   # safety_footwear - pink
    5: (0, 0, 255),       # fire - red
    6: (128, 128, 128)    # smoke - gray
}


def draw_annotations(image_path: Path, label_path: Path, output_path: Path) -> bool:
    img = cv2.imread(str(image_path))
    if img is None:
        return False

    h, w, _ = img.shape
    if not label_path.exists():
        return False

    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue

            cls_id = int(parts[0])
            cx, cy, bw, bh = map(float, parts[1:])

            # Convert YOLO normalized coords to pixel bounding box
            x1 = int((cx - bw / 2) * w)
            y1 = int((cy - bh / 2) * h)
            x2 = int((cx + bw / 2) * w)
            y2 = int((cy + bh / 2) * h)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w - 1, x2)
            y2 = min(h - 1, y2)

            color = CLASS_COLORS.get(cls_id, (255, 255, 255))
            label_text = CANONICAL_NAMES.get(cls_id, f"class_{cls_id}")

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                img,
                label_text,
                (x1, max(y1 - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)
    return True


def render_representative_samples(processed_dir: Path, output_samples_dir: Path):
    images_dir = processed_dir / "images"
    labels_dir = processed_dir / "labels"

    # Find sample for each class
    found_classes = set()
    output_samples_dir.mkdir(parents=True, exist_ok=True)

    for img_path in images_dir.rglob("*.*"):
        lbl_path = labels_dir / img_path.parent.name / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            continue

        try:
            with open(lbl_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        cls_id = int(parts[0])
                        if cls_id in CANONICAL_NAMES and cls_id not in found_classes:
                            out_img = output_samples_dir / f"sample_{CANONICAL_NAMES[cls_id]}_{img_path.name}"
                            if draw_annotations(img_path, lbl_path, out_img):
                                found_classes.add(cls_id)
                                logger.info("Rendered sample for class '%s': %s", CANONICAL_NAMES[cls_id], out_img)
        except Exception:
            pass

    logger.info("Rendered samples for %d distinct classes.", len(found_classes))


def main():
    parser = argparse.ArgumentParser(description="Generate visual samples with annotated bounding boxes.")
    parser.add_argument("--processed-dir", default="datasets/processed")
    parser.add_argument("--output", default="datasets/reports/samples")
    args = parser.parse_args()

    render_representative_samples(Path(args.processed_dir), Path(args.output))


if __name__ == "__main__":
    main()