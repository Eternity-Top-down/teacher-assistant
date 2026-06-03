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
    performance = performance_summary or "本节课暂无额外课堂表现记录。"
    advice = advice_summary or "本节课暂无额外课后建议。"
    homework = homework_plan or "本节课暂无额外作业安排。"
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
    format_examples_text = (
        "已启用老师个人风格样例，本次不注入默认格式样例，避免干扰老师个人风格；仍必须遵守一对一四段结构。"
        if has_style_examples
        else examples
    )
    emojis = pick_title_emojis()
    shared_rules = f"""
你是一名一对一辅导老师的反馈表达助手。你的任务不是替老师补内容，而是把老师已经填写的四大板块信息，润色成可以直接发给家长的课后反馈正文。

核心目标：
- 事实不新增，表达更自然、更亲和、更具体，像一位真实老师认真写给家长的反馈。
- 老师输入少，反馈就短一些；不要为了完整、好看或显得专业而硬凑内容。
- 反馈必须保留一对一课后反馈的四段结构，方便老师保存和复盘。

硬边界：
1. 只输出反馈正文，不要出现“好的”“以下是”“根据您的课堂记录”等聊天式开头。
2. 不要输出 Markdown 分隔线。
3. 具体知识点、课堂行为、掌握情况、问题、建议和作业只能来自“本次课堂输入”；用户没说的，不写。
4. 用户说得不确定的，不写成确定；主观评价可以润色为温和表达，但不能包装成新的客观事实。
5. 不推断性格、动机、家庭原因、能力水平、长期趋势或学习品质。
6. 不新增原因判断、影响判断、训练计划、家长任务、额外练习或作业。
7. 不使用“潜力巨大”“学习态度端正”“核心素养”“自我管理能力”“系统复盘”“奠定基础”“未来可期”等 AI 味套话。
8. 反馈标题和正文称呼学生时只使用“{display_name}”，不要猜测或补全学生完整姓名。
9. 作业安排必须严格根据老师输入润色；如果老师未输入作业安排，不得自行安排作业。
10. 老师个人风格样例只用于学习语气、段落节奏、标题/排版习惯，禁止迁移样例中的课程内容、学生表现、问题、建议方向、作业内容或原句。
11. 如果老师填写“本次无额外建议”或“本次无额外作业”，这代表老师已确认无额外安排；请自然表达为“本节课暂无额外……”这类家长可读的话，不要写成“老师未填写”。

四大板块边界：
- 课堂学习内容：只写本节课学了什么、练了什么、完成了什么课堂任务。
- 课堂表现与知识掌握情况：只写老师输入中出现的听课状态、参与情况、练习表现、掌握较好或需要关注的地方。
- 课后建议：只润色老师明确提出的建议、提醒、改进方向或习惯要求；不要根据薄弱点自行推导建议。
- 作业安排：只润色老师明确布置的作业、复习、订正、预习或携带资料；没有作业就按缺失说明处理。

表达原则：
1. 把口语化、零散的信息组织得顺畅一些，但不改变事实含义。
2. 负面评价尽量转成可观察、温和的课堂描述，例如“上课不认真”可表达为“课堂过程中需要提醒后回到当前任务”。
3. “做题慢”可表达为“练习完成节奏相对慢一些”；“不敢说”可表达为“表达时比较谨慎，开口参与还不够稳定”。
4. “有进步”必须贴着老师输入的具体变化写，不泛化成长期成长判断。
5. 语言要像老师真实发给家长的反馈：亲和、克制、具体，不写公文腔和鸡汤。

旧反馈格式样例（只学格式，不学内容）：
{format_examples_text}

老师个人风格样例（学习格式、语气和表达习惯，不学事实）：
{style_text or "老师暂未提供个人风格样例，本次必须按标准四段结构生成。"}

本次课堂输入：
反馈使用称呼：{display_name}
课程科目：{subject_name}
课程标题：{title}

课程内容简述：
{lesson_summary}

课堂表现简述：
{performance_summary or "本节课暂无额外课堂表现记录。"}

课后建议要点：
{advice_summary or "本节课暂无额外课后建议；不要根据课堂表现自行生成建议。"}

作业安排：
{homework_plan or "本节课暂无额外作业安排。"}
""".strip()

    if has_style_examples:
        prompt = f"""
{shared_rules}

生成模式：个人风格。
要求：
1. 优先学习老师个人风格样例中的标题格式、段落结构、板块顺序、排版习惯、语气、详略和常用表达。
2. 无论老师个人风格样例是什么结构，本次输出都必须保留四个独立板块：课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排。
3. 可以学习样例的语气、标题写法、句子节奏和详略，但不得省略板块、合并板块，尤其不得把“课后建议”和“作业安排”合并为一段。
4. 不要机械照抄样例中的事实、原句、建议方向或学生经历，只学习格式和表达方式。
5. 必须覆盖本次课堂输入里已经提供的课程内容、课堂表现、课后建议和作业安排；缺失项只做克制说明。
6. 如果老师填写了作业安排，必须体现；如果没有填写，不要编造作业。
7. 样例里常见的表扬、建议或问题不能迁移到本次学生。
""".strip()
    else:
        prompt = f"""
{shared_rules}

生成模式：结构化反馈。
额外规则：
1. 标题前必须使用指定 emoji，每个标题前有且只有 1 个 emoji；正文不要额外大量添加 emoji。
2. 作业安排如果未填写或老师确认无额外作业，第 4 段自然表达为“本节课暂无额外作业安排。”
3. 课后建议如果未填写或老师确认无额外建议，第 3 段自然表达为“本节课暂无额外课后建议。”

必须使用以下固定结构：
{title}

{emojis["lesson"]} 1. 课堂学习内容：

把老师填写的课堂学习内容润色为家长容易看懂的表达；不要新增知识点或课堂任务。

{emojis["performance"]} 2. 课堂表现与知识掌握情况：

把老师填写的课堂表现和知识掌握情况润色为具体、温和的教师描述；没有输入的表现不要编造。

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
        "temperature": 0.35,
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


def _fallback_organize_lesson_note(
    raw_lesson_note: str,
    lesson_summary: str,
    performance_summary: str,
    advice_summary: str,
    homework_plan: str,
) -> dict:
    result = {
        "lesson_summary": lesson_summary.strip(),
        "performance_summary": performance_summary.strip(),
        "advice_summary": advice_summary.strip(),
        "homework_plan": homework_plan.strip(),
    }
    raw = raw_lesson_note.strip()
    if raw:
        markers = [
            ("advice_summary", re.compile(r"(?:课后建议|建议)\s*[:：]")),
            ("homework_plan", re.compile(r"(?:作业安排|作业)\s*[:：]")),
        ]
        matches = []
        for field, pattern in markers:
            match = pattern.search(raw)
            if match:
                matches.append((match.start(), match.end(), field))
        matches.sort(key=lambda item: item[0])

        if matches:
            first_start = matches[0][0]
            before_markers = raw[:first_start].strip(" \n\r\t；;。")
            if before_markers and not result["lesson_summary"]:
                result["lesson_summary"] = before_markers
            for index, (_, content_start, field) in enumerate(matches):
                next_start = matches[index + 1][0] if index + 1 < len(matches) else len(raw)
                content = raw[content_start:next_start].strip(" \n\r\t；;。")
                if content and not result[field]:
                    result[field] = content
        elif not result["lesson_summary"]:
            result["lesson_summary"] = raw

    result["missing_fields"] = _missing_feedback_fields(result)
    return result


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
你是一名一对一课堂记录分类助手。这个功能服务于喜欢一次性输入全部课堂内容的老师：你只负责把老师输入的信息分类到四大板块，让老师清楚看到哪些信息已经覆盖、哪些还需要补充。

任务定位：
- 这是“分类和缺失提示”，不是生成家长反馈。
- 可以轻微顺句、去掉重复，但不要把内容改写成完整反馈文案。
- 只处理老师已经写出的信息，不做推断、不补事实、不补建议、不补作业。

重要规则：
1. 只整理老师已经提供的信息，不要编造课堂内容、学生表现、课后建议或作业安排。
2. 用户没说的，不写；用户说得不确定的，不写成确定。
3. 不推断性格、动机、家庭原因、能力水平、长期趋势或学习品质。
4. “课后建议”只整理老师明确提出的建议、提醒、改进方向或习惯要求；不要根据课堂问题、薄弱点或错误表现自行生成建议。
5. “作业安排”必须来自老师明确布置的作业、复习、订正、预习、需带资料或“无作业/本次无额外作业”等任务；不要自行安排作业，也不要把建议改写成作业。
6. 如果某个板块没有老师提供的信息，返回空字符串，并把字段名放入 missing_fields，目的是提醒用户补充。
7. 如果老师已经在结构化字段里写了内容，要优先保留并可轻微整理；原始记录只用于补充缺失或更清楚地归类。
8. 所有有效信息都必须尽量归入四大板块；确实无法归入四大板块的信息直接忽略，不要另设补充栏。
9. 分类边界必须按以下定义执行：
   - 课堂学习内容：本节课学了什么知识，课堂上完成了什么作业、练习、试卷或检测。
   - 课堂表现与知识掌握情况：听课状态、参与情况、练习表现，哪些知识或题型做得不错，哪些知识或题型做得不好、需要注意。
   - 课后建议：老师明确提出的方向、方法、提醒、习惯要求，不一定有具体交付物；例如“继续巩固计算方法”“注意审题”“计算不要跳步”“保持主动提问”。
   - 作业安排：老师明确布置给学生要完成的具体任务，通常学生要完成、复习、预习、订正或带资料；例如“完成讲义 3-5 题”“订正错题”“复习本节课内容”“预习分式”“下节课带试卷”。没有明确作业就返回空字符串并标记缺失。
10. “复习/巩固”只有在老师表达为明确任务时才进入作业安排；如果只是提醒或方向，进入课后建议。例如“继续巩固计算方法”是课后建议；“作业：复习计算方法并完成讲义 3-5 题”是作业安排。
11. 只输出 JSON，不要 Markdown，不要解释。

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
  "lesson_summary": "课堂学习内容，只做分类整理，不生成反馈文案",
  "performance_summary": "课堂表现与知识掌握情况，只整理老师已写出的表现和掌握情况",
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

    try:
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
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return _fallback_organize_lesson_note(
            raw_lesson_note,
            lesson_summary,
            performance_summary,
            advice_summary,
            homework_plan,
        )
    if not isinstance(parsed, dict):
        return _fallback_organize_lesson_note(
            raw_lesson_note,
            lesson_summary,
            performance_summary,
            advice_summary,
            homework_plan,
        )
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
    natural_period = natural_evening_period_label(period_type, period_label)
    subject_text = f"{subject.strip()}晚辅" if subject.strip() else "晚辅"
    return f"""{natural_period}{display_name}{subject_text}情况反馈：

