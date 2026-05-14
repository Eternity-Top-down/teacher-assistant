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
) -> str:
    subject_name = subject or "数学"
    display_name = student_display_name(student_name)
    emojis = pick_title_emojis()
    raw_title = lesson_title or f"{display_name}第{lesson_number}次{subject_name}课"
    title = title_with_date(raw_title, lesson_date)
    performance = performance_summary or "老师本次未填写具体课堂表现，建议后续结合课堂观察继续补充。"
    advice = advice_summary or "老师本次未填写具体课后建议。"
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
6. 反馈标题和正文称呼学生时只使用“{display_name}”，不要猜测或补全学生完整姓名。
7. 作业安排必须严格根据老师输入润色；如果老师未输入作业安排，不得自行安排作业。
8. 老师输入可能是一句话、流水账或无序文本；生成前请先提取事实并分点归纳，再组织反馈正文。
9. 归纳时必须遵守四大板块边界：课堂学习内容写本节课学了什么知识、课堂上完成了什么作业/练习/试卷/检测；课堂表现与知识掌握情况写听课状态、是否认真耐心和专注、哪些知识或题型做得不错、哪些知识或题型做得不好且需要注意；课后建议只写老师明确提出的建议、提醒、改进方向或习惯要求，不根据薄弱点自行生成建议；作业安排只按老师明确布置的真实任务润色，不新增作业，也不要把建议改写成作业。

内置优秀表达原则（只学习表达方式）：
1. 先具体肯定学生做得好的地方，再温和指出需要关注的问题。
2. 如果老师提供了课后建议，润色后仍要具体可执行，例如“复盘错题原因”“整理解题步骤”“复述本节方法”；如果老师没有提供，不要自行补建议。
3. 用家长容易看懂的表达，不堆砌教学术语。

旧反馈格式样例（只学格式，不学内容）：
{examples}

老师个人风格样例（学习格式、语气和表达习惯，不学事实）：
{style_text or "老师暂未提供个人风格样例，本次必须按标准四段结构生成。"}

本次课堂输入：
反馈使用称呼：{display_name}
课程科目：{subject_name}
课程标题：{title}

课程内容简述：
{lesson_summary}

课堂表现简述：
{performance_summary or "老师未额外填写，请只根据课程内容做客观、保守表述。"}

课后建议要点：
{advice_summary or "老师未填写具体课后建议；不要根据课堂表现自行生成建议。"}

作业安排：
{homework_plan or "老师未填写具体作业安排。"}
""".strip()

    if has_style_examples:
        prompt = f"""
{shared_rules}

生成模式：个人风格。
要求：
1. 优先学习老师个人风格样例中的标题格式、段落结构、板块顺序、排版习惯、语气、详略和常用表达。
2. 如果样例呈现稳定的四段标题结构，必须沿用这套四段结构；不得因为启用个人风格而省略标题、合并板块或改成自由段落。
3. 如果样例呈现非四段结构，可以跟随样例的自然格式，但仍要清楚覆盖课程内容、课堂表现、课后建议和作业安排四类信息。
4. 不要机械照抄样例中的事实、原句或学生经历，只学习格式和表达方式。
5. 必须覆盖本次课堂输入里的课程内容、课堂表现、课后建议和作业安排；如果某项没有输入，只能做保守说明。
6. 如果老师填写了作业安排，必须体现；如果没有填写，不要编造作业。
""".strip()
    else:
        prompt = f"""
{shared_rules}

生成模式：结构化反馈。
额外规则：
1. 标题前必须使用指定 emoji，每个标题前有且只有 1 个 emoji；正文不要额外大量添加 emoji。
2. 作业安排如果未填写，第 4 段写“本次老师未填写具体作业安排。”

必须使用以下固定结构：
{title}

{emojis["lesson"]} 1. 课堂学习内容：

总结本节课学习的知识点，尽量条目化，方便学生复习和回顾。

{emojis["performance"]} 2. 课堂表现与知识掌握情况：

总结学生课堂状态、掌握较好的地方、掌握不好且需要关注的地方。没有输入的表现不要编造。

{emojis["advice"]} 3. 课后建议：

严格根据老师输入的课后建议进行润色，不要从课堂表现或薄弱点自行新增建议。

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


ORGANIZE_FIELD_LABELS = {
    "lesson_summary": "课堂学习内容",
    "performance_summary": "课堂表现与知识掌握情况",
    "advice_summary": "课后建议",
    "homework_plan": "作业安排",
}


