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
COMPOUND_SURNAMES = (
    "欧阳",
    "司马",
    "上官",
    "诸葛",
    "东方",
    "独孤",
    "南宫",
    "万俟",
    "闻人",
    "夏侯",
    "尉迟",
    "公羊",
    "赫连",
    "澹台",
    "皇甫",
    "宗政",
    "濮阳",
    "公冶",
    "太叔",
    "申屠",
    "公孙",
    "慕容",
    "仲孙",
    "钟离",
    "长孙",
    "宇文",
    "司徒",
    "鲜于",
    "司空",
    "闾丘",
    "子车",
    "亓官",
    "司寇",
    "巫马",
    "公西",
    "颛孙",
    "壤驷",
    "公良",
    "漆雕",
    "乐正",
    "宰父",
    "谷梁",
    "拓跋",
    "夹谷",
    "轩辕",
    "令狐",
    "段干",
    "百里",
    "呼延",
    "东郭",
    "南门",
    "羊舌",
    "微生",
    "公户",
    "公玉",
    "公仪",
    "梁丘",
    "公仲",
    "公上",
    "公门",
    "公山",
    "公坚",
    "左丘",
    "公伯",
    "西门",
    "公祖",
    "第五",
    "公乘",
    "贯丘",
    "公皙",
    "南荣",
    "东里",
    "东宫",
    "仲长",
    "子书",
    "子桑",
    "即墨",
    "达奚",
    "褚师",
)


def pick_title_emojis() -> dict[str, str]:
    return {key: random.choice(values) for key, values in TITLE_EMOJIS.items()}


def student_display_name(full_name: str) -> str:
    name = full_name.strip()
    if not name:
        return name
    if all("\u4e00" <= char <= "\u9fff" for char in name):
        if len(name) <= 2:
            return name
        compound_surname = next((surname for surname in COMPOUND_SURNAMES if name.startswith(surname)), "")
        if compound_surname:
            given_name = name[len(compound_surname) :]
            return given_name if len(given_name) >= 2 else name
        return name[1:]
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
    subject: str,
    homework_summary: str,
) -> str:
    display_name = student_display_name(student_name)
    period_word = {"day": "当天", "week": "本周", "month": "本月"}.get(period_type, "本次")
    next_word = {"day": "后续晚辅", "week": "下周晚辅", "month": "下个月晚辅"}.get(period_type, "后续晚辅")
    natural_period = natural_evening_period_label(period_type, period_label)
    subject_text = f"{subject.strip()}作业" if subject.strip() else "作业"
    habit_text = f"{subject.strip()}作业习惯" if subject.strip() else "作业习惯"
    return f"""{natural_period}{display_name}{subject_text}完成情况反馈：

{period_word}晚辅中，{display_name}的{subject_text}完成情况主要表现为：{homework_summary}

从整体情况来看，孩子的晚辅作业状态可以结合以上情况继续跟进。后续完成作业时，建议继续关注订正质量、计算细节和独立思考过程，遇到不会的题目及时标记并提问，避免问题积累。

{next_word}会继续关注{display_name}的{subject_text}完成质量和错题订正情况，帮助孩子逐步养成更稳定的{habit_text}。"""


def natural_evening_period_label(period_type: str, period_label: str) -> str:
    natural_labels = {"day": "今天", "week": "本周", "month": "本月"}
    return natural_labels.get(period_type, (period_label or "").strip() or "本次")


