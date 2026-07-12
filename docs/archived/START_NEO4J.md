# 快速启动Neo4j - 命令清单

## 🚀 在命令提示符(CMD)中执行

```bash
# 1. 停止旧容器（如果存在）
docker stop neo4j
docker rm neo4j

# 2. 启动新的Neo4j容器
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.14

# 3. 等待15秒后检查状态
docker ps --filter "name=neo4j"

# 4. 查看日志确认启动成功
docker logs neo4j --tail 20
```

## ✅ 启动成功的标志

日志中应该看到：
```
Started.
Remote interface available at http://localhost:7474/
```

## 🔗 连接信息

- **Bolt协议**: `bolt://localhost:7687`
- **Web界面**: `http://localhost:7474`
- **用户名**: `neo4j`
- **密码**: `password`

## 📝 后续步骤

1. 访问 http://localhost:7474 验证Neo4j运行正常
2. 重启后端，Neo4j连接错误应该消失
3. 修改前端RRFRecommend.vue，恢复使用graph_rag模型

---

**直接复制上面的命令到CMD执行即可！**
