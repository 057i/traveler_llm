# 附近推荐功能增强方案

## 📋 现状分析

### ✅ 已有功能
1. **State字段**：
   - `needs_nearby_search: bool` ✅ 已存在
   - `neo4j_results: List[Dict[str, Any]]` ✅ 已存在

2. **查询分析节点**：
   - 已判断 `needs_nearby_search` ✅
   - Prompt已包含"附近"、"周边"关键词检测 ✅

3. **Neo4j节点**：
   - 已有附近检索逻辑 ✅
   - 条件执行（needs_nearby_search=True时） ✅

4. **Synthesizer节点**：
   - 已获取 `neo4j_results` ✅
   - 已将附近信息加入Prompt ✅
   - 但**附近信息混在sources中，不明显** ❌

---

## 🎯 改进方案

### **需要改进的地方**

1. **查询分析Prompt优化**：增强附近场景的判断（酒店、美食）
2. **前端展示优化**：将附近推荐单独展示，更清晰
3. **Sources结构优化**：分离主要推荐和附近推荐

---

## 📝 详细修改方案

### **方案1：最小改动（推荐）**

**只需修改Synthesizer节点，将附近推荐单独返回**

#### **1. 修改State（添加新字段）**

```python
# state.py
class AIRecommendState(TypedDict):
    # ... 现有字段 ...
    
    # Final
    final_answer: str
    sources: List[Dict[str, Any]]
    nearby_recommendations: List[Dict[str, Any]]  # 新增：附近推荐
```

#### **2. 修改Synthesizer节点**

```python
# node_synthesizer.py

# 在准备sources的地方（第122-145行）修改：

# 主要推荐sources（只包含reranked_results）
sources = []
for i, r in enumerate(reranked_results[:3]):  # Top 3
    if isinstance(r, dict):
        sources.append({
            "name": r.get('name', f'景点{i+1}'),
            "description": r.get('description', '')[:300],
            "score": r.get('rerank_score') or r.get('score', 0),
            "source": r.get('source', 'unknown')
        })

state["sources"] = sources

# 附近推荐（单独保存）
nearby_recommendations = []
if neo4j_results:
    for i, nr in enumerate(neo4j_results[:5]):  # Top 5附近
        if isinstance(nr, dict):
            nearby_recommendations.append({
                "name": nr.get('name', f'附近景点{i+1}'),
                "description": nr.get('description', '')[:300],
                "distance": nr.get('distance', '未知'),  # 如果有距离信息
                "type": nr.get('type', 'attraction')  # 景点/酒店/美食
            })

state["nearby_recommendations"] = nearby_recommendations
```

#### **3. 优化Prompt（可选）**

```python
# node_synthesizer.py 第88-103行

prompt = f"""作为专业的旅游顾问，根据以下信息生成详细且有帮助的推荐。

用户问题: {query}

检索到的景点信息:
{context}

{nearby_context}

请生成一个详细、结构清晰的回答，要求：
1. 直接回答用户的问题，重点介绍检索到的主要景点
2. 包含景点的特色、游玩建议、实用信息
3. 如果有附近景点信息，在回答末尾单独列出"附近推荐"章节
4. 提供交通、住宿、美食等实用建议
5. 语言生动易读，结构清晰，使用markdown格式

回答:"""
```

#### **4. 前端展示修改**

```vue
<!-- AIRecommend.vue -->

<!-- 主要来源 -->
<el-collapse-item name="sources">
  <template #title>
    <div style="display: flex; align-items: center; gap: 8px;">
      <el-icon><Document /></el-icon>
      <span>参考来源 ({{ msg.sources.length }}条)</span>
    </div>
  </template>
  <!-- sources展示 -->
</el-collapse-item>

<!-- 附近推荐 -->
<el-collapse-item 
  v-if="msg.nearby_recommendations && msg.nearby_recommendations.length > 0"
  name="nearby"
>
  <template #title>
    <div style="display: flex; align-items: center; gap: 8px;">
      <el-icon><LocationInformation /></el-icon>
      <span>附近推荐 ({{ msg.nearby_recommendations.length }}条)</span>
    </div>
  </template>
  <el-collapse>
    <el-collapse-item
      v-for="(nearby, idx) in msg.nearby_recommendations"
      :key="idx"
      :title="`${nearby.name}${nearby.distance ? ' - ' + nearby.distance : ''}`"
    >
      <div class="source-content">
        <p><strong>描述：</strong>{{ nearby.description }}</p>
        <p v-if="nearby.type"><strong>类型：</strong>{{ nearby.type }}</p>
      </div>
    </el-collapse-item>
  </el-collapse>
</el-collapse-item>
```

