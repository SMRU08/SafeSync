import json

path = r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.system_generated\logs\transcript.jsonl"
last_user_prompt = None
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT":
            last_user_prompt = obj

if last_user_prompt:
    with open("outputs/last_prompt.txt", "w", encoding="utf-8") as out:
        out.write(last_user_prompt.get("content", ""))
    print("Saved last prompt of length:", len(last_user_prompt.get("content", "")))
