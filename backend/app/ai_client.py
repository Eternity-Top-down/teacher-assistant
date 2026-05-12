import json
import random
import re
from pathlib import Path

import httpx

from .ai_settings import AIConfig
from .config import settings


EXAMPLES_PATH = Path(__file__).resolve().parent / "prompt_examples" / "feedback_examples.txt"
TITLE_EMOJIS = {
    "lesson": ["📚", "📝", "📖", "📘", "📗", "📙", "🔢", "🧮", "🧠", "💭", "🔎", "📌"],
    "performance": ["🌟", "✅", "💡", "👏", "💪", "🎉", "🙂", "🙌", "🔥", "🌱", "⭐", "👌"],
    "advice": ["🎯", "💪", "🔍", "🧭", "🚀", "📈", "🪄", "🧩", "🔑", "🛠️", "🌈", "🏁"],
    "homework": ["✏️", "📌", "📒", "📋", "🗒️", "📎", "🖊️", "✅", "📍", "🧾", "📔", "📝"],
}


def pick_title_emojis() -> dict[str, str]:
    return {key: random.choice(values) for key, values in TITLE_EMOJIS.items()}


def student_display_name(full_name: str) -> str:
    name = full_name.strip()
    if not name:
        return name
    if all("\u4e00" <= char <= "\u9fff" for char in name):
        if len(name) == 2:
            return name[1:]
        if len(name) >= 3:
            return name[-2:]
    return name


def strip_title_date(title: str) -> str:
    value = title.strip()
    if value.endswith("）"):
        start = value.rfind("（")
        if start != -1:
            inside = value[start + 1 : -1]
            if "." in inside and all(part.isdigit() for part in inside.split(".", 1)):
                return value[:start].strip()
    return value


def title_with_date(title: str, lesson_date: str) -> str:
    base = strip_title_date(title)
    return f"{base}（{lesson_date}）" if lesson_date and base else base


def read_format_examples() -> str:
    try:
        return EXAMPLES_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def fallback_feedback(
    student_name: str,
    subject: str,
    lesson_number: int,
    lesson_title: str,
    lesson_date: str,
    lesson_summary: str,
    performance_summary: str,
    advice_summary: str,
    homework_plan: str,
    supplement_summary: str = "",
) -> str:
    subject_name = subject or "数学"
    display_name = student_display_name(student_name)
    emojis = pick_title_emojis()
    raw_title = lesson_title or f"{display_name}第{lesson_number}次{subject_name}课"
    title = title_with_date(raw_title, lesson_date)
    performance = performance_summary or "老师本次未填写具体课堂表现，建议后续结合课堂观察继续补充。"
    advice = advice_summary or "课后建议围绕本节课内容及时复习，整理课堂中讲到的方法和容易出错的地方，再结合类似题型做巩固。"
    if supplement_summary:
        advice = f"{advice}\n\n课堂补充信息：{supplement_summary}"
    homework = homework_plan or "本次老师未填写具体作业安排。"
    return f"""{title}

{emojis["lesson"]} 1. 课堂学习内容：

本节课主要围绕以下内容进行学习和练习：

1. {lesson_summary}

{emojis["performance"]} 2. 课堂表现与知识掌握情况：

{performance}

{emojis["advice"]} 3. 课后建议：

{advice}

{emojis["homework"]} 4. 作业安排：

{homework}"""


