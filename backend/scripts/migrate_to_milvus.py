"""
ChromaDB閸掔檿ilvus閺佺増宓佹潻浣盒╅懘姘拱
閹笛嗩攽濮濄儵顎冮敍?1. 濡偓閺岊檽ilvus鏉╃偞甯?2. 閸掓稑缂?濞撳懐鈹朚ilvus闂嗗棗鎮?3. 娴犲东SON閺傚洣娆㈢€电厧鍙嗛弲顖滃仯閺佺増宓侀崚鐧昳lvus
4. 濞村鐦Λ鈧槐銏犲閼?"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(backend_dir))


from pymilvus import connections, utility
from loguru import logger
import json
from app.core.milvus_rag_client_milvus import get_rag_engine
from app.models.schemas import Destination, QueryRequest, Season, TravelType
from config.settings import settings


def check_milvus_connection():
    try:
        collection_name = settings.MILVUS_COLLECTION_NAME
        logger.info(f"濡偓閺屻儵娉﹂崥? {collection_name}")

        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            logger.success(f"閴?閹存劕濮涢崚鐘绘珟閺冄囨肠閸? {collection_name}")
        else:
            logger.info(f"闂嗗棗鎮庢稉宥呯摠閸? {collection_name}")

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
        logger.info("瀵偓婵顕遍崗銉︽珯閻愯鏆熼幑顔煎煂Milvus...")

        rag_engine = get_rag_engine()

        if not data_dir.exists():
            logger.error(f"閴?閺佺増宓侀惄顔肩秿娑撳秴鐡ㄩ崷? {data_dir}")
            return False

        logger.info(f"閹垫儳鍩?{len(json_files)} 娑擃亝鏆熼幑顔芥瀮娴?)

        total_count = 0
        for json_file in json_files:
            logger.info(f"\n婢跺嫮鎮婇弬鍥︽: {json_file.name}")
            destinations = load_destinations_from_json(json_file)

            if destinations:
                success = rag_engine.add_destinations(
                    destinations=destinations,
                    source_file=json_file.name
                )

                if success:
                    total_count += len(destinations)
                    logger.success(f"閴?閹存劕濮涚€电厧鍙?{len(destinations)} 娑擃亝娅欓悙?)
                else:
                    logger.error(f"閴?鐎电厧鍙嗘径杈Е: {json_file.name}")

        logger.success(f"\n閴?閹鍙＄€电厧鍙?{total_count} 娑擃亝娅欓悙鐟板煂Milvus")
        return True

    except Exception as e:
        logger.error(f"閴?鐎电厧鍙嗛弫鐗堝祦婢惰精瑙? {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    logger.info("=" * 60)
    logger.info("ChromaDB閸掔檿ilvus閺佺増宓佹潻浣盒╅懘姘拱")
    logger.info("=" * 60)

    try:
        if not check_milvus_connection():
            logger.error("Milvus鏉╃偞甯存径杈Е閿涘矁顕Λ鈧弻銉︽箛閸斺剝妲搁崥锕€鎯庨崝?)
            return False

        clear_collection()

        if not import_destinations():
            logger.error("鐎电厧鍙嗘径杈Е閿涘瞼绮撳銏ｇ讣缁?)
            return False

        if not test_search():
            logger.error("濡偓缁便垺绁寸拠鏇炪亼鐠?)
            return False

        # 鐎瑰本鍨?        logger.success("\n" + "=" * 60)
        logger.success("棣冨竴 Milvus鏉╀胶些閹存劕濮?")
        logger.success("=" * 60)
        logger.info("\n閸氬海鐢诲銉╊€?")
        logger.info("1. 婢跺洣鍞ら崢鐒g_engine.py: cp rag_engine.py rag_engine_chroma_backup.py")
        logger.info("2. 閺囨寧宕插鏇熸惛: cp rag_engine_milvus.py rag_engine.py")
        logger.info("3. 闁插秴鎯庨崥搴ｎ伂閺堝秴濮? uvicorn app.main:app --reload")
        logger.info("4. 閸︺劌澧犵粩顖涚ゴ鐠囨洘鎮崇槐銏犲閼?)

        return True

    except Exception as e:
        logger.error(f"\n閴?鏉╀胶些婢惰精瑙? {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
