"""
测试后端SSE接口，检查complete事件是否包含answer字段
"""
import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def test_sse_complete_event():
    """测试SSE complete事件是否包含answer"""

    # 1. 生成session_id
    session_id = f"test_session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    print(f"Session ID: {session_id}")
    print("=" * 80)

    # 2. 发起查询请求
    print("\n[步骤1] 发起查询请求...")
    query_url = f"{BASE_URL}/api/ai-recommend/query"
    query_payload = {
        "query": "推荐一下三清山的旅游攻略",
        "session_id": session_id
    }

    try:
        response = requests.post(query_url, json=query_payload, timeout=10)
        print(f"查询请求状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"查询请求响应: {response.json()}")
        else:
            print(f"查询请求失败: {response.text}")
            return
    except Exception as e:
        print(f"查询请求异常: {e}")
        return

    # 3. 等待一段时间让workflow执行
    print("\n[步骤2] 等待workflow执行...")
    time.sleep(15)  # 等待15秒

    # 4. 连接SSE事件流
    print(f"\n[步骤3] 连接SSE事件流...")
    events_url = f"{BASE_URL}/api/ai-recommend/events/{session_id}"
    print(f"SSE URL: {events_url}")

    try:
        with requests.get(events_url, stream=True, timeout=30) as response:
            print(f"SSE连接状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"SSE连接失败: {response.text}")
                return

            print("\n[步骤4] 接收SSE事件...")
            print("=" * 80)

            event_type = None
            event_data = ""
            complete_event_found = False

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        event_data = line.split(":", 1)[1].strip()

                        # 解析并打印事件
                        try:
                            data = json.loads(event_data)

                            if event_type == "complete":
                                complete_event_found = True
                                print(f"\n{'='*80}")
                                print(f"🎯 找到COMPLETE事件！")
                                print(f"{'='*80}")
                                print(f"\n事件类型: {event_type}")
                                print(f"\n完整数据:")
                                print(json.dumps(data, indent=2, ensure_ascii=False))
                                print(f"\n数据键列表: {list(data.keys())}")
                                print(f"\n关键字段检查:")
                                print(f"  - answer in data: {'answer' in data}")
                                print(f"  - sources in data: {'sources' in data}")

                                if "answer" in data:
                                    answer_len = len(data["answer"])
                                    print(f"  - answer长度: {answer_len} 字符")
                                    print(f"  - answer前100字符: {data['answer'][:100]}...")
                                else:
                                    print(f"  ❌ answer字段不存在！")

                                if "sources" in data:
                                    print(f"  - sources数量: {len(data['sources'])}")
                                else:
                                    print(f"  ❌ sources字段不存在！")

                                print(f"\n{'='*80}")
                                break  # 收到complete就结束

                            else:
                                # 其他事件简要打印
                                step_name = data.get("step_name", data.get("step", ""))
                                print(f"[{event_type}] {step_name}")

                        except json.JSONDecodeError as e:
                            print(f"JSON解析失败: {e}")
                            print(f"原始数据: {event_data[:200]}")

                        event_type = None
                        event_data = ""

            if not complete_event_found:
                print(f"\n❌ 未收到complete事件！")

    except requests.exceptions.Timeout:
        print(f"\n❌ SSE连接超时")
    except Exception as e:
        print(f"\n❌ SSE连接异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SSE Complete事件测试")
    print("="*80)
    test_sse_complete_event()
    print("\n" + "="*80)
    print("测试完成")
    print("="*80 + "\n")
