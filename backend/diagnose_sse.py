import requests
import json
import time

BASE_URL = "http://localhost:8000"
session_id = "session_1783830930683_766apgr44"

print("=" * 80)
print("诊断SSE事件流")
print("=" * 80)

# 连接SSE
events_url = f"{BASE_URL}/api/ai-recommend/events/{session_id}"
print(f"\n连接: {events_url}\n")

try:
    with requests.get(events_url, stream=True, timeout=10) as response:
        print(f"状态码: {response.status_code}\n")
        
        event_type = None
        event_count = 0
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                event_data = line.split(":", 1)[1].strip()
                event_count += 1
                
                try:
                    data = json.loads(event_data)
                    
                    # 打印事件摘要
                    if event_type == "result":
                        print(f"\n{'='*60}")
                        print(f"[{event_count}] RESULT事件!")
                        print(f"{'='*60}")
                        print(f"Keys: {list(data.keys())}")
                        print(f"Has answer: {'answer' in data}")
                        if 'answer' in data:
                            print(f"Answer length: {len(data['answer'])}")
                            print(f"Answer preview: {data['answer'][:100]}...")
                        print(f"Has sources: {'sources' in data}")
                        if 'sources' in data:
                            print(f"Sources count: {len(data['sources'])}")
                        print(f"{'='*60}\n")
                    elif event_type == "complete":
                        print(f"\n[{event_count}] COMPLETE事件")
                        print(f"Keys: {list(data.keys())}")
                        print(f"Message: {data.get('message')}")
                        print()
                        break
                    else:
                        step_name = data.get("step_name", data.get("step", ""))
                        print(f"[{event_count}] {event_type}: {step_name}")
                        
                except json.JSONDecodeError:
                    print(f"[{event_count}] {event_type}: [解析失败]")
                    
                event_type = None
                
except requests.exceptions.Timeout:
    print("\n超时")
except Exception as e:
    print(f"\n错误: {e}")

print("\n" + "=" * 80)
print(f"共接收 {event_count} 个事件")
print("=" * 80)
