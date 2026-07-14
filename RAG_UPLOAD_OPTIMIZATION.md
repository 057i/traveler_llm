# RAG上传优化记录

## 已完成

### 1. Semaphore并发限制
- 文件：app/api/documents.py
- 改动：添加 processing_semaphore = Semaphore(2)
- 效果：限制最多2个文档同时处理

## 待实施

### 2. 列表查询缓存
- 文件：app/api/documents.py
- 改动：list_documents函数添加2秒缓存
- 效果：减少Redis查询压力

### 3. 前端降频刷新  
- 文件：frontend/src/views/DocumentManager.vue
- 改动：添加最少3秒刷新间隔
- 效果：减少请求频率

## 性能分析

### 为什么不用BackgroundTasks？
- RAG处理是长任务（5-30分钟）
- BackgroundTasks适合短任务（<5分钟）
- 当前asyncio.create_task更合适

### 为什么不用线程池？
- 任务65%是IO密集型
- 已使用async/await架构
- Semaphore轻量且高效
- 线程池开销大且需重构

## 实施日期
2026-07-14 15:32:14
