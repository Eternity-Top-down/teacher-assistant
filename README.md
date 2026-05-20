# 教师反馈助手

面向一对一辅导老师、晚辅老师和班课老师的本地优先反馈工作台。项目支持学生管理、课后反馈生成、晚辅反馈、班课班级管理、个人反馈风格样例和账号级模型配置，目标是把日常教学记录整理成可复用、可检索、可直接发给家长的反馈正文。

## 功能概览

- 账号体系：邮箱验证码注册/登录、JWT 鉴权、当前账号信息读取和退出登录。
- 一对一学生：创建、查看、编辑、删除学生，维护年级和科目。
- 一对一课后反馈：新增、生成、保存、查看、编辑、删除反馈，支持“原始记录整理”和“直接填四板块”双入口，反馈生成前仍需补齐课堂内容、课堂表现、课后建议、作业安排、AI 初稿和最终反馈。
- 反馈效率工具：反馈表单草稿自动保存、历史反馈按时间筛选、一对一和晚辅反馈可按学生姓名配合日期查询、最终反馈一键复制。
- AI 反馈生成：支持 OpenAI-compatible Chat Completions API；新增反馈默认先把老师的原始课堂记录整理成课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排四大板块，四项齐全后再生成反馈；没有启用个人风格样例时按标准四段结构生成，启用样例后按老师个人风格生成，也可在单次新增反馈中临时停用个人风格。
- 个人风格样例：一对一反馈样例和晚辅反馈样例分开维护，支持新增、查看详情、编辑、启用/停用、删除；生成时只学习对应模块的语气、结构和详略，样例库可多保存，参与生成时建议挑 1-3 条满意且愿意复用的反馈，最多 5 条，支持从已保存反馈一键设为样例。
- 晚辅模块：维护晚辅班级、批量录入晚辅学生；进入班级后默认先显示学生名单，点击“开始填写反馈”后可用表格按天、按周或按月批量填写学生情况、生成 AI 初稿并批量保存；每条反馈可填写本次学科，用于生成“某学生某科作业完成情况”口径；生成时优先依据老师输入的作业完成度、作业质量、晚辅状态、主要问题和后续提醒，不足的信息不硬凑，并可按时间段、反馈类型和学生姓名查询全部晚辅反馈。
- 班课模块：维护班课班级，当前支持创建、查看、编辑、删除班级和反馈查询占位入口。
- 本地数据：默认使用 SQLite，本地自动建表；API Key 加密存储，不在前端回显明文。

## 技术栈

- 前端：Vue 3 + Vite
- 后端：FastAPI + SQLite
- 网络请求：原生 `fetch`，通过 Vite 代理访问后端 `/api`
- 邮箱验证码：SMTP，默认按 QQ 邮箱配置
- AI 接入：OpenAI-compatible Chat Completions API，用于课堂记录整理和反馈生成

## 目录结构

```text
teacher-assistant/
  backend/
    app/                  FastAPI 应用、数据库、鉴权、AI 接入
    requirements.txt      后端依赖
    .env.example          后端环境变量示例
  frontend/
    src/                  Vue 单页应用源码
    src/assets/           页面插画和反馈操作图标
    package.json          前端脚本和依赖
    vite.config.js        本地开发代理配置
  files/                  开发截图和过程资料
  CHANGELOG.md            功能演进记录
  README.md
```

## 快速开始

### 1. 启动后端

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

后端默认地址：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173
```

本地开发时，Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`。

## 配置说明

复制 `backend/.env.example` 为 `backend/.env` 后按需调整：

```env
APP_SECRET=please-change-this-secret-in-development
DATABASE_PATH=teacher_assistant.db

SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=

AI_API_KEY=
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-pro
AI_DISPLAY_NAME=平台默认模型
AI_PROVIDER=deepseek
AI_TRIAL_QUOTA=30
ALLOW_GLOBAL_AI_FALLBACK=true

# 可选：显式配置 DeepSeek 平台默认模型，供新用户在试用额度内体验
DEEPSEEK_API_KEY=
AI_PLATFORM_MODELS=[{"id":"deepseek","name":"DeepSeek 平台默认","provider":"deepseek","base_url":"https://api.deepseek.com","model":"deepseek-v4-pro","api_key_env":"DEEPSEEK_API_KEY"}]
```

### 必改项

- `APP_SECRET`：用于 JWT 和 API Key 加密。正式使用前必须换成足够长的随机字符串。
- `DATABASE_PATH`：SQLite 数据库路径。默认会在后端目录下创建 `teacher_assistant.db`。

### 邮箱验证码