async def generate_feedback(
    student_name: str,
    subject: str,
    lesson_number: int,
    lesson_title: str,
    lesson_date: str,
    lesson_summary: str,
    performance_summary: str,
    advice_summary: str,
    homework_plan: str,
    supplement_summary: str = "",
    style_examples: list[dict] | None = None,
    ai_config: AIConfig | None = None,
) -> str:
    config = ai_config or AIConfig(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        provider="env",
    )
    if not config.api_key:
        return fallback_feedback(
            student_name,
            subject,
            lesson_number,
            lesson_title,
            lesson_date,
            lesson_summary,
            performance_summary,
            advice_summary,
            homework_plan,
            supplement_summary,
        )

    subject_name = subject or "数学"
    display_name = student_display_name(student_name)
    examples = read_format_examples()
    raw_title = lesson_title or f"{display_name}第{lesson_number}次{subject_name}课"
    title = title_with_date(raw_title, lesson_date)
    style_text = "\n\n".join(
        f"样例{index}：\n{example.get('content', '').strip()}"
        for index, example in enumerate(style_examples or [], start=1)
        if example.get("content", "").strip()
    )
    has_style_examples = bool(style_text)
    emojis = pick_title_emojis()
    shared_rules = f"""
你是一名一对一辅导老师，需要根据“本次课堂输入”直接写出可以发给家长的课后反馈正文。

重要规则：
1. 只输出反馈正文，不要出现“好的”“以下是”“根据您的课堂记录”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 内置表达原则和老师个人风格样例只用于学习语气、段落详略、措辞习惯，禁止复用其中的课程内容、学生表现、问题描述、作业内容或原句。
4. 新反馈的具体知识点、课堂表现、问题、建议和作业只能来自“本次课堂输入”；如果输入没有提供，不要编造具体事实。
5. 语气自然、具体、克制，像老师写给家长的课后记录，少用“扎实基础、奠定基础、逐步提升”等空泛套话。
6. 反馈标题和正文称呼学生时只使用“{display_name}”，不要使用完整姓名“{student_name}”。
7. 作业安排必须严格根据老师输入润色；如果老师未输入作业安排，不得自行安排作业。
8. 老师输入可能是一句话、流水账或无序文本；生成前请先提取事实并分点归纳，再组织反馈正文。
9. 归纳时：课堂学习内容提取知识点、题型、方法和练习内容；课堂表现提取课堂状态、掌握较好处和薄弱点；课后建议提取可执行建议；作业安排严格按老师输入整理。

内置优秀表达原则（只学习表达方式）：
1. 先具体肯定学生做得好的地方，再温和指出需要关注的问题。
2. 建议要可执行，例如“复盘错题原因”“整理解题步骤”“复述本节方法”，避免空泛鼓励。
3. 用家长容易看懂的表达，不堆砌教学术语。

旧反馈格式样例（只学格式，不学内容）：
{examples}

老师个人风格样例（只学语气和表达习惯，不学事实）：
{style_text or "老师暂未提供个人风格样例，本次必须按标准四段结构生成。"}

本次课堂输入：
学生完整姓名：{student_name}
反馈使用称呼：{display_name}
课程科目：{subject_name}
课程标题：{title}

课程内容简述：
{lesson_summary}

课堂表现简述：
{performance_summary or "老师未额外填写，请只根据课程内容做客观、保守表述。"}

课后建议要点：
{advice_summary or "老师未额外填写，请根据已输入的问题做保守、可执行建议；不要编造具体问题。"}

作业安排：
{homework_plan or "老师未填写具体作业安排。"}

内容补充：
{supplement_summary or "老师未额外填写内容补充；请以四大板块事实为主生成。"}
""".strip()

    if has_style_examples:
        prompt = f"""
{shared_rules}

生成模式：个人风格。
要求：
1. 优先学习老师个人风格样例的排版、分段、语气、详略和常用表达习惯。
2. 不强制使用四段标题，也不强制使用标题 emoji。
3. 可以保留清楚的小标题，但不要机械套用“课堂学习内容/课堂表现/课后建议/作业安排”四标题。
4. 必须覆盖本次课堂输入里的课程内容、课堂表现、课后建议和作业安排；如果某项没有输入，只能做保守说明。
5. 如果老师填写了作业安排，必须体现；如果没有填写，不要编造作业。
6. 如果老师填写了内容补充，可将其作为额外事实来源合并进相关段落，但不得替代四大板块内容。
""".strip()
    else:
        prompt = f"""
{shared_rules}

生成模式：结构化反馈。
额外规则：
1. 标题前必须使用指定 emoji，每个标题前有且只有 1 个 emoji；正文不要额外大量添加 emoji。
2. 作业安排如果未填写，第 4 段写“本次老师未填写具体作业安排。”
3. 如果老师填写了内容补充，可在覆盖四段内容的前提下合并到相关段落，不得忽略任何一段。

必须使用以下固定结构：
{title}

{emojis["lesson"]} 1. 课堂学习内容：

总结本节课学习的知识点，尽量条目化，方便学生复习和回顾。

{emojis["performance"]} 2. 课堂表现与知识掌握情况：

总结学生课堂状态、掌握较好的地方、掌握不好且需要关注的地方。没有输入的表现不要编造。

{emojis["advice"]} 3. 课后建议：

根据学生存在的问题提出有效可行的帮助方案。建议必须能对应到老师输入的事实。

{emojis["homework"]} 4. 作业安排：

严格根据老师输入的作业安排进行润色，不新增作业。
""".strip()

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你只输出一对一课后反馈正文，不进行对话解释。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.55,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{config.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def _extract_json_object(text: str) -> dict:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("图片识别结果不是 JSON")
        return json.loads(cleaned[start : end + 1])


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


async def analyze_lesson_materials(
    student_name: str,
    subject: str,
    lesson_title: str,
    images: list[dict],
    ai_config: AIConfig,
) -> dict:
    subject_name = subject or "数学"
    prompt = f"""
你是一名一对一辅导老师的课堂资料整理助手。请综合识别老师上传的多张课堂资料图片，帮助老师填写“课堂学习内容”。

资料可能包括：试卷页、习题集、课堂讲义、错题照片、作业批改痕迹、课堂练习截图。

重要规则：
1. 只识别图片里能看清的内容，不要猜测模糊、被遮挡或看不完整的题目。
2. 输出面向老师备课和填写课后反馈，不要直接生成给家长看的反馈正文。
3. 聚焦本节课涉及的知识点、题型、课堂练习内容、易错点或薄弱点。
4. 如果图片包含答案、批改痕迹或错题标记，可以提炼错题类型和易错点，但不要评价学生态度。
5. 多张图片要综合提炼，不要逐张分散罗列。
6. 只输出 JSON，不要 Markdown，不要解释。

学生：{student_name}
科目：{subject_name}
课程标题：{lesson_title or "未填写"}

请按以下 JSON 结构输出：
{{
  "knowledge_points": ["知识点1", "知识点2"],
  "question_types": ["题型1", "题型2"],
  "practice_summary": "用一段话概括这些资料中的课堂练习内容",
  "weak_points": ["易错点或需要复习的点1", "易错点或需要复习的点2"],
  "lesson_summary_suggestion": "可直接填入课堂学习内容的一段总结，条理清楚，适合老师继续修改"
}}
""".strip()

    content = [{"type": "text", "text": prompt}]
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image['mime_type']};base64,{image['data_base64']}",
                },
            }
        )

    payload = {
        "model": ai_config.model,
        "messages": [
            {"role": "system", "content": "你只输出严格 JSON，用于老师整理课堂图片资料。"},
            {"role": "user", "content": content},
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{ai_config.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {ai_config.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()

    parsed = _extract_json_object(raw)
    result = {
        "knowledge_points": _string_list(parsed.get("knowledge_points")),
        "question_types": _string_list(parsed.get("question_types")),
        "practice_summary": str(parsed.get("practice_summary", "")).strip(),
        "weak_points": _string_list(parsed.get("weak_points")),
        "lesson_summary_suggestion": str(parsed.get("lesson_summary_suggestion", "")).strip(),
    }
    if not result["lesson_summary_suggestion"]:
        raise ValueError("图片识别结果缺少课堂学习内容建议")
    return result


def fallback_evening_monthly_feedback(
    student_name: str,
    feedback_month: str,
    homework_summary: str,
) -> str:
    return f"""{student_name}{feedback_month}晚辅作业完成情况反馈：

本月晚辅中，{student_name}的作业完成情况主要表现为：{homework_summary}

从整体情况来看，孩子能够完成本月主要作业任务，但仍需要继续关注作业订正、计算细节和独立思考过程。后续建议在完成作业时尽量保持步骤完整，遇到不会的题目及时标记并主动提问，避免问题积累。

下个月晚辅会继续关注{student_name}的作业完成质量和错题订正情况，帮助孩子逐步养成更稳定的数学作业习惯。"""


async def generate_evening_monthly_feedback(
    student_name: str,
    grade: str,
    school: str,
    feedback_month: str,
    homework_summary: str,
    ai_config: AIConfig | None = None,
) -> str:
    config = ai_config or AIConfig(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        provider="env",
    )
    if not config.api_key:
        return fallback_evening_monthly_feedback(student_name, feedback_month, homework_summary)

    student_info = "，".join(part for part in [student_name, grade, school] if part)
    prompt = f"""
你是一名晚辅老师，需要根据老师输入的“本月该学生数学作业完成情况简述”，直接写一份可以发给家长的月度反馈正文。

要求：
1. 只输出反馈正文，不要出现“好的”“以下是”“根据您的描述”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 只根据本次输入生成，不要编造没有提供的具体事实。
4. 语气自然、具体、克制，适合发给家长。
5. 内容重点围绕：作业完成情况、作业质量/订正情况、存在问题、下月建议。
6. 不强制固定标题格式，但正文要完整、清楚、方便老师修改。

学生信息：{student_info or student_name}
反馈月份：{feedback_month}
本月作业完成情况简述：
{homework_summary}
""".strip()

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你只输出晚辅月度作业反馈正文，不进行对话解释。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.55,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{config.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
