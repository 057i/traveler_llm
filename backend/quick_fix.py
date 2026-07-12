from pathlib import Path

def has_garbled(line):
    for char in line:
        code = ord(char)
        if 0x9589 <= code <= 0x9FFF or 0xE000 <= code <= 0xF8FF:
            return True
    return False

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        cleaned = [line for line in lines if not has_garbled(line)]
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(cleaned)
        return True, len(lines) - len(cleaned)
    except Exception as e:
        return False, str(e)

base = Path(r'E:\大模型开发\代码\网站\travel_proj\backend\app\workflows')
files = [
    'team_recommend/master_agent.py',
    'team_recommend/schemas.py',
    'team_recommend/service.py',
    'team_recommend/team_manager.py',
    'ai_recommend/nodes/node_confidence_check.py',
    'ai_recommend/nodes/node_parallel_retrieval.py',
    'ai_recommend/nodes/node_query_rewriter.py',
    'ai_recommend/nodes/node_rerank.py',
    'ai_recommend/nodes/node_rrf_fusion.py',
    'ai_recommend/nodes/node_rrf_fusion_with_tavily.py',
    'ai_recommend/nodes/node_synthesizer.py',
    'ai_recommend/nodes/node_tavily_search.py',
    'document_processing/nodes/node_chunking.py',
    'document_processing/nodes/node_entity_extraction.py',
    'document_processing/nodes/node_pdf_parse.py',
    'document_processing/nodes/node_vectorization.py',
    'team_recommend/subagents/budget_expert.py',
    'team_recommend/subagents/food_assistant.py',
    'team_recommend/subagents/graph_rag_assistant.py',
    'team_recommend/subagents/itinerary_planner.py',
    'team_recommend/subagents/rag_assistant.py',
    'team_recommend/subagents/tools.py',
    'team_recommend/subagents/transport_assistant.py',
]

for f in files:
    path = base / f
    if path.exists():
        success, info = clean_file(path)
        print(f'{f}: {info}')