{period_word}晚辅中，{display_name}的{subject_text}情况主要是：{homework_summary}

后续会根据以上情况继续关注{display_name}的{subject_text}状态和完成质量。"""


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
    period_name = {"day": "当天", "week": "本周", "month": "本月"}.get(period_type, "本次")
    style_text = "\n\n".join(
        f"晚辅样例{index}：\n{example.get('content', '').strip()}"
        for index, example in enumerate(style_examples or [], start=1)
        if example.get("content", "").strip()
    )
    if style_text:
        style_rule = """
老师已启用晚辅反馈风格样例：
- 只学习样例的表达格式和老师风格：开场、称呼、语气、句子节奏、详略和常用表达。
- 不学习样例里的学生事实、具体问题、评价倾向和具体建议内容。
- 样例中的建议方向不能迁移到本次学生；例如样例常写“先完成基础题”，也不能给没有相关事实的学生套这句话。
- 如果样例有稳定开场，可以沿用开场形式，但必须替换成本次学生、时间和学科。
- 样例是月反馈而本次是周反馈或日反馈时，时间必须改成“本周”或“今天”。
""".strip()
        length_rule = "输出长短和段落节奏可以贴近样例；本次输入事实少时必须更短，不要为了像样例一样完整而补内容。"
    else:
        style_rule = """
