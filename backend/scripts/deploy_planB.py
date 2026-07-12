"""
ChromaDB閺傝顢岯闁劎璁查懘姘拱
閹笛嗩攽濮濄儵顎冮敍?1. 濡偓閺岊檳hromaDB鏉╃偞甯?2. 濞撳懐鈹栭悳鐗堟箒闂嗗棗鎮?3. 闁插秵鏌婄€电厧鍙嗛弲顖滃仯閺佺増宓?4. 濞村鐦Λ鈧槐銏犲閼?"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(backend_dir))


import chromadb
from loguru import logger
import json
from app.core.milvus_rag_client import get_rag_engine
from app.models.schemas import Destination, QueryRequest, Season, TravelType
from config.settings import settings


def check_chromadb_connection():
    try:
        collection_name = settings.CHROMA_COLLECTION_NAME
        logger.info(f"濞撳懐鈹栭梿鍡楁値: {collection_name}")

        try:
            client.delete_collection(name=collection_name)
            logger.success(f"閴?閹存劕濮涢崚鐘绘珟閺冄囨肠閸? {collection_name}")
        except Exception as e:
            logger.info(f"闂嗗棗鎮庢稉宥呯摠閸︺劍鍨ㄥ鎻掑灩闂? {e}")

        return True
    except Exception as e:
        logger.error(f"閴?濞撳懐鈹栭梿鍡楁値婢惰精瑙? {e}")
        raise


def load_destinations_from_json(json_path: Path) -> list[Destination]:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        destinations = []
        for item in data:
            try:
                dest = Destination(**item)
                destinations.append(dest)
            except Exception as e:
                logger.warning(f"鐠哄疇绻冮弮鐘虫櫏閺佺増宓? {e}")
                continue

        logger.info(f"娴?{json_path.name} 閸旂姾娴囨禍?{len(destinations)} 娑擃亝娅欓悙?)
        return destinations
    except Exception as e:
        logger.error(f"閸旂姾娴嘕SON閺傚洣娆㈡径杈Е {json_path}: {e}")
        return []


def import_destinations():
    try:
        logger.info("\n瀵偓婵绁寸拠鏇燁梾缁便垹濮涢懗?..")

        rag_engine = get_rag_engine()

        test_queries = [
            {
                "query": "閸栨ぞ鍚惃鍕坊閸欏弶鏋冮崠鏍ㄦ珯閻?,
                "season": Season.SPRING,
                "travel_type": TravelType.FAMILY
            },
            {
                "query": "娑撳﹥鎹ｉ柅鍌氭値閹峰秶鍙庨惃鍕勾閺?,
                "season": Season.AUTUMN,
                "travel_type": TravelType.COUPLE
            },
            {
                "query": "鐟楁寧绠规搴㈡珯",
                "season": None,
                "travel_type": None
            }
        ]

        for i, test_case in enumerate(test_queries, 1):
            logger.info(f"\n濞村鐦?{i}: {test_case['query']}")

            query_request = QueryRequest(
                query=test_case['query'],
                season=test_case['season'],
                travel_type=test_case['travel_type'],
                interests=[]
            )

            results = rag_engine.search(query_request, top_k=5)

            logger.info(f"鏉╂柨娲栫紒鎾寸亯閺? {len(results)}")
            for idx, result in enumerate(results[:3], 1):
                logger.info(f"  {idx}. {result['destination']} (閻╅晲鎶€鎼? {result['similarity']:.4f})")
                logger.info(f"     娴ｅ秶鐤? {result['metadata']['location']}")
                logger.info(f"     閺夈儲绨? {result['source']}")

        logger.success("\n閴?濡偓缁便垺绁寸拠鏇炵暚閹?")
        return True

    except Exception as e:
        logger.error(f"閴?濡偓缁便垺绁寸拠鏇炪亼鐠? {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """娑撹鍤遍弫?""
    logger.info("=" * 60)
    logger.info("ChromaDB閺傝顢岯闁劎璁查懘姘拱")
    logger.info("=" * 60)

    try:
        # 濮濄儵顎?: 濡偓閺岊檳hromaDB鏉╃偞甯?        logger.info("\n[濮濄儵顎?] 濡偓閺岊檳hromaDB鏉╃偞甯?)
        client = check_chromadb_connection()

        # 濮濄儵顎?: 濞撳懐鈹栭悳鐗堟箒闂嗗棗鎮?        logger.info("\n[濮濄儵顎?] 濞撳懐鈹栭悳鐗堟箒闂嗗棗鎮?)
        clear_collection(client)

        # 濮濄儵顎?: 闁插秵鏌婄€电厧鍙嗛弲顖滃仯閺佺増宓?        logger.info("\n[濮濄儵顎?] 闁插秵鏌婄€电厧鍙嗛弲顖滃仯閺佺増宓?)
        if not import_destinations():
            logger.error("鐎电厧鍙嗘径杈Е閿涘瞼绮撳銏ゅ劥缂?)
            return False

        # 濮濄儵顎?: 濞村鐦Λ鈧槐銏犲閼?        logger.info("\n[濮濄儵顎?] 濞村鐦Λ鈧槐銏犲閼?)
        if not test_search():
            logger.error("濡偓缁便垺绁寸拠鏇炪亼鐠?)
            return False

        # 鐎瑰本鍨?        logger.success("\n" + "=" * 60)
        logger.success("棣冨竴 ChromaDB閺傝顢岯闁劎璁查幋鎰!")
        logger.success("=" * 60)
        logger.info("\n閸氬海鐢诲銉╊€?")
        logger.info("1. 闁插秴鎯庨崥搴ｎ伂閺堝秴濮? uvicorn app.main:app --reload")
        logger.info("2. 閸︺劌澧犵粩顖涚ゴ鐠囨洘鎮崇槐銏犲閼?)
        logger.info("3. 鐎佃鐦弬瑙勵攳B娑撳骸甯弬瑙勵攳閻ㄥ嫭顥呯槐銏℃櫏閺?)

        return True

    except Exception as e:
        logger.error(f"\n閴?闁劎璁叉径杈Е: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