如果配置 QQ 邮箱 SMTP：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=你的QQ邮箱
SMTP_PASSWORD=你的QQ邮箱授权码
SMTP_FROM=你的QQ邮箱
```

`SMTP_PASSWORD` 是邮箱服务生成的 SMTP 授权码，不是 QQ 登录密码。  
如果暂时不配置邮箱，验证码会打印在后端终端里，方便本地开发测试。

### AI 模型配置

登录网页后进入「设置」页面选择可用模型：

- 平台默认模型：只提供 DeepSeek 平台默认模型，默认兼容 `AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 这一组旧配置；如果配置了 `AI_PLATFORM_MODELS`，系统也只会把 DeepSeek 作为平台默认模型展示给老师试用。前端会显示供应商和模型名，但不会显示 API Key。新账号默认可免费试用 `AI_TRIAL_QUOTA` 次。
- 我的模型配置：老师可以保存多套自己的 OpenAI-compatible API 配置，并选择其中一套作为当前使用模型；设置页默认先展示可用模型列表，点击新增或编辑后才展开配置表单。个人 API Key 会加密保存在 SQLite 数据库中，前端只显示是否已配置，不回显明文。
- 生成界面也可直接选择“本次使用模型”，不需要先回到设置页切换全局当前模型。
- 反馈生成模型用于整理一对一课堂记录、生成一对一课后反馈和晚辅反馈；课堂记录整理、一对一生成、单条晚辅生成、晚辅批量生成各扣 1 次平台试用额度，晚辅批量表格一次点击只扣 1 次。
- 个人反馈风格样例：用于让生成结果更贴近老师自己的表达习惯；设置页可通过“反馈样例类型”选择框切换管理一对一反馈样例和晚辅反馈样例，两类样例库互不影响。没有启用一对一样例时，一对一反馈默认按课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排四段结构输出；启用样例后会优先学习样例里的标题格式、段落结构、语气和详略，但仍必须覆盖四类课堂信息。晚辅样例只影响晚辅反馈，生成时优先学习样例中稳定、可迁移的开场、表达结构和语气，再以学生表现、作业完成情况、知识点掌握情况和学习建议作为质量底座；样例中稳定出现的聊天式称呼和开场可作为老师沟通风格保留，但不会复用样例中的学生事实。晚辅反馈仍只需要老师输入情况简述，会根据简述中的可用事实密度自动调整生成策略，并按日/周/月反馈口径使用“今天 / 本周 / 本月”这类正文时间说法。

平台默认模型试用额度用完后，系统会提示老师配置自己的 API。第一版不做管理员页面，单个用户加额度可直接维护数据库中的 `teacher_ai_usage.trial_quota_total`。

`AI_PLATFORM_MODELS` 必须是单行 JSON 数组。平台默认模型当前只保留 DeepSeek；如配置了其他 provider 的平台默认项，后端不会展示给老师试用。为了避免把 Key 写进 JSON，推荐使用 `api_key_env`、`model_env` 这类 `*_env` 字段，让系统从同一个 `.env` 文件读取真实值。

新增个人模型配置可保存老师自己的 API；DeepSeek 以外的模型请老师在“我的模型配置”里自行填写 API Key、Base URL 和模型名。

当前内置预设重点覆盖：

- DeepSeek：`https://api.deepseek.com`，默认 `deepseek-v4-pro`。
- 豆包 / 火山方舟：不作为平台默认模型；如需使用，请在“我的模型配置”中自行填写 API Key、Base URL 和模型名。
- 自定义兼容接口：用于其他 OpenAI-compatible 文本生成模型，需手动填写 Base URL、模型名和 API Key。

### 个人风格样例

样例标题只是这条样例保存在样例库里的管理名称，方便后续查找和管理，不会被 AI 当成反馈标题学习。AI 实际读取的是“反馈样例”正文内容。一对一反馈样例和晚辅反馈样例会分开保存、分开启用、分开传给模型；从历史反馈设为样例时会按反馈来源自动归入对应样例库。

新增样例时，如果不填写样例标题，系统会优先使用“反馈样例”正文里的第一行作为样例库管理名称。如果你粘贴的反馈标题不在正文第一行，建议手动填写样例标题，方便后续管理。

如果希望 AI 学习标题格式或固定段落结构，请把标题行和完整正文结构一起粘贴到“反馈样例”正文里，而不是只写在“样例标题”里。例如：

```text
某学生第3次数学课（4.26）

📖1.课堂学习内容：
……
```

样例库可以多保存，方便积累不同场景的好文案；真正参与生成时，建议只启用 1-3 条自己满意、改过后愿意复用、最接近本次想要效果的真实反馈。建议先把样例中的姓名匿名化为“学生A / 学生B”，避免在样例库和 prompt 中暴露真实学生信息。

新增课后反馈时，先输入本节课的原始记忆概述，AI 会先整理到课堂学习内容、课堂表现与知识掌握情况、课后建议和作业安排四大板块。整理完成后老师需要查看并修正四大板块，四项都补齐后才能生成反馈；课后建议必须来自老师明确提出的建议、提醒或改进方向，AI 不会根据薄弱点自行生成建议。作业安排必须来自实际布置，没有作业也要明确写“无”或“本次无额外作业”。

