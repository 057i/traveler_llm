# 综合搜索升级方案：RAG多路检索 + 结构化筛选 + SSE流式传输

## 📊 现状分析

### 当前综合搜索
- ❌ 只有空壳，没有实际实现
- ❌ 没有RAG检索
- ❌ 没有结构化筛选
- ❌ 没有SSE流式传输

### AI推荐现有能力
✅ **可复用的节点和方法：**

1. **node_milvus_hybrid.py** - Milvus混合检索
   - 稠密向量检索
   - 稀疏向量检索
   - 精确匹配
   - RRF融合

2. **node_neo4j_nearby.py** - Neo4j图谱检索
   - 附近景点查询
   - 关系遍历

3. **node_rrf_fusion.py** - RRF融合算法
   - 多路结果融合

4. **node_rerank.py** - 重排序
   - BGE-Reranker模型

5. **node_confidence_check.py** - 置信度检查
   - 结果质量评估

---

## 🎯 升级目标

### 新的综合搜索功能
```
用户输入
  ↓
【Query处理】
  - 提取关键词
  - 提取实体
  - 理解意图
  ↓
【多路RAG检索】并行
  ├─ Milvus稠密向量
  ├─ Milvus稀疏向量
  ├─ Milvus精确匹配
  └─ Neo4j图谱查询
  ↓
【结构化筛选】
  - 预算范围
  - 天数范围
  - 旅行类型
  - 兴趣偏好
  - 季节
  ↓
【RRF融合】
  - 多路结果融合
  - 去重
  ↓
【重排序】（可选）
  - BGE-Reranker
  ↓
【SSE流式返回】
  - 实时进度
  - 逐条结果
```

---

## 🛠️ 实施方案

### 架构设计

#### 1. 后端服务层

**文件结构：**
```
backend/app/
├── api/
│   └── integrated_search.py          # 升级：API路由 + SSE端点
├── services/
│   └── integrated_search_service.py  # 新增：核心搜索服务
└── workflows/
    └── integrated_search/             # 新增：搜索工作流
        ├── __init__.py
        ├── search_orchestrator.py     # 搜索编排器
        ├── filters/
        │   ├── __init__.py
        │   ├── budget_filter.py       # 预算筛选
        │   ├── duration_filter.py     # 天数筛选
        │   ├── type_filter.py         # 类型筛选
        │   └── season_filter.py       # 季节筛选
        └── retrievers/
            ├── __init__.py
            ├── milvus_retriever.py    # 复用AI推荐逻辑
            └── neo4j_retriever.py     # 复用AI推荐逻辑
```

---

### Phase 1: 创建搜索服务（复用AI推荐代码）

**文件：`services/integrated_search_service.py`**

