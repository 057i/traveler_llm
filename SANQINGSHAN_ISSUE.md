# 三清山数据搜索问题诊断

## 问题描述
上传三清山文档后，AI推荐功能搜索不到相关数据

## 症状
- 文档列表显示上传成功
- Neo4j有实体数据
- 但搜索返回"没有收录关于三清山的信息"

## 根本原因
RAG向量化失败：DataNotMatchException (expect 17, got 12)

## 已排查
1. ✅ Milvus Collection确实有17个字段
2. ✅ 代码应该构造17个字段
3. ❌ 实际只传了12个字段

## 待确认
需要查看调试日志：
- [RAG] First entry field count
- [RAG] First entry fields

## 诊断日期
2026-07-14 17:37:12
