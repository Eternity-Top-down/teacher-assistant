import httpx

from .config import settings


def fallback_feedback(lesson_summary: str, performance_summary: str) -> str:
    performance = performance_summary or "课堂整体配合度较好，能够跟随老师的引导完成主要学习任务。"
    return f"""本次学习内容：
本次课程主要围绕“{lesson_summary}”展开，课堂中对核心知识点进行了梳理，并结合例题帮助学生理解和应用。

课堂表现：
{performance} 学生在课堂中能够积极回应问题，对已经掌握的内容有一定表达能力。

问题分析：
目前需要重点关注的是知识点之间的迁移应用能力。部分题目在条件变化后，学生容易出现思路不够稳定的情况，需要继续通过典型题型巩固。

课后建议：
建议课后完成 2-3 道同类型练习，并把解题步骤写完整。下次课可以先用一道复习题检查掌握情况，再逐步提高题目综合度。

给家长的总结：
本次课学生整体状态不错，已经对本节重点内容建立了初步理解。后续建议保持规律练习，帮助知识从“听懂”进一步转化为“会独立完成”。
"""


async def generate_feedback(lesson_summary: str, performance_summary: str) -> str:
    if not settings.ai_api_key:
        return fallback_feedback(lesson_summary, performance_summary)

    prompt = f"""
你是一名有经验的一对一辅导老师。请根据老师输入的真实课堂记录，生成一份适合发给家长的中文课后反馈。

要求：
1. 语言专业、温暖、具体，不夸张。
2. 不要编造过多未提供的事实。
3. 输出固定为五个小标题：本次学习内容、课堂表现、问题分析、课后建议、给家长的总结。
4. 每个小标题下写 1-3 句话。

课程内容简述：
{lesson_summary}

学生课堂表现简述：
{performance_summary or "老师未额外填写，请根据课程内容保持客观表述。"}
""".strip()

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "你是擅长撰写一对一课后反馈的教学助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.ai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
