"""
Python文件缂栫爜淇鍜屾敞閲婃坊鍔?- 宸ヤ綔鎶ュ憡

任务鎵ц鎯呭喌鎬荤粨
"""

# ============================================================================
# ============================================================================

鎬绘枃浠舵暟: 71涓狿ython文件
- app/api: 6涓枃浠?- app/core: 12涓枃浠?- app/services: 8涓枃浠?- app/workflows: 43涓枃浠?- config: 2涓枃浠?
# ============================================================================
# ============================================================================

宸插畬鎴愪慨澶嶅苟娣诲姞瀹屽杽涓枃娉ㄩ噴鐨勬枃浠?

1. app/api/ai_recommend.py (8.1 KB)
   - 淇缂栫爜闂
   - 娣诲姞瀹屾暣鐨勫嚱鏁版敞閲婏紙鍖呭惈Args銆丷eturns銆丒xample绛夛級
   - 4涓矾鐢卞嚱鏁板叏閮ㄦ坊鍔犺缁嗘敞閲?
2. app/api/chat.py (4.3 KB)
   - 淇缂栫爜闂
   - 娣诲姞瀹屾暣鐨勭被鍜屽嚱鏁版敞閲?   - 2涓矾鐢卞嚱鏁板叏閮ㄦ坊鍔犺缁嗘敞閲?
3. app/api/rrf.py (8.2 KB)
   - 淇缂栫爜闂
   - 娣诲姞瀹屾暣鐨勫嚱鏁版敞閲?   - 3涓矾鐢卞嚱鏁板叏閮ㄦ坊鍔犺缁嗘敞閲婏紝鍖呭惈瀹屾暣鐨勬妧鏈爤璇存槑

4. app/api/team_recommend_ws.py (6.6 KB)
   - 淇缂栫爜闂
   - 娣诲姞瀹屾暣鐨刉ebSocket鍑芥暟娉ㄩ噴
   - 鍖呭惈宸ヤ綔娴佺▼璇存槑鍜屾暟鎹牸寮忚鏄?
