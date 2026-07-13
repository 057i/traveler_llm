"""Test rerank threshold filtering"""
import asyncio
from app.core.rerank_client import get_rerank_client

async def test():
    client = get_rerank_client()

    query = '北京有什么好玩的景点'

    candidates = [
        {'name': '故宫', 'description': '中国明清两代的皇家宫殿，世界文化遗产', 'tags': ['历史', '建筑']},
        {'name': '长城', 'description': '中国古代军事防御工程，世界七大奇迹之一', 'tags': ['历史', '景观']},
        {'name': '天坛', 'description': '明清两代皇帝祭天祈谷的场所', 'tags': ['历史', '建筑']},
        {'name': '颐和园', 'description': '中国现存最大的皇家园林', 'tags': ['园林', '历史']},
        {'name': '鸟巢', 'description': '2008年北京奥运会主体育场', 'tags': ['现代', '建筑']},
        {'name': '上海外滩', 'description': '上海的标志性建筑群', 'tags': ['现代', '景观']},
        {'name': '西湖', 'description': '杭州著名风景区', 'tags': ['自然', '景观']},
    ]

    print("\n" + "="*80)
    print("测试Rerank阈值过滤")
    print("="*80)
    print(f"Query: {query}")
    print(f"候选数: {len(candidates)}")
    print(f"配置: threshold=0.5, min=3, max=7")
    print("="*80)

    results = await client.rerank(
        query,
        candidates,
        top_n=10,
        threshold=0.5,
        min_results=3,
        max_results=7
    )

    print("\n" + "="*80)
    print(f"✅ 最终返回: {len(results)} 条结果")
    print("="*80)
    for i, r in enumerate(results, 1):
        score = r.get('rerank_score', 0)
        marker = "✅" if score >= 0.5 else "⚠️"
        print(f"#{i}: {r['name']:10s} | score={score:.4f} {marker}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test())