```python
"""
综合搜索服务

复用AI推荐的检索能力 + 添加结构化筛选
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
import asyncio


class IntegratedSearchService:
    """综合搜索服务 - 多路RAG检索 + 结构化筛选"""
    
    def __init__(self):
        """初始化搜索服务"""
        pass
    
    async def search_stream(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式搜索
        
        Args:
            query: 搜索关键词
            filters: 结构化筛选条件
                {
                    "budget_range": [min, max],      # 预算范围
                    "duration_range": [min, max],    # 天数范围
                    "travel_type": str,              # 旅行类型
                    "interests": List[str],          # 兴趣偏好
                    "season": str                    # 季节
                }
            top_k: 返回结果数量
            
        Yields:
            进度更新和搜索结果
        """
        logger.info(f"[IntegratedSearch] Starting search: {query}")
        
        try:
            # Step 1: Query处理
            yield {
                "type": "progress",
                "step": "query_processing",
                "message": "正在分析查询...",
                "progress": 10
            }
            
            entities = self._extract_entities(query)
            
            # Step 2: 多路RAG检索（并行）
            yield {
                "type": "progress",
                "step": "retrieval",
                "message": "正在搜索知识库...",
                "progress": 20
            }
            
            milvus_results, neo4j_results = await asyncio.gather(
                self._search_milvus(query, entities, top_k),
                self._search_neo4j(entities)
            )
            
            yield {
                "type": "progress",
                "step": "retrieval_complete",
                "message": f"检索到 {len(milvus_results)} 条Milvus结果，{len(neo4j_results)} 条图谱结果",
                "progress": 50
            }
            
            # Step 3: RRF融合
            yield {
                "type": "progress",
                "step": "fusion",
                "message": "正在融合结果...",
                "progress": 60
            }
            
            fused_results = self._rrf_fusion(milvus_results, neo4j_results)
            
            # Step 4: 结构化筛选
            if filters:
                yield {
                    "type": "progress",
                    "step": "filtering",
                    "message": "正在应用筛选条件...",
                    "progress": 70
                }
                
                filtered_results = self._apply_filters(fused_results, filters)
            else:
                filtered_results = fused_results
            
            # Step 5: 流式返回结果
            yield {
                "type": "progress",
                "step": "results_ready",
                "message": f"找到 {len(filtered_results)} 个符合条件的结果",
                "progress": 90
            }
            
            for idx, result in enumerate(filtered_results[:top_k]):
                yield {
                    "type": "result",
                    "index": idx,
                    "data": result
                }
                await asyncio.sleep(0.05)  # 模拟流式传输
            
            # Step 6: 完成
            yield {
                "type": "complete",
                "total": len(filtered_results),
                "message": "搜索完成",
                "progress": 100
            }
            
        except Exception as e:
            logger.error(f"[IntegratedSearch] Search failed: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }
    
    async def _search_milvus(
        self, 
        query: str, 
        entities: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Milvus混合检索（复用AI推荐的逻辑）
        
        直接复用：
        - app.core.milvus_hybrid_client
        - app.core.embedding_service
        - app.core.fusion_strategies
        """
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client
        from app.core.embedding_service import get_embedding_service
        
        milvus_client = get_milvus_hybrid_client()
        embedding_service = get_embedding_service()
        
        # 1. 稠密检索
        dense_vector = embedding_service.encode(query, normalize_embeddings=True)
        dense_results = await milvus_client._search_dense(dense_vector, top_k=top_k)
        
        # 2. 稀疏检索
        sparse_results = await milvus_client._search_sparse(query, top_k=top_k)
        
        # 3. 精确匹配
        exact_results = []
        if entities:
            for entity in entities[:5]:
                try:
                    entity_results = milvus_client.collection.query(
                        expr=f'name == "{entity}"',
                        output_fields=["destination_id", "name", "province", "city",
                                      "category", "description", "rating"],
                        limit=3
                    )
                    for r in entity_results:
                        exact_results.append({
                            'name': r.get('name'),
                            'city': r.get('city'),
                            'province': r.get('province'),
                            'category': r.get('category'),
                            'description': r.get('description'),
                            'rating': r.get('rating', 0),
                            'score': 1.0
                        })
                except:
                    pass
        
        # 4. 简单合并去重
        seen = set()
        merged = []
        
        for r in exact_results + dense_results + sparse_results:
            name = r.get('name')
            if name and name not in seen:
                seen.add(name)
                merged.append(r)
        
        return merged
    
    async def _search_neo4j(self, entities: List[str]) -> List[Dict[str, Any]]:
        """
        Neo4j图谱检索（复用AI推荐的逻辑）
        
        直接复用：
        - app.core.neo4j_client
        """
        if not entities:
            return []
        
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()
        
        results = []
        for entity in entities[:3]:
            try:
                # 查询同城景点
                query = """
                MATCH (d1:Destination {name: $name})-[:LOCATED_IN]->(c:City)
                MATCH (d2:Destination)-[:LOCATED_IN]->(c)
                WHERE d2.name <> d1.name
                RETURN d2.name as name, d2.city as city, d2.category as category
                LIMIT 5
                """
                same_city = neo4j_client.query(query, {"name": entity})
                results.extend(same_city)
            except:
                pass
        
        return results
    
    def _rrf_fusion(
        self,
        milvus_results: List[Dict],
        neo4j_results: List[Dict]
    ) -> List[Dict]:
        """
        RRF融合（复用AI推荐的逻辑）
        
        直接复用：
        - app.core.fusion_strategies.FusionStrategy
        """
        # 简单合并，按score排序
        all_results = milvus_results + neo4j_results
        
        # 去重
        seen = set()
        unique = []
        for r in all_results:
            name = r.get('name')
            if name and name not in seen:
                seen.add(name)
                unique.append(r)
        
        # 按score排序
        unique.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique
    
    def _apply_filters(
        self,
        results: List[Dict],
        filters: Dict[str, Any]
    ) -> List[Dict]:
        """应用结构化筛选"""
        filtered = results
        
        # 预算筛选（需要结果中有price字段）
        if "budget_range" in filters:
            min_budget, max_budget = filters["budget_range"]
            filtered = [
                r for r in filtered
                if min_budget <= r.get('estimated_price', 0) <= max_budget
            ]
        
        # 天数筛选（需要结果中有recommended_days字段）
        if "duration_range" in filters:
            min_days, max_days = filters["duration_range"]
            filtered = [
                r for r in filtered
                if min_days <= r.get('recommended_days', 1) <= max_days
            ]
        
        # 类型筛选
        if "travel_type" in filters and filters["travel_type"]:
            travel_type = filters["travel_type"]
            filtered = [
                r for r in filtered
                if r.get('category') == travel_type
            ]
        
        # 兴趣偏好筛选（标签匹配）
        if "interests" in filters and filters["interests"]:
            interests = set(filters["interests"])
            filtered = [
                r for r in filtered
                if interests & set(r.get('tags', []))
            ]
        
        # 季节筛选（需要结果中有best_season字段）
        if "season" in filters and filters["season"]:
            season = filters["season"]
            filtered = [
                r for r in filtered
                if season in r.get('best_season', [])
            ]
        
        return filtered
    
    def _extract_entities(self, query: str) -> List[str]:
        """简单的实体提取"""
        import re
        keywords = ['山', '寺', '湖', '岛', '古镇', '公园', '景区']
        entities = []
        for kw in keywords:
            pattern = f'[\\u4e00-\\u9fa5]+{kw}'
            matches = re.findall(pattern, query)
            entities.extend(matches)
        return list(set(entities))[:5]


# 单例
_integrated_search_service = None

def get_integrated_search_service() -> IntegratedSearchService:
    """获取综合搜索服务单例"""
    global _integrated_search_service
    if _integrated_search_service is None:
        _integrated_search_service = IntegratedSearchService()
    return _integrated_search_service
```

