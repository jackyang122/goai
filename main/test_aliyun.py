"""
测试阿里云 Qwen 连接
"""
import os
from openai import OpenAI

# 从环境变量获取 API Key
api_key = os.getenv("DASHSCOPE_API_KEY", "sk-a525401e790f47b398f04e842abdb4da")

client = OpenAI(
    api_key=api_key,
    base_url="https://llm-5b9b6pwwik5hloih.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)

messages = [{"role": "user", "content": "你是谁"}]

print("正在测试阿里云 Qwen3.6-Plus 模型...")
print("=" * 50)

try:
    completion = client.chat.completions.create(
        model="qwen3.6-plus",
        messages=messages,
        extra_body={"enable_thinking": True},
        stream=True
    )

    is_answering = False
    print("\n" + "=" * 20 + "思考过程" + "=" * 20)

    for chunk in completion:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            if not is_answering:
                print(delta.reasoning_content, end="", flush=True)

        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n" + "=" * 20 + "完整回复" + "=" * 20)
                is_answering = True
            print(delta.content, end="", flush=True)

    print("\n" + "=" * 50)
    print("✅ 测试成功！")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    print(f"错误类型: {type(e).__name__}")
