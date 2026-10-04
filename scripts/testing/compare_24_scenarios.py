import sys, json
from pathlib import Path
from ultralytics import YOLO
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"

v3 = YOLO(str(V3_PATH))
v6 = YOLO(str(V6_PATH))

from scripts.testing.run_realworld_validation_suite import SCENARIOS_SPEC, OPERATING_THRESHOLDS, CLASS_NAMES

test_img_dir = ROOT / "datasets" / "processed_v3" / "images" / "test"
test_lbl_dir = ROOT / "datasets" / "processed_v3" / "labels" / "test"

all_test_imgs = sorted(list(test_img_dir.glob("*.jpg")) + list(test_img_dir.glob("*.png")))
img_by_classes = {}
for img_p in all_test_imgs:
    lbl_p = test_lbl_dir / f"{img_p.stem}.txt"
    classes_present = set()
    if lbl_p.exists():
        for line in lbl_p.read_text().strip().splitlines():
            if line:
                c_id = int(line.split()[0])
                classes_present.add(CLASS_NAMES.get(c_id, str(c_id)))
    img_by_classes[img_p] = classes_present

def eval_model(model):
    res_list = []
    for spec in SCENARIOS_SPEC:
        s_id = spec["id"]
        s_name = spec["name"]
        s_group = spec["group"]
        targets = spec["target_classes"]
        forbids = spec["forbid_classes"]

        if s_group == "HardNegative":
            if "safety_vest" in targets:
                cand = [p for p, c in img_by_classes.items() if "safety_vest" in c and "fire" not in c and "smoke" not in c][:5]
            else:
                cand = [p for p, c in img_by_classes.items() if p.stem.startswith("hneg")][:5]
                if not cand:
                    cand = [p for p, c in img_by_classes.items() if "fire" not in c and "smoke" not in c][:5]
        elif s_group == "Hazard":
            cand = [p for p, c in img_by_classes.items() if any(t in c for t in targets)][:5]
        else:
            cand = [p for p, c in img_by_classes.items() if any(t in c for t in targets)][:5]

        if not cand:
            cand = all_test_imgs[:3]

        preds_found = Counter()
        for p in cand:
            res = model.predict(source=str(p), imgsz=384, conf=0.20, verbose=False)[0]
            for b in res.boxes:
                cname = CLASS_NAMES.get(int(b.cls[0].item()), "")
                conf = float(b.conf[0].item())
                if conf >= OPERATING_THRESHOLDS.get(cname, 0.20):
                    preds_found[cname] += 1

        target_met = all(preds_found[t] > 0 for t in targets) if targets else True
        forbidden_clean = not any(preds_found[f] > 0 for f in forbids)
        passed = target_met and forbidden_clean
        res_list.append({
            "id": s_id,
            "name": s_name,
            "group": s_group,
            "passed": passed,
            "targets_met": target_met,
            "forbidden_clean": forbidden_clean,
            "preds": dict(preds_found)
        })
    return res_list

v3_results = eval_model(v3)
v6_results = eval_model(v6)

v3_pass = sum(1 for r in v3_results if r["passed"])
v6_pass = sum(1 for r in v6_results if r["passed"])
print(f"V3 Pass: {v3_pass}/24 ({v3_pass/24*100:.1f}%)")
print(f"V6 Pass: {v6_pass}/24 ({v6_pass/24*100:.1f}%)")

out_comp = {
    "v3_passed": v3_pass,
    "v6_passed": v6_pass,
    "comparisons": []
}

for v3_r, v6_r in zip(v3_results, v6_results):
    print(f"Scenario {v3_r['id']:02d} [{v3_r['group']}]: V3={v3_r['passed']} | V6={v6_r['passed']} - {v3_r['name']}")
    out_comp["comparisons"].append({
        "id": v3_r["id"],
        "name": v3_r["name"],
        "group": v3_r["group"],
        "v3_passed": v3_r["passed"],
        "v6_passed": v6_r["passed"],
        "v3_preds": v3_r["preds"],
        "v6_preds": v6_r["preds"],
    })

with open(ROOT / "reports" / "v3_vs_v6_scenarios_comparison.json", "w") as f:
    json.dump(out_comp, f, indent=2)