async def generate_evening_feedback(
    student_name: str,
    grade: str,
    school: str,
    period_type: str,
    period_label: str,
    subject: str,
    homework_summary: str,
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
        return fallback_evening_feedback(student_name, period_type, period_label, subject, homework_summary)

    display_name = student_display_name(student_name)
    student_info = "，".join(part for part in [student_name, grade, school] if part)
    subject_name = subject.strip()
    natural_period = natural_evening_period_label(period_type, period_label)
    feedback_topic = f"{natural_period}{display_name}的{subject_name}晚辅情况" if subject_name else f"{natural_period}{display_name}的晚辅情况"
    period_rule = {
        "day": "按天反馈：强调当天晚辅中的真实状态，语言更短、更具体，适合当天发给家长。",
        "week": "按周反馈：总结本周晚辅中的稳定表现、作业完成、知识掌握和后续提醒。",
        "month": "按月反馈：总结本月晚辅中的阶段表现、作业习惯、知识薄弱点和后续学习建议。",
    }.get(period_type, "按本次反馈时间段总结晚辅中的真实情况。")
    period_name = {"day": "当天", "week": "本周", "month": "本月"}.get(period_type, "本次")
    style_text = "\n\n".join(
        f"晚辅样例{index}：\n{example.get('content', '').strip()}"
        for index, example in enumerate(style_examples or [], start=1)
        if example.get("content", "").strip()
    )
    if style_text:
        style_rule = """
8. 本次已启用老师的晚辅反馈风格样例。请把个人风格当作本次输出的优先表达层：先学习样例里稳定、清晰、反复出现的开场、结构、表达顺序和语气，再用本次学生事实填充内容；默认晚辅四个基础方向只做质量兜底，不要把输出改回通用模板。
9. 生成正文前，先在内部提炼样例的“风格画像”：开场方式、是否聊天式表达、是否固定称呼接收人、段落结构、评价维度、表达顺序、肯定与提醒比例、建议具体程度、结尾方式、句子密度和语气。
10. 即使只启用 1 条样例，只要样例内容完整、结构清楚、表达有明显个人习惯，也必须坚定学习这条样例的开场、结构和语气；不要因为样例数量少就退回通用写法。
11. 如果样例呈现“谢姐，反馈一下这个月/本周/今天某某数学作业的完成情况”这类开场，必须沿用这种开场形式；其中学生姓名、时间口径、学科和作业情况要替换为本次信息。
12. 对接收人称呼的处理：如果启用的样例里有清晰的固定称呼，可以把它视为该老师的沟通风格并保留；如果多条样例中的称呼不一致，或本次情况简述明确提供了新的接收人称呼，则优先使用本次称呼或省略称呼，不要随意编造新称呼。
13. 如果样例中存在清晰、可迁移的高质量风格特征，请强学习这些特征，让输出明显像老师本人；只有在样例明显很短、空泛、随意或无法形成有效风格画像时，才退回默认晚辅反馈结构并轻微学习语气和措辞。
14. 批量生成时，每个学生都必须按同一套“风格优先 + 默认结构保底”的逻辑改写本条事实，不能有的学生套样例、有的学生自由发挥。
15. 只学习样例的结构、观察维度、表达节奏、语气和措辞习惯，禁止复用样例里的学生事实、原句、题目、具体表现、作业内容或问题细节。
16. 样例只决定表达方式，不决定本次评价倾向；不要因为样例整体积极就把本次学生写得偏好，也不要因为样例问题较多就放大本次问题。
17. 如果样例是月反馈，但本次是日反馈或周反馈，保留样例开场和结构，但时间口径必须改成“今天”或“本周”，不要照抄“本月”“这个月”“月反馈”。
18. 允许基于输入做概括性延伸，例如由“计算错得多”延伸为“计算准确率和订正质量需要关注”；禁止新增可验证细节，例如具体题型、正确率、家长任务、主动提问、老师点拨后的反应等，除非本次输入中有依据。
19. 贴近样例风格时仍必须遵守事实边界：没有输入依据的内容不要补，不要为了凑齐样例里的某一项而编造；样例中有但本次输入没有依据的观察维度，可以自然略过或用更概括的同风格表达轻轻带过。
""".strip()
        length_rule = "输出长短：优先贴近样例中稳定且高质量的篇幅和密度；输入信息很少时可以略短，但不要因为默认结构保底而改成生硬的通用短反馈。"
    else:
        style_rule = """
8. 老师暂未提供晚辅反馈风格样例，本次按自然、清楚、克制的晚辅反馈写法生成。
9. 不强制固定标题格式，也不要强行套四段标题；可按输入信息自然分段，正文要清楚、方便老师修改。
""".strip()
        length_rule = """输出长度建议：
- 按天反馈：1-2 个自然段，短而具体。
- 按周反馈：2-3 个自然段，概括一周完成度、质量、问题和提醒。
- 按月反馈：2-4 个自然段，概括阶段表现，但仍只写输入中有依据的事实。"""
    prompt = f"""
你是一名晚辅老师，需要根据老师输入的“该学生晚辅情况简述”，直接写一份可以发给家长的晚辅反馈正文。

生成前请先在心里完成事实判断，但不要把判断过程输出：
- 学生表现：晚辅时的专注度、效率、主动性、独立性、是否需要提醒、是否愿意提问。
- 作业完成情况：完成量、完成速度、是否拖拉、订正情况、书写、步骤、正确率和完成质量。
- 知识点掌握情况：哪些知识点或题型比较稳定，哪些地方容易错、理解不到位、方法不熟或需要复盘。
- 学习建议：基于本次输入中已经出现的表现、作业和知识掌握情况，给出后续订正、复盘、检查、效率或习惯方面的提醒。

同时请在心里判断本次输入的“可用事实密度”，不要根据字数、语气或老师是否认真来判断：
- 可用事实较少：只有笼统评价或少量核心事实时，例如“作业完成一般，计算错得多”，要用上述四个方向补足一份结构完整、真实、能发给家长的反馈；只能做概括性延伸，不要新增具体题型、正确率、主动提问、老师点拨后反应或家长任务。
- 可用事实中等：提供了主要表现、作业问题、知识薄弱点或学习提醒时，要保留这些主要事实，适度组织和展开，让反馈比简单复述更完整，但不要把没有依据的细节写实。
- 可用事实较多：提供了具体题型、订正情况、老师引导后的反应、迁移情况、问题原因或后续方向时，要优先保留这些真实细节，减少套话和泛化，不要压缩成通用模板。

写作要求：
1. 只输出可直接发给家长的反馈正文，不要出现“好的”“以下是”“根据您的描述”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 只根据本次输入生成；没有提供的事实不要补细节，不要为了显得完整而编造。
4. 最高优先级是像老师真实发给家长的话：自然、具体、克制，不像分析报告，不给家长制造焦虑。
5. 优先覆盖老师已经提供的信息；可以把零散表述整理得更顺，并围绕学生表现、作业完成情况、知识点掌握情况、学习建议四个方向自然展开。
6. 四个方向只用于内部组织，不是固定标题，也不是必填模板；正文不要显性写成“学生表现方面、作业完成方面、知识点掌握方面、学习建议方面”。
7. 可用事实少时不是简单写短，而是写得简洁、结构完整、表达概括、真实可用；不要为了结构完整而补出具体过程。可用事实多时不要稀释老师提供的具体信息，不要改写成泛泛而谈的套话。
8. 学习建议只能来自老师输入或由输入直接推出的通用提醒，例如“订正错题”“复盘出错原因”“提高完成效率”；不要新增具体作业任务、家长任务、题目数量或不存在的知识点，也不要给家长布置监督任务。
9. 正文称呼学生时只使用“{display_name}”，不要使用登记全名“{student_name}”，也不要补全或猜测其他姓名。
10. 如果学科已填写，反馈标题或开头可自然呈现为“{feedback_topic}”；如果学科未填写，不要自行猜测学科，也不要默认写“数学”。
11. 正文里的时间表达要符合家长沟通习惯：日反馈写“今天”，周反馈写“本周”，月反馈写“本月”；不要在正文标题里直接使用机器日期格式“{period_label}”，也不要写成“5月20日”“第20周”“2026年5月”这类存档式时间。
12. {period_rule}
{style_rule}

{length_rule}

老师晚辅反馈风格样例（只学写法，不学事实）：
{style_text or "无"}

学生登记信息：{student_info or student_name}
反馈使用称呼：{display_name}
内部存储时间：{period_label}
正文自然时间说法：{natural_period}
反馈口径：{period_name}晚辅
反馈主题：{feedback_topic}
学科：{subject_name or "未填写，请不要自行补学科"}
晚辅情况简述：
{homework_summary}
""".strip()

    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你只输出晚辅作业反馈正文，不进行对话解释。"
                    "如果用户提供老师晚辅反馈风格样例，优先学习样例中稳定、可迁移的开场、结构、语气、详略和表达习惯，"
                    "同时用默认晚辅结构和事实边界兜底。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35 if style_text else 0.55,
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
    subject: str = "",
    ai_config: AIConfig | None = None,
) -> str:
    return await generate_evening_feedback(
        student_name=student_name,
        grade=grade,
        school=school,
        period_type="month",
        period_label=feedback_month,
        subject=subject,
        homework_summary=homework_summary,
        ai_config=ai_config,
    )
