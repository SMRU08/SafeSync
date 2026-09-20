import argparse
import json
import logging
import yaml
from pathlib import Path
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("normalize_classes")


def load_mapping(mapping_file: Path) -> tuple[dict, set]:
    with open(mapping_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Build lower-case string to canonical integer index map
    name_to_id = {}
    for canon_id, canon_name in config.get("canonical_classes", {}).items():
        name_to_id[canon_name.lower()] = canon_id

    string_to_id = {}
    for canon_name, aliases in config.get("mappings", {}).items():
        canon_id = name_to_id.get(canon_name.lower())
        if canon_id is not None:
            string_to_id[canon_name.lower()] = canon_id
            for alias in aliases:
                string_to_id[alias.lower()] = canon_id

    ignored = {name.lower() for name in config.get("ignored_in_detector", [])}
    return string_to_id, ignored


def normalize_dataset(
    source_labels_dir: Path,
    source_class_names: list[str],
    output_labels_dir: Path,
    mapping_file: Path,
    unmapped_report_file: Path
):
    string_to_id, ignored = load_mapping(mapping_file)
    output_labels_dir.mkdir(parents=True, exist_ok=True)
    unmapped_report_file.parent.mkdir(parents=True, exist_ok=True)

    unmapped_counts = {}
    total_processed = 0

    for label_path in source_labels_dir.rglob("*.txt"):
        new_lines = []
        with open(label_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue

                orig_idx = int(parts[0])
                if orig_idx < len(source_class_names):
                    orig_name = source_class_names[orig_idx].lower()
                else:
                    orig_name = f"unknown_{orig_idx}"

                if orig_name in ignored:
                    # Explicitly filtered out per strategy
                    continue

                if orig_name in string_to_id:
                    canon_id = string_to_id[orig_name]
                    new_line = f"{canon_id} " + " ".join(parts[1:])
                    new_lines.append(new_line)
                else:
                    unmapped_counts[orig_name] = unmapped_counts.get(orig_name, 0) + 1

        dest_file = output_labels_dir / label_path.name
        with open(dest_file, "w", encoding="utf-8") as out:
            for nl in new_lines:
                out.write(nl + "\n")
        total_processed += 1

    # Write unmapped classes report
    report = [
        {"original_class": k, "count": v, "reason_not_mapped": "Not in canonical class map or ignored"}
        for k, v in unmapped_counts.items()
    ]
    with open(unmapped_report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Normalized %d label files. Unmapped classes saved to %s", total_processed, unmapped_report_file)


def main():
    parser = argparse.ArgumentParser(description="Normalize dataset annotations to canonical classes.")
    parser.add_argument("--labels-in", required=True, help="Input labels directory.")
    parser.add_argument("--classes-in", required=True, nargs="+", help="Original class names in order.")
    parser.add_argument("--labels-out", required=True, help="Output normalized labels directory.")
    parser.add_argument("--mapping", default="datasets/manifests/class_mapping.yaml", help="Path to class_mapping.yaml")
    parser.add_argument("--unmapped-report", default="datasets/reports/unmapped_classes.json", help="Path to unmapped report.")
    args = parser.parse_args()

    normalize_dataset(
        Path(args.labels_in),
        args.classes_in,
        Path(args.labels_out),
        Path(args.mapping),
        Path(args.unmapped_report)
    )


if __name__ == "__main__":
    main()