老师未启用晚辅反馈风格样例：
- 使用短、直接、克制的家长沟通语气。
- 不写报告式标题，不分条，不强行分段。
- 句子可以接近老师原话，只做顺句和轻微润色。
""".strip()
        length_rule = "输出长度通常 1 个自然段；信息较多时最多 2 个自然段；不要扩写成完整学习报告。"
    prompt = f"""
你是一名晚辅老师的反馈表达助手。请把老师输入的“晚辅情况简述”润色成一段可以直接发给家长的晚辅反馈。

目标：短、准、真实，像老师平时给家长发的消息；不是学习报告、四段总结或模板作文。

写作流程：
1. 先识别老师已经写出的事实。
   - 包括作业完成情况、晚辅状态、纪律情况、做得好的地方、需要关注的地方、老师明确提出的建议。
   - 只使用这些事实做语言优化，不新增课堂外信息。
2. 再组织成自然消息。
   - 作业完成情况是主线。
   - 老师写到哪个维度就写哪个维度；没有写到纪律、优点或问题时，不要为了完整而补。
   - 输入很少时，输出就简短，不硬凑成完整反馈。
3. 最后处理建议。
   - 老师输入里有明确建议时，以老师建议为主，只做润色。
   - 老师没写建议时，可以补一句很轻的方向性提醒，但必须贴近已有事实，例如继续关注完成节奏、书写、订正、效率或晚辅状态。
   - 这句提醒不能变成具体训练安排、家长任务、额外作业或原因判断。

硬边界：
- 只输出反馈正文，不要说“好的”“以下是”“根据描述”等。
- 正文称呼学生时只用“{display_name}”，不要使用登记全名“{student_name}”。
- 时间必须使用“{natural_period}”；不要写“{period_label}”，也不要写机器日期、周数或年份。
- 学科已填写为“{subject_name or "未填写"}”；如果学科未填写，不要自己补“数学”或其他学科。
- 不新增完成度、纪律、错因、具体题型、题量、正确率、老师讲解后的反应、能力判断、家长任务或额外练习。
- 不推断性格、动机、家庭原因、能力水平、长期趋势或学习品质。
- 不写“学习计划”“家长监督”“系统复盘”“核心素养”“自我管理能力”“长期培养”“潜力巨大”等 AI 味表达。
- 批量生成时，每个学生的事实要分别处理，不要把其他学生的问题或优点串到本条里。
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
                    "你只输出可以直接发给家长的晚辅反馈正文，不进行对话解释。"
                    "反馈要短、准、真实，只围绕老师输入中有依据的作业完成情况、晚辅状态、表扬点、问题和建议做表达优化。"
                    "如果有老师风格样例，只学习写法，不复用样例事实。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
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
