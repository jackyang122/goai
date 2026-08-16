"""
测试 DeepTutor LLM 配置
"""
import json
import requests

# 读取配置文件
config_path = "C:/project/work/eduAgent/goai/deeptutor-ref/data/user/settings/model_catalog.json"

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    llm_config = config['services']['llm']
    active_profile = next((p for p in llm_config['profiles'] if p['id'] == llm_config['active_profile_id']), None)

    if not active_profile:
        print("错误: 没有激活的 LLM 配置")
    else:
        print("=== 当前 LLM 配置 ===")
        print(f"提供商: {active_profile['provider']}")
        print(f"Base URL: {active_profile['base_url']}")
        print(f"激活模型: {llm_config['active_model_id']}")

        # 测试连接
        print("\n=== 测试 LLM 连接 ===")

        import openai
        client = openai.OpenAI(
            api_key=active_profile['api_key'],
            base_url=active_profile['base_url']
        )

        try:
            response = client.chat.completions.create(
                model=llm_config['active_model_id'],
                messages=[{"role": "user", "content": "你好，请简短回复"}],
                max_tokens=50
            )
            print("[OK] 连接成功！")
            print(f"回复: {response.choices[0].message.content}")

        except Exception as e:
            print(f"[ERROR] 连接失败: {e}")
            print(f"错误类型: {type(e).__name__}")

except Exception as e:
    print(f"读取配置文件失败: {e}")