---

### Phase 2: 升级API路由（添加SSE端点）

**文件：`api/integrated_search.py`**

```python
"""
综合搜索 API - 升级版

添加：
1. RAG多路检索
2. 结构化筛选
3. SSE流式传输
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
import json

router = APIRouter(prefix="/api/integrated-search", tags=["综合搜索"])


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 20


class SearchFilters(BaseModel):
    """结构化筛选条件"""
    budget_range: Optional[List[int]] = None      # [min, max]
    duration_range: Optional[List[int]] = None    # [min_days, max_days]
    travel_type: Optional[str] = None             # 旅行类型
    interests: Optional[List[str]] = None         # 兴趣标签
    season: Optional[str] = None                  # 季节


@router.post("/search/stream")
async def search_stream(request: SearchRequest = Body(...)):
    """
    流式综合搜索（SSE）
    
    返回SSE流，实时传输搜索进度和结果
    """
    try:
        logger.info(f"[IntegratedSearch] Stream search: {request.query}")
        
        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()
        
        async def event_generator():
            """SSE事件生成器"""
            try:
                async for event in search_service.search_stream(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.top_k
                ):
                    # 转换为SSE格式
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
            except Exception as e:
                logger.error(f"[IntegratedSearch] Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"[IntegratedSearch] Failed to start stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(request: SearchRequest = Body(...)):
    """
    普通综合搜索（非流式）
    
    直接返回所有结果
    """
    try:
        logger.info(f"[IntegratedSearch] Search: {request.query}")
        
        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()
        
        results = []
        metadata = {}
        
        async for event in search_service.search_stream(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k
        ):
            if event['type'] == 'result':
                results.append(event['data'])
            elif event['type'] == 'complete':
                metadata = {
                    'total': event['total'],
                    'message': event['message']
                }
        
        return {
            "status": "success",
            "results": results,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"[IntegratedSearch] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "integrated_search_v2"}
```

---

### Phase 3: 前端改造（Vue3）

**文件：`frontend/src/views/IntegratedSearch.vue`**