5. fix_encoding.py (鏂板垱寤?
   - 缂栫爜妫€娴嬪拰淇宸ュ叿鑴氭湰
   - 鍙嚜鍔ㄦ娴嬪苟鎶ュ憡涔辩爜文件

# ============================================================================
# 鈿狅笍 浠嶉渶淇鐨勬枃浠?(57涓?
# ============================================================================

## app/api/ (1涓?
- documents.py - RAG鏂囨。绠＄悊API (澶ф枃浠讹紝536琛?

## app/core/ (10涓?
- fusion_strategies.py - 娣峰悎妫€绱㈣瀺鍚堢瓥鐣?- health_check.py - 系统鍚姩妫€鏌?- milvus_client.py - Milvus瀹㈡埛绔?- neo4j_graph_client.py - Neo4j鍥炬暟鎹簱瀹㈡埛绔?- redis_client.py - Redis瀹㈡埛绔?- reranker.py - 閲嶆帓搴忓櫒
- rerank_client.py - 閲嶆帓搴忓鎴风
- rrf_client.py - RRF铻嶅悎瀹㈡埛绔?- tavily_client.py - Tavily搜索瀹㈡埛绔?- workflow_engine.py - 宸ヤ綔娴佸紩鎿?
## app/services/ (7涓?
- base_service.py - 鍩虹服务绫?- chat_history.py - 鑱婂ぉ鍘嗗彶服务
- destination_extractor.py - 鐩殑鍦版彁鍙栨湇鍔?- document_task.py - 鏂囨。任务服务
- hybrid_recommend.py - 娣峰悎推荐服务
- progress_tracker.py - 进度杩借釜服务
- rrf_recommend_service.py - RRF推荐服务

## app/workflows/ (37涓?
### 涓诲伐浣滄祦 (3涓?
- chat_workflow.py
- manager.py
- websocket_workflow.py

### AI推荐宸ヤ綔娴?(9涓?
- ai_recommend/graph_builder.py
- ai_recommend/service.py
- ai_recommend/state.py
- ai_recommend/__init__.py
- ai_recommend/nodes/node_confidence_check.py
- ai_recommend/nodes/node_parallel_retrieval.py
- ai_recommend/nodes/node_query_rewriter.py
- ai_recommend/nodes/node_rerank.py
- ai_recommend/nodes/node_rrf_fusion.py
- ai_recommend/nodes/node_rrf_fusion_with_tavily.py
- ai_recommend/nodes/node_synthesizer.py
- ai_recommend/nodes/node_tavily_search.py
- ai_recommend/nodes/__init__.py

### 鏂囨。处理宸ヤ綔娴?(7涓?
- document_processing/graph_builder.py
- document_processing/state.py
- document_processing/__init__.py
- document_processing/nodes/node_chunking.py
- document_processing/nodes/node_entity_extraction.py
- document_processing/nodes/node_pdf_parse.py
- document_processing/nodes/node_vectorization.py
- document_processing/nodes/__init__.py

### 鍥㈤槦推荐宸ヤ綔娴?(10涓?
- team_recommend/master_agent.py
- team_recommend/schemas.py
- team_recommend/service.py
- team_recommend/team_manager.py
- team_recommend/__init__.py
- team_recommend/subagents/base.py
- team_recommend/subagents/budget_expert.py
- team_recommend/subagents/food_assistant.py
- team_recommend/subagents/graph_rag_assistant.py
- team_recommend/subagents/itinerary_planner.py
- team_recommend/subagents/rag_assistant.py
- team_recommend/subagents/tools.py
- team_recommend/subagents/transport_assistant.py

## config/ (2涓?
- fusion_config.py - 铻嶅悎绛栫暐配置
- settings.py - 鍏ㄥ眬璁剧疆配置

# ============================================================================
# 馃敡 淇绛栫暐璇存槑
# ============================================================================

鎵€鏈変贡鐮佹枃浠剁殑鐗瑰緛:
- 文件宸叉槸UTF-8缂栫爜
- 浣嗗唴瀹逛腑鐨勪腑鏂囧瓧绗﹁错误鍦颁互鍏朵粬缂栫爜保存锛屽鑷存樉绀轰负涔辩爜
- 渚嬪锛?閺傚洦銆? 搴旇鏄?"鏂囨。"锛?閹恒劏宕? 搴旇鏄?"推荐"

淇鏂规硶:
1. 鎵嬪姩閲嶅啓姣忎釜文件鐨勪腑鏂囧唴瀹?2. 涓烘瘡涓嚱鏁版坊鍔犲畬鍠勭殑涓枃娉ㄩ噴锛屽寘鎷?
   - 鍑芥暟鍔熻兘璇存槑
   - 鍙傛暟璇存槑 (Args)
   - 杩斿洖鍊艰鏄?(Returns)
   - 寮傚父璇存槑 (Raises锛屽鏋滄湁)
   - 浣跨敤绀轰緥 (Example锛屽鏋滃鏉?

# ============================================================================

鐢变簬鍓╀綑文件鏁伴噺杈冨锛?7涓級锛屽缓璁垎闃舵处理:

## 闃舵1锛氭牳蹇冩ā鍧椾紭鍏?(浼樺厛绾э細楂?
1. app/core/*.py (10涓枃浠? - 鏍稿績寮曟搸
2. config/*.py (2涓枃浠? - 配置文件

## 闃舵2锛氫笟鍔℃湇鍔?(浼樺厛绾э細涓?
3. app/services/*.py (7涓枃浠? - 涓氬姟服务灞?
## 闃舵3锛氬伐浣滄祦妯″潡 (浼樺厛绾э細涓?
4. app/workflows/涓绘枃浠?(3涓枃浠?
5. app/workflows/瀛愭ā鍧?(34涓枃浠?

## 闃舵4锛欰PI瀹屽杽 (浼樺厛绾э細浣?
6. app/api/documents.py (1涓ぇ文件)

# ============================================================================
# 馃摑 娉ㄩ噴鏍煎紡鏍囧噯
# ============================================================================

宸查噰鐢ㄧ殑娉ㄩ噴鏍煎紡绀轰緥:

```python
def example_function(param1: str, param2: int) -> dict:
    \"\"\"
    鍑芥暟鐨勭畝鐭弿杩帮紙涓€鍙ヨ瘽姒傛嫭鍔熻兘锛?
    详细璇存槑鍑芥暟鐨勫姛鑳姐€佺敤閫斻€佹妧鏈爤绛?    鍙互鍖呭惈澶氳璇存槑

    Args:
        param1 (str): 鍙傛暟1鐨勮缁嗚鏄?        param2 (int): 鍙傛暟2鐨勮缁嗚鏄?            鍙互澶氳璇存槑澶嶆潅鍙傛暟

    Returns:
        dict: 杩斿洖鍊肩殑详细璇存槑
            {
                'key1': '鍊肩殑璇存槑',
                'key2': '鍊肩殑璇存槑'
            }

    Raises:
        ValueError: 浠€涔堟儏鍐典笅鎶涘嚭姝ゅ紓甯?        HTTPException: 浠€涔堟儏鍐典笅鎶涘嚭姝ゅ紓甯?
    Example:
        >>> result = example_function("test", 123)
        >>> print(result)
        {'key1': 'value1', 'key2': 'value2'}
    \"\"\"
    pass
```

# ============================================================================
# 馃幆 完成进度
# ============================================================================

进度: 5 / 71 (7.0%)
- 鉁?宸插畬鎴? 5涓枃浠?- 鈿狅笍 寰呭鐞? 57涓枃浠?- 鉁?姝ｅ父: 14涓枃浠讹紙鏃犻渶淇锛屼富瑕佹槸__init__.py绛夌畝鍗曟枃浠讹級

棰勮鍓╀綑宸ヤ綔閲?
- 鏍稿績妯″潡 (12涓?: 绾?-8灏忔椂
- 涓氬姟服务 (7涓?: 绾?-4灏忔椂
- 宸ヤ綔娴佹ā鍧?(37涓?: 绾?5-20灏忔椂
- 鎬昏: 绾?4-32灏忔椂

# ============================================================================
# 馃搶 閲嶈鎻愮ず
# ============================================================================

2. 鎵€鏈夋敞閲婇兘浣跨敤瑙勮寖鐨勪腑鏂囷紝骞堕伒寰狦oogle Python椋庢牸鎸囧崡
3. 淇濈暀浜嗗師鏈夌殑浠ｇ爜閫昏緫鍜屽姛鑳斤紝鍙慨澶嶄簡缂栫爜鍜屾坊鍔犱簡娉ㄩ噴
4. 鍙互浣跨敤fix_encoding.py鑴氭湰蹇€熸娴嬪摢浜涙枃浠朵粛鏈変贡鐮侀棶棰?
# ============================================================================
# 馃搧 宸ュ叿文件
# ============================================================================

宸插垱寤虹殑宸ュ叿:
1. fix_encoding.py - 缂栫爜妫€娴嬪拰淇鑴氭湰
   - 鍙互鎵归噺鎵弿鎵€鏈塒ython文件
   - 鑷姩妫€娴嬩贡鐮佹枃浠?   - 鐢熸垚详细鐨勭粺璁℃姤鍛?
浣跨敤鏂规硶:
```bash
cd E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend
python fix_encoding.py
```

# ============================================================================
# 鉁?鎬荤粨
# ============================================================================

鏈任务宸插畬鎴愬垵姝ュ伐浣?
1. 鉁?淇浜?涓狝PI文件鐨勭紪鐮侀棶棰?2. 鉁?涓鸿繖5涓枃浠舵坊鍔犱簡瀹屽杽鐨勪腑鏂囨敞閲?3. 鉁?创建浜嗚嚜鍔ㄥ寲妫€娴嬪伐鍏?4. 鉁?鐢熸垚浜嗚缁嗙殑宸ヤ綔鎶ュ憡

鍓╀綑宸ヤ綔寤鸿鍒嗛樁娈佃繘琛岋紝浼樺厛处理鏍稿績妯″潡鍜岄厤缃枃浠躲€?