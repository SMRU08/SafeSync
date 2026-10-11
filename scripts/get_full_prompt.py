import json

path = r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.system_generated\logs\transcript_full.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT":
            last_user_prompt = obj

with open("outputs/full_last_prompt.txt", "w", encoding="utf-8") as out:
    out.write(last_user_prompt.get("content", ""))
print("Saved full prompt, len:", len(last_user_prompt.get("content", "")))
