import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

print("="*80)
print("测试Result事件")
print("="*80)

# 生成新session
session_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:6]}"
print(f"\nSession ID: {session_id}\n")

# 发起查询
print("[1] 发起查询...")
try:
    resp = requests.post(
        f"{BASE_URL}/api/ai-recommend/query",
        json={"query": "推荐三清山", "session_id": session_id},
        timeout=5
    )
    print(f"状态: {resp.status_code}")
except Exception as e:
    print(f"失败: {e}")
    exit(1)

# 连接SSE
print("\n[2] 连接SSE...")
events_url = f"{BASE_URL}/api/ai-recommend/events/{session_id}"

result_received = False
answer_content = None

try:
    with requests.get(events_url, stream=True, timeout=60) as response:
        print(f"连接状态: {response.status_code}\n")
        
        event_type = None
        count = 0
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                event_data = line.split(":", 1)[1].strip()
                count += 1
                
                try:
                    data = json.loads(event_data)
                    
                    if event_type == "result":
                        result_received = True
                        answer_content = data.get("answer", "")
                        
                        print("\n" + "="*80)
                        print("收到RESULT事件！")
                        print("="*80)
                        print(f"Answer长度: {len(answer_content)}")
                        print(f"Answer前200字符:\n{answer_content[:200]}")
                        print("="*80 + "\n")
                    
                    elif event_type == "complete":
                        print(f"[{count}] COMPLETE")
                        break
                    
                    elif event_type in ["node_start", "node_end"]:
                        step = data.get("step_name", data.get("step", ""))
                        print(f"[{count}] {event_type}: {step}")
                    
                except:
                    pass
                
                event_type = None
        
        print("\n" + "="*80)
        if result_received and answer_content:
            print(f"✓ 测试成功！收到answer {answer_content}")
        else:
            print("✗ 测试失败！")
            if not result_received:
                print("  - 没有收到result事件")
            elif not answer_content:
                print("  - result事件中answer为空")
        print("="*80)
        
except Exception as e:
    print(f"\n异常: {e}")