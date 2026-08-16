"""
测试 Book 功能的 LLM 调用方式
"""
import openai

config = {
    "api_key": "sk-a525401e790f47b398f04e842abdb4da",
    "base_url": "https://llm-5b9b6pwwik5hloih.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3.6-plus"
}

print("=== 测试 Book 功能可能的 LLM 调用方式 ===")

client = openai.OpenAI(
    api_key=config["api_key"],
    base_url=config["base_url"]
)

# 测试1: 基础调用
print("\n[测试1] 基础调用（非流式）")
try:
    response = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=100
    )
    print(f"成功: {response.choices[0].message.content[:50]}...")
except Exception as e:
    print(f"失败: {e}")

# 测试2: 流式调用（带 thinking）
print("\n[测试2] 流式调用（带 enable_thinking）")
try:
    completion = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": "你好"}],
        extra_body={"enable_thinking": True},
        stream=True,
        max_tokens=100
    )

    content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content

    if content:
        print(f"成功: {content[:50]}...")
    else:
        print("失败: 返回空内容")

except Exception as e:
    print(f"失败: {e}")

# 测试3: 不带 thinking 的流式调用
print("\n[测试3] 流式调用（不带 thinking）")
try:
    completion = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": "你好"}],
        stream=True,
        max_tokens=100
    )

    content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content

    if content:
        print(f"成功: {content[:50]}...")
    else:
        print("失败: 返回空内容")

except Exception as e:
    print(f"失败: {e}")

# 测试4: 模拟 Book 的大纲生成请求
print("\n[测试4] 模拟 Book 大纲生成")
try:
    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "user", "content": "为一本关于 Python 编程的教程创建大纲，包含5个章节"}
        ],
        max_tokens=500
    )
    print(f"成功: {response.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"失败: {e}")
