from pathlib import Path

def has_garbled(line):
    for char in line:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0xE000 <= code <= 0xF8FF:
            return True
    return False

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        cleaned = [line for line in lines if not has_garbled(line)]
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(cleaned)
        return len(lines) - len(cleaned)
    except Exception as e:
        return str(e)

base = Path(r'E:\大模型开发\代码\网站\travel_proj\backend\app\workflows')
files = [
    'team_recommend/schemas.py',
    'team_recommend/service.py',
    'document_processing/nodes/node_entity_extraction.py',
    'document_processing/nodes/node_vectorization.py',
    'team_recommend/subagents/budget_expert.py',
    'team_recommend/subagents/food_assistant.py',
    'team_recommend/subagents/itinerary_planner.py',
    'team_recommend/subagents/rag_assistant.py',
    'team_recommend/subagents/transport_assistant.py',
]

for f in files:
    path = base / f
    if path.exists():
        result = clean_file(path)
        print(f'{f}: removed {result} lines')
