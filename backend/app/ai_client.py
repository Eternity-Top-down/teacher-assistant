from pathlib import Path

import httpx

from .config import settings


EXAMPLES_PATH = Path(__file__).resolve().parent / "prompt_examples" / "feedback_examples.txt"


def read_format_examples() -> str:
    try:
        return EXAMPLES_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def fallback_feedback(
    student_name: str,
    subject: str,
    lesson_number: int,
    lesson_date: str,
    lesson_summary: str,
    performance_summary: str,
) -> str:
    subject_name = subject or "数学"
    performance = performance_summary or "课堂整体配合度较好，能够跟随老师的引导完成主要学习任务。"
    return f"""{student_name}第{lesson_number}次{subject_name}课（{lesson_date}）

📖1.课堂学习内容：

① 本节课主要围绕老师记录的内容进行讲解与练习：

1. {lesson_summary}

✨2.课堂表现与知识掌握情况：

① {student_name}{performance}

② 从本次课堂情况来看，{student_name}对本节课涉及的基础内容有了一定理解，能够在老师引导下梳理做题思路。

③ 后续还需要结合类似题型继续巩固，把课堂中讲到的方法真正转化为自己可以独立完成的解题能力。

📌3.课后建议与作业安排：

① 课后重点复习本次课堂学习的内容，尤其是课堂中讲解过的题型和容易出错的步骤。

② 做题时注意规范书写步骤，不急不躁，尽量减少计算和审题上的失误。

③ 下次课会先检查本次内容的掌握情况，再继续针对薄弱环节做讲解和练习。"""


async def generate_feedback(
    student_name: str,
    subject: str,
    lesson_number: int,
    lesson_date: str,
    lesson_summary: str,
    performance_summary: str,
) -> str:
    if not settings.ai_api_key:
        return fallback_feedback(
            student_name,
            subject,
            lesson_number,
            lesson_date,
            lesson_summary,
            performance_summary,
        )

    subject_name = subject or "数学"
    examples = read_format_examples()
    prompt = f"""
你是一名一对一辅导老师，需要根据“本次课堂输入”直接写出可以发给家长的课后反馈正文。

重要规则：
1. 只输出反馈正文，不要出现“好的”“以下是”“根据您的课堂记录”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 旧反馈样例只用于学习格式、语气、段落详略和编号方式，禁止复用样例中的课程内容、学生表现、问题描述或原句。
4. 新反馈的具体知识点、课堂表现、问题和建议只能来自“本次课堂输入”；如果输入没有提供，不要编造具体事实。
5. 语气自然、具体、克制，像老师写给家长的课后记录，少用“扎实基础、奠定基础、逐步提升”等 AI 套话。

必须使用以下固定结构：
{student_name}第{lesson_number}次{subject_name}课（{lesson_date}）

📖1.课堂学习内容：

① ...

1. ...

✨2.课堂表现与知识掌握情况：

① ...

② ...

📌3.课后建议与作业安排：

① ...

② ...

旧反馈格式样例（只学格式，不学内容）：
{examples}

本次课堂输入：
学生姓名：{student_name}
课程科目：{subject_name}
课程标题：{student_name}第{lesson_number}次{subject_name}课（{lesson_date}）

课程内容简述：
{lesson_summary}

课堂表现简述：
{performance_summary or "老师未额外填写，请只根据课程内容做客观、保守表述。"}
""".strip()

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "你只输出一对一课后反馈正文，不进行对话解释。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.55,
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
