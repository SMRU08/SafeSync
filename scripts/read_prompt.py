import json

path = r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT":
            content = obj.get("content", "")
            print("STEP:", obj.get("step_index"), "LEN:", len(content))
            print(content[:500])
            print("="*60)
