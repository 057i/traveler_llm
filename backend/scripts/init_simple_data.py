"""
缁犫偓閸栨牜澧楅弫鐗堝祦閸掓繂顫愰崠鏍壖閺?- 閻╁瓨甯撮幙宥勭稊 ChromaDB
"""
import sys
import os
import chromadb


from loguru import logger


def create_sample_data():
    try:
        logger.info("瀵偓婵鍨垫慨瀣缁€杞扮伐閺佺増宓侀敍鍫㈢暆閸栨牜澧楅敍?..")

        os.makedirs(persist_directory, exist_ok=True)

        client = chromadb.PersistentClient(path=persist_directory)

            client.delete_collection("travel_destinations")
            logger.info("閸掔娀娅庨弮褔娉﹂崥?)
        except:
            pass

            name="travel_destinations",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("閸掓稑缂撻弬浼存肠閸? travel_destinations")

        sample_data = create_sample_data()
        ids = [item["id"] for item in sample_data]
        documents = [item["text"] for item in sample_data]
        metadatas = [item["metadata"] for item in sample_data]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.success(f"閴?閹存劕濮涘ǎ璇插 {len(sample_data)} 娑擃亝娅欓悙鐟板煂閸氭垿鍣洪弫鐗堝祦鎼存搫绱?)
        logger.info("閺佺増宓佸韫箽鐎涙﹫绱濋悳鏉挎躬閸欘垯浜掑鈧慨瀣ゴ鐠囨洘甯归懡鎰閼虫垝绨?)

        # 妤犲矁鐦夐弫鐗堝祦
        count = collection.count()
        logger.info(f"闂嗗棗鎮庢稉顓炲彙閺?{count} 閺夆剝鏆熼幑?)

        return True

    except Exception as e:
        logger.error(f"閸掓繂顫愰崠鏍ㄦ殶閹诡喖銇戠拹? {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
