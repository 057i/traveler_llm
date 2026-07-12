# 前端路由规范化文档

## ✅ 已完成的优化

### 1. 路由命名规范化

#### 规范前（旧路由）
```javascript
/sse          → SSERecommend
/rrf          → RRFRecommend
/chat         → ChatRecommend
/websocket    → WebSocketChat
/documents    → DocumentManager
```

#### 规范后（新路由）
```javascript
/ai-recommend       → AIRecommend       (AI推荐 - 多智能体工作流)
/ai-team-recommend  → AITeamRecommend   (AI团队推荐 - 传统RAG)
/rrf-recommend      → RRFRecommend      (RRF融合推荐)
/sse-recommend      → SSERecommend      (SSE实时推荐 - 已弃用)
/documents          → DocumentManager   (RAG文档管理)
```

### 2. 路由规范

#### 命名规则
- **URL路径**: 使用 kebab-case（短横线分隔）
  - ✅ `/ai-recommend`
  - ❌ `/aiRecommend`
  - ❌ `/ai_recommend`

- **路由名称**: 使用 PascalCase（大驼峰）
  - ✅ `AIRecommend`
  - ❌ `aiRecommend`
  - ❌ `ai-recommend`

- **组件名称**: 使用 PascalCase
  - ✅ `ChatRecommend`
  - ❌ `chatRecommend`

#### 语义化
- 路由名称应清晰表达功能
- 使用完整单词而非缩写（除非缩写非常通用）
- 分组相关路由（如所有推荐功能以 `-recommend` 结尾）

### 3. Meta信息增强

每个路由现在包含完整的meta信息：

```javascript
{
  path: '/ai-recommend',
  name: 'AIRecommend',
  component: ChatRecommend,
  meta: {
    title: 'AI推荐',                        // 页面标题
    icon: 'ChatDotRound',                   // 菜单图标
    description: '使用多智能体工作流进行智能推荐'  // 功能描述
  }
}
```

### 4. 兼容性处理

为保持向后兼容，旧路由会自动重定向到新路由：

```javascript
// 兼容旧路由（重定向）
{
  path: '/chat',
  redirect: '/ai-recommend'
},
{
  path: '/websocket',
  redirect: '/ai-team-recommend'
},
{
  path: '/rrf',
  redirect: '/rrf-recommend'
},
{
  path: '/sse',
  redirect: '/sse-recommend'
}
```

## 📋 完整路由表

| 新路由 | 旧路由（兼容） | 路由名称 | 页面标题 | 功能说明 |
|--------|--------------|---------|---------|---------|
| `/ai-recommend` | `/chat` | `AIRecommend` | AI推荐 | 多智能体工作流推荐 |
| `/ai-team-recommend` | `/websocket` | `AITeamRecommend` | AI团队推荐 | 传统RAG流程推荐 |
| `/rrf-recommend` | `/rrf` | `RRFRecommend` | RRF融合推荐 | RRF融合多源检索 |
| `/sse-recommend` | `/sse` | `SSERecommend` | SSE实时推荐 | SSE流式推荐（已弃用） |
| `/documents` | - | `DocumentManager` | RAG文档管理 | 知识库文档管理 |

## 🔧 修复的问题

### 1. ChromaDB统计错误
**错误**: `object of type 'int' has no len()`

**原因**: `chroma_client.count()` 返回值处理不当

**修复**:
```python
# 修复前
chroma_count = chroma_client.count()

# 修复后
try:
    count_result = chroma_client.count()
    chroma_count = int(count_result) if count_result is not None else 0
except Exception as e:
    logger.error(f"获取 ChromaDB 统计失败: {e}")
    chroma_count = 0
```

## 📝 使用建议

### 前端导航
推荐使用路由名称进行导航，而不是路径：

```javascript
// ✅ 推荐
router.push({ name: 'AIRecommend' })

// ❌ 不推荐
router.push('/ai-recommend')
```

### 链接生成
使用命名路由生成链接：

```vue
<!-- ✅ 推荐 -->
<router-link :to="{ name: 'AIRecommend' }">AI推荐</router-link>

<!-- ❌ 不推荐 -->
<router-link to="/ai-recommend">AI推荐</router-link>
```

## 🚀 后续优化建议

1. **路由懒加载**: 使用动态import提升性能
   ```javascript
   component: () => import('@/views/ChatRecommend.vue')
   ```

2. **路由权限控制**: 添加权限验证
   ```javascript
   meta: {
     requiresAuth: true,
     roles: ['admin', 'user']
   }
   ```

3. **面包屑导航**: 利用meta信息自动生成面包屑
   ```javascript
   meta: {
     breadcrumb: ['首页', 'AI推荐']
   }
   ```

4. **页面缓存**: 配置keep-alive
   ```javascript
   meta: {
     keepAlive: true
   }
   ```