def _missing_feedback_fields(payload: dict) -> list[str]:
    return [field for field in ORGANIZE_FIELD_LABELS if not str(payload.get(field, "")).strip()]


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
            raise ValueError("AI 返回内容不是 JSON")
        return json.loads(cleaned[start : end + 1])


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


async def organize_lesson_note(
    student_name: str,
    subject: str,
    lesson_title: str,
    raw_lesson_note: str,
    lesson_summary: str,
    performance_summary: str,
    advice_summary: str,
    homework_plan: str,
    ai_config: AIConfig,
) -> dict:
    subject_name = subject or "数学"
    display_name = student_display_name(student_name)
    prompt = f"""
你是一名一对一辅导老师的课堂记录整理助手。你的任务是把老师随手写的本节课原始记录，整理成后续生成家长反馈必须使用的四大板块。

重要规则：
1. 只整理老师已经提供的信息，不要编造课堂内容、学生表现、课后建议或作业安排。
2. “课后建议”只整理老师明确提出的建议、提醒、改进方向或习惯要求，例如复盘错题、注意审题、巩固概念、加强计算、保持节奏等；不要根据课堂问题、薄弱点或错误表现自行生成建议。
3. “作业安排”必须来自老师明确布置的作业、复习、订正、预习、需带资料或“无作业/本次无额外作业”等任务；不要自行安排作业，也不要把建议改写成作业。
4. 如果某个板块没有老师提供的信息，返回空字符串，并把字段名放入 missing_fields。
5. 如果老师已经在结构化字段里写了内容，要优先保留并可轻微整理；原始记录只用于补充缺失或更清楚地归类。
6. 所有有效信息都必须尽量归入四大板块；确实无法归入四大板块的信息直接忽略，不要另设补充栏。
7. 分类边界必须按以下定义执行：
   - 课堂学习内容：本节课学了什么知识，课堂上完成了什么作业、练习、试卷或检测。
   - 课堂表现与知识掌握情况：听课状态、是否认真耐心/专注，哪些知识或题型做得不错，哪些知识或题型做得不好、需要注意。
   - 课后建议：老师明确提出的方向、方法、提醒、习惯要求，不一定有具体交付物；例如“继续巩固计算方法”“注意审题”“计算不要跳步”“保持主动提问”。
   - 作业安排：老师明确布置给学生要完成的具体任务，通常学生要完成、复习、预习、订正或带资料；例如“完成讲义 3-5 题”“订正错题”“复习本节课内容”“预习分式”“下节课带试卷”。没有明确作业就返回空字符串并标记缺失。
8. “复习/巩固”只有在老师表达为明确任务时才进入作业安排；如果只是提醒或方向，进入课后建议。例如“继续巩固计算方法”是课后建议；“作业：复习计算方法并完成讲义 3-5 题”是作业安排。
9. 只输出 JSON，不要 Markdown，不要解释。

去敏分类参考（只学习分类边界和表达粒度，不复用学生事实）：
原始记录：本节课主要复习不等式和因式分解两个单元，课堂上做了归纳复习和检测。学生A听课认真，做题更专注，也会主动思考和提问；不等式和因式分解的计算速度有进步，但一次函数图像理解还不熟，因式分解公式法掌握不够熟，不等式乘除负数变号容易忘。建议课后巩固不等式和因式分解基础题，加强一次函数图像复习，熟悉平方差公式和完全平方公式的应用，计算时一步步写清楚。作业是复习本节课不等式和因式分解内容，预习学校正在学的分式，下节课带半期试卷。
对应整理：
lesson_summary：复习不等式和因式分解两个单元，完成归纳复习和检测，涉及不等式定义、运算、不等式组解集与数轴、一次函数图像与不等式关系、因式分解定义、提公因式法、平方差公式和完全平方公式等内容。
performance_summary：学生A听课认真，做题专注，能更主动思考和提问；不等式和因式分解计算速度与理解有进步；一次函数图像理解不够熟，因式分解公式法记忆和应用不够熟，不等式乘除负数变号容易出错。
advice_summary：课后巩固不等式和因式分解的基础题型，加强一次函数图像复习，熟悉提公因式法、平方差公式和完全平方公式的应用；计算时放慢节奏、写清步骤，减少跳步。
homework_plan：复习本节课不等式和因式分解内容；预习学校正在学的分式；下节课带半期试卷。

学生称呼：{display_name or "该学生"}
科目：{subject_name}
课程标题：{lesson_title or "未填写"}

老师原始记录：
{raw_lesson_note or "老师未填写原始记录"}

已有结构化字段：
课堂学习内容：{lesson_summary or "未填写"}
课堂表现与知识掌握情况：{performance_summary or "未填写"}
课后建议：{advice_summary or "未填写"}
作业安排：{homework_plan or "未填写"}

请按以下 JSON 结构输出：
{{
  "lesson_summary": "课堂学习内容",
  "performance_summary": "课堂表现与知识掌握情况",
  "advice_summary": "课后建议，只能来自老师明确提出的建议、提醒、改进方向或习惯要求",
  "homework_plan": "作业安排，必须来自老师明确输入；没有作业则写老师明确输入的无作业说明",
  "missing_fields": ["lesson_summary", "performance_summary", "advice_summary", "homework_plan"]
}}
""".strip()

    payload = {
        "model": ai_config.model,
        "messages": [
            {"role": "system", "content": "你只输出严格 JSON，用于老师整理一对一课后反馈素材。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=30) as client:
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
        "lesson_summary": str(parsed.get("lesson_summary", "")).strip(),
        "performance_summary": str(parsed.get("performance_summary", "")).strip(),
        "advice_summary": str(parsed.get("advice_summary", "")).strip(),
        "homework_plan": str(parsed.get("homework_plan", "")).strip(),
    }
    missing = [field for field in _string_list(parsed.get("missing_fields")) if field in ORGANIZE_FIELD_LABELS]
    result["missing_fields"] = sorted(set(missing + _missing_feedback_fields(result)), key=list(ORGANIZE_FIELD_LABELS).index)
    return result


def fallback_evening_feedback(
    student_name: str,
    period_type: str,
    period_label: str,
    homework_summary: str,
) -> str:
    period_word = {"day": "当天", "week": "本周", "month": "本月"}.get(period_type, "本次")
    next_word = {"day": "后续晚辅", "week": "下周晚辅", "month": "下个月晚辅"}.get(period_type, "后续晚辅")
    return f"""{student_name}{period_label}晚辅作业完成情况反馈：

{period_word}晚辅中，{student_name}的作业完成情况主要表现为：{homework_summary}

从整体情况来看，孩子的晚辅作业状态可以结合以上情况继续跟进。后续完成作业时，建议继续关注订正质量、计算细节和独立思考过程，遇到不会的题目及时标记并提问，避免问题积累。

{next_word}会继续关注{student_name}的作业完成质量和错题订正情况，帮助孩子逐步养成更稳定的数学作业习惯。"""


async def generate_evening_feedback(
    student_name: str,
    grade: str,
    school: str,
    period_type: str,
    period_label: str,
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
        return fallback_evening_feedback(student_name, period_type, period_label, homework_summary)

    student_info = "，".join(part for part in [student_name, grade, school] if part)
    period_rule = {
        "day": "按天反馈：强调当天晚辅作业完成情况，语言更短、更具体，适合当天发给家长。",
        "week": "按周反馈：总结本周晚辅作业完成情况，覆盖一周内完成度、订正、稳定问题和下周提醒。",
        "month": "按月反馈：总结本月晚辅作业完成情况，覆盖整体完成度、作业质量、订正情况、常见问题和下月提醒。",
    }.get(period_type, "按本次反馈时间段总结晚辅作业完成情况。")
    period_name = {"day": "当天", "week": "本周", "month": "本月"}.get(period_type, "本次")
    prompt = f"""
你是一名晚辅老师，需要根据老师输入的“该学生晚辅作业完成情况简述”，直接写一份可以发给家长的晚辅反馈正文。

要求：
1. 只输出反馈正文，不要出现“好的”“以下是”“根据您的描述”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 只根据本次输入生成，不要编造没有提供的具体事实。
4. 语气自然、具体、克制，适合发给家长。
5. 内容重点围绕：作业完成情况、作业质量/订正情况、存在问题、后续提醒。
6. 不强制固定标题格式，但正文要完整、清楚、方便老师修改。
7. {period_rule}

学生信息：{student_info or student_name}
反馈时间：{period_label}
反馈口径：{period_name}晚辅
作业完成情况简述：
{homework_summary}
""".strip()

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你只输出晚辅作业反馈正文，不进行对话解释。"},
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


async def generate_evening_monthly_feedback(
    student_name: str,
    grade: str,
    school: str,
    feedback_month: str,
    homework_summary: str,
    ai_config: AIConfig | None = None,
) -> str:
    return await generate_evening_feedback(
        student_name=student_name,
        grade=grade,
        school=school,
        period_type="month",
        period_label=feedback_month,
        homework_summary=homework_summary,
        ai_config=ai_config,
    )