新增课后反馈时，「课堂记录整理」区域提供「填写参考」入口，可打开可拖动、可调整大小的参考示例浮窗。参考内容只帮助老师理解四个核心字段应该写什么。参考示例不会保存进反馈，也不是个人风格样例。

### 前端 API 地址

前端默认使用：

```text
/api
```

本地开发由 Vite 代理到后端。如果前后端分离部署，可以在构建或运行环境中设置：

```env
VITE_API_BASE=https://你的后端域名/api
```

## 常用命令

后端开发服务：

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

前端开发服务：

```bash
cd frontend
npm run dev
```

前端生产构建：

```bash
cd frontend
npm run build
```

前端本地预览构建结果：

```bash
cd frontend
npm run preview
```

## 服务器部署与更新

一个常见部署方式是让 Nginx 对外监听 `8080`，前端静态文件由 Nginx 提供，`/api/*` 转发到本机 FastAPI 后端 `127.0.0.1:8000`。

后端代码本身已经使用 `/api/...` 路由，FastAPI 不需要额外设置 `root_path="/api"`。

Nginx 反向代理建议保留完整请求路径：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000$request_uri;
    proxy_http_version 1.1;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

服务器更新代码的常规流程：

```bash
cd /home/ubuntu/teacher-assistant
git pull
cd frontend
npm install
npm run build
sudo systemctl restart teacher-assistant-backend
```

更新后检查：

```bash
curl -i http://127.0.0.1:8000/api/health
curl -i http://127.0.0.1:8080/api/health
```

两条都应返回：

```json
{"ok":true}
```

只有修改 Nginx 配置时才需要：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 数据与安全

- SQLite 数据库和 `.env` 均已通过 `.gitignore` 排除，不应提交到仓库。
- 后端启动时会自动创建所需数据表，并对部分旧字段做轻量补齐。
- API Key 采用应用密钥派生的加密方式保存；更换 `APP_SECRET` 会导致旧 API Key 无法解密。
- 当前项目适合个人或小团队本地/内网使用。若部署到公网，应补充 HTTPS、反向代理、日志策略、备份策略和更完整的权限/限流措施。

## 主要 API 分组

- `POST /api/auth/send-code`：发送邮箱验证码
- `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`：账号与鉴权
- `/api/settings/ai`：反馈生成模型配置
- `/api/settings/ai/configs`、`/api/settings/ai/select`：个人模型配置和当前模型选择
- `/api/settings/style-examples`：个人反馈风格样例，支持按 `feedback_type` 区分一对一和晚辅样例
- `/api/students`、`/api/students/{student_id}/feedbacks`、`/api/students/{student_id}/feedbacks/organize`：一对一学生、课堂记录整理与课后反馈
- `/api/feedbacks`、`/api/feedbacks/{feedback_id}`：反馈查询、详情、编辑与删除
- `/api/evening/*`：晚辅班级、晚辅学生、单条/批量晚辅反馈生成保存和按时间段查询全部晚辅反馈
- `/api/group-classes`：班课班级管理

完整字段和请求格式以 FastAPI 自动生成的 `/docs` 为准。

## 维护约定

- 重要功能变化先记录到 `CHANGELOG.md` 顶部的“未发布”区块。
- 阶段完成或发布时，再把“未发布”内容归档到对应日期。
- README 只保留当前可用的功能、启动方式和维护说明；详细演进历史放在 `CHANGELOG.md`。
- 修改涉及接口、环境变量、启动方式或数据模型时，同步检查 README 和 `.env.example`。

### 基于 Git 维护文档

Git 会记录每次提交中的代码差异，但不会记录未提交前的每一次保存或每一次对话。维护文档时建议把 Git 当作证据来源，而不是直接照抄提交信息。

常用检查命令：

```bash
git status --short
git diff
git log --date=iso-local --stat
git show --stat <commit>
git show <commit>
```

推荐流程：

1. 开发中先把当前变化写到 `CHANGELOG.md` 的“未发布”区块。
2. 准备阶段性整理时，用 `git diff` 查看尚未提交的变化，用 `git show <commit>` 查看已提交的实际代码变化。
3. 把代码差异翻译成用户和维护者能理解的记录，例如“新增反馈查询页”“调整反馈生成入口”，而不是“修改 App.vue”。
4. 若变化影响安装、启动、配置、API、数据安全或项目定位，同步更新 README。
5. 提交文档时可以使用类似 `docs: 更新 README 和 CHANGELOG` 的信息；功能提交可以使用 `feat:`、`fix:`、`refactor:`、`docs:` 这类前缀。

## 当前状态

这是一个本地优先的教学反馈助手应用，功能已经从最初的一对一 MVP 扩展到一对一反馈、晚辅反馈、班课班级管理、原始记录整理和个性化风格生成。后续可以继续围绕部署、备份、测试覆盖、权限边界和 README/CHANGELOG 维护流程做工程化完善。