---

### **方案2：完整改进（可选）**

如果需要更强的附近推荐功能，还可以：

#### **1. 增强查询分析Prompt**

```python
# node_query_rewriter.py 第56-90行

prompt = f"""你是旅游领域的智能助手。请分析用户的查询并返回JSON格式的结果。

用户查询: {user_query}

请分析以下内容：
1. is_travel_related: 判断是否是旅游相关问题（景点、路线、住宿、美食、攻略等）
2. rewritten_query: 将查询重写为更适合检索的形式
3. entities: 提取地名、景点名等实体
4. needs_nearby_search: 是否需要附近推荐（包含"附近"、"周边"、"周围"、"附近酒店"、"附近美食"、"周边景点"等关键词）
5. nearby_type: 如果needs_nearby_search=true，判断类型：景点(attraction)/酒店(hotel)/美食(food)/全部(all)
6. expanded_keywords: 生成3-5个相关搜索关键词

输出JSON格式：
{{
  "is_travel_related": true/false,
  "rewritten_query": "重写后的查询",
  "entities": ["实体1", "实体2"],
  "needs_nearby_search": true/false,
  "nearby_type": "attraction/hotel/food/all",
  "expanded_keywords": "关键词1 关键词2 关键词3"
}}

示例：

- 输入: "推荐三清山附近的酒店"
  输出: {{"is_travel_related": true, "rewritten_query": "三清山 附近 酒店", "entities": ["三清山"], "needs_nearby_search": true, "nearby_type": "hotel", "expanded_keywords": "三清山住宿 三清山酒店 三清山客栈"}}

- 输入: "三清山周边有什么好吃的"
  输出: {{"is_travel_related": true, "rewritten_query": "三清山 周边 美食", "entities": ["三清山"], "needs_nearby_search": true, "nearby_type": "food", "expanded_keywords": "三清山美食 三清山餐厅 上饶美食"}}

只返回JSON，不要其他内容：
"""
```

#### **2. State添加nearby_type字段**

```python
# state.py
class AIRecommendState(TypedDict):
    # Query rewriter
    rewritten_query: str
    expanded_query: str
    entities: List[str]
    needs_nearby_search: bool
    nearby_type: str  # 新增：附近推荐类型
    # ...
```

#### **3. Neo4j节点根据类型查询**

```python
# node_neo4j_nearby.py

nearby_type = state.get("nearby_type", "all")

# 根据类型查询不同的关系
if nearby_type == "hotel":
    # 查询 NEARBY_HOTEL 关系
    pass
elif nearby_type == "food":
    # 查询 NEARBY_FOOD 关系
    pass
else:
    # 查询所有 NEARBY 关系
    pass
```

---

## 🎯 推荐实施步骤

### **阶段1：基础优化（推荐立即实施）**

1. ✅ State添加 `nearby_recommendations` 字段
2. ✅ Synthesizer节点分离附近推荐
3. ✅ 前端添加"附近推荐"展示区域
4. ✅ 测试基本功能

**工作量**：约30分钟
**效果**：附近推荐更清晰，用户体验提升

### **阶段2：功能增强（可选）**

1. ⏳ 查询分析Prompt增强（判断nearby_type）
2. ⏳ State添加 `nearby_type` 字段
3. ⏳ Neo4j节点支持分类查询
4. ⏳ 前端按类型显示图标

**工作量**：约1-2小时
**效果**：支持酒店、美食等分类推荐

---

## 📊 效果对比

### **当前效果**
```
参考来源 (5条)
  来源1: 女神 - 相关度: 94.8%
  来源2: 三清山 - 相关度: 92.3%
  来源3: 玉清台 - 相关度: 92.1%
  来源4: 三清宫 - 附近
  来源5: 西海岸 - 附近
```

### **改进后效果**
```
参考来源 (3条)
  来源1: 女神 - 相关度: 94.8%
  来源2: 三清山 - 相关度: 92.3%
  来源3: 玉清台 - 相关度: 92.1%

附近推荐 (5条)
  🗺️ 三清宫 - 距离: 2.5km
  🗺️ 西海岸景区 - 距离: 3.0km
  🗺️ 南清园 - 距离: 1.8km
  🏨 三清山国际度假村 - 距离: 5.0km
  🍜 山庄餐厅 - 距离: 2.0km
```

---

## 🚀 立即开始

建议从**阶段1（基础优化）**开始：

1. 修改 `state.py` 添加字段
2. 修改 `node_synthesizer.py` 分离附近推荐
3. 修改前端 `AIRecommend.vue` 添加展示
4. 测试功能

**是否开始实施？**