```vue
<template>
  <div class="integrated-search">
    <!-- 搜索区域 -->
    <div class="search-box">
      <input
        v-model="searchQuery"
        placeholder="输入旅行需求..."
        @keyup.enter="handleSearch"
      />
      
      <!-- 结构化筛选 -->
      <div class="filters">
        <div class="filter-item">
          <label>预算范围</label>
          <input v-model="filters.budgetMin" type="number" placeholder="最低" />
          <span>-</span>
          <input v-model="filters.budgetMax" type="number" placeholder="最高" />
        </div>
        
        <div class="filter-item">
          <label>天数</label>
          <input v-model="filters.daysMin" type="number" placeholder="最少" />
          <span>-</span>
          <input v-model="filters.daysMax" type="number" placeholder="最多" />
        </div>
        
        <div class="filter-item">
          <label>旅行类型</label>
          <select v-model="filters.travelType">
            <option value="">全部</option>
            <option value="自然风光">自然风光</option>
            <option value="历史文化">历史文化</option>
            <option value="休闲度假">休闲度假</option>
          </select>
        </div>
      </div>
      
      <button @click="handleSearch">搜索</button>
    </div>
    
    <!-- 进度显示 -->
    <div v-if="searching" class="progress-box">
      <div class="progress-bar">
        <div class="progress-fill" :style="{width: progress + '%'}"></div>
      </div>
      <p>{{ progressMessage }}</p>
    </div>
    
    <!-- 结果列表 -->
    <div class="results">
      <div
        v-for="result in results"
        :key="result.name"
        class="result-card"
      >
        <h3>{{ result.name }}</h3>
        <p>{{ result.description }}</p>
        <div class="meta">
          <span>{{ result.city }}</span>
          <span>评分: {{ result.rating }}</span>
          <span>相关度: {{ (result.score * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const searchQuery = ref('')
const searching = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const results = ref([])

const filters = ref({
  budgetMin: null,
  budgetMax: null,
  daysMin: null,
  daysMax: null,
  travelType: ''
})

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  searching.value = true
  progress.value = 0
  results.value = []
  
  try {
    // 构建筛选条件
    const filterPayload = {}
    
    if (filters.value.budgetMin && filters.value.budgetMax) {
      filterPayload.budget_range = [filters.value.budgetMin, filters.value.budgetMax]
    }
    
    if (filters.value.daysMin && filters.value.daysMax) {
      filterPayload.duration_range = [filters.value.daysMin, filters.value.daysMax]
    }
    
    if (filters.value.travelType) {
      filterPayload.travel_type = filters.value.travelType
    }
    
    // 发起SSE请求
    const response = await fetch('/api/integrated-search/search/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: searchQuery.value,
        filters: filterPayload,
        top_k: 20
      })
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6))
          
          if (data.type === 'progress') {
            progress.value = data.progress
            progressMessage.value = data.message
          } else if (data.type === 'result') {
            results.value.push(data.data)
          } else if (data.type === 'complete') {
            searching.value = false
          } else if (data.type === 'error') {
            console.error('Search error:', data.message)
            searching.value = false
          }
        }
      }
    }
    
  } catch (error) {
    console.error('Search failed:', error)
    searching.value = false
  }
}
</script>

<style scoped>
.integrated-search {
  padding: 20px;
}

.search-box input {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filters {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-box {
  margin: 20px 0;
}

.progress-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s;
}

.results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.3s;
}

.result-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
</style>
```

---

## 📋 实施步骤

### Step 1: 创建搜索服务
- [ ] 创建 `services/integrated_search_service.py`
- [ ] 复用AI推荐的Milvus检索逻辑
- [ ] 复用AI推荐的Neo4j检索逻辑
- [ ] 实现结构化筛选逻辑

### Step 2: 升级API路由
- [ ] 升级 `api/integrated_search.py`
- [ ] 添加SSE端点 `/search/stream`
- [ ] 保留普通端点 `/search`

### Step 3: 前端改造
- [ ] 创建/升级前端页面
- [ ] 添加结构化筛选UI
- [ ] 实现SSE流式接收
- [ ] 实时显示进度和结果

### Step 4: 测试验证
- [ ] 测试RAG检索
- [ ] 测试结构化筛选
- [ ] 测试SSE流式传输
- [ ] 性能优化

---

## 🎯 核心优势

### 复用AI推荐的能力
1. ✅ Milvus混合检索（稠密+稀疏+精确）
2. ✅ Neo4j图谱查询
3. ✅ RRF融合算法
4. ✅ Embedding服务

### 新增能力
1. ✅ 结构化筛选（预算/天数/类型/兴趣/季节）
2. ✅ SSE流式传输（实时进度反馈）
3. ✅ 更友好的用户体验

---

**准备开始实施吗？我可以逐步帮你完成每个文件！**
