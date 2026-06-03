# 教师反馈助手

面向一对一辅导老师、晚辅老师和班课老师的本地优先反馈工作台。项目支持学生管理、一对一课后反馈、晚辅反馈、班课班级管理、个人反馈风格样例和账号级模型配置，目标是把老师输入的真实教学记录整理成可复用、可检索、可直接发给家长的反馈正文。

当前反馈生成的核心原则是：老师负责输入本节课或本次晚辅中真实发生的事实，AI 负责分类、润色和表达优化。AI 不负责补写老师没有提供的知识点、课堂行为、掌握情况、建议、作业或原因判断。

## 功能概览

- 账号体系：邮箱验证码注册/登录、JWT 鉴权、当前账号信息读取和退出登录。
- 一对一学生：创建、查看、编辑、删除学生，维护年级和科目。
- 一对一课后反馈：新增、生成、保存、查看、编辑、删除反馈，支持“原始记录整理”和“直接填四板块”双入口；最终反馈保持课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排四段结构。
- 反馈效率工具：反馈表单草稿自动保存、历史反馈按时间筛选、一对一和晚辅反馈可按学生姓名配合日期查询、最终反馈一键复制。
- 原始记录整理：方便喜欢一次性输入全部课堂记录的老师，AI 只把原始记录分类到四大板块，并提示缺少哪些信息；它不是最终反馈生成，也不替老师补建议或作业。
- AI 反馈生成：支持 OpenAI-compatible Chat Completions API；生成前需要有可用的个人模型配置。AI 根据老师已填写内容做语言润色，输入少则输出短，缺失事实不硬凑。
- 个人风格样例：一对一反馈样例和晚辅反馈样例分开维护，支持新增、查看详情、编辑、启用/停用、删除；生成时只学习对应模块的语气、结构、排版和详略，不迁移样例中的学生事实和建议方向。
- 晚辅模块：维护晚辅班级、批量录入晚辅学生；进入班级后默认先显示学生名单，点击“开始填写反馈”后可用表格按天、按周或按月批量填写晚辅情况、生成 AI 初稿并批量保存；每条反馈可填写本次学科，用于生成“某学生某科晚辅情况”口径，并可按时间段、反馈类型和学生姓名查询全部晚辅反馈。
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

登录网页后进入「设置」页面，添加自己的 OpenAI-compatible API 配置。每条配置需要填写：

- API Key
- Base URL
- 模型名
- 供应商和配置名称

老师可以保存多套个人模型配置，并选择其中一套作为当前使用模型。生成界面也可直接选择“本次使用模型”，用于临时切换本次一对一整理、一对一反馈、晚辅单条反馈或晚辅批量反馈使用的模型。

个人 API Key 会加密保存在 SQLite 数据库中，前端只显示是否已配置，不回显明文。项目不再提供服务端统一模型；没有可用个人模型配置时，AI 相关功能会提示先到设置页添加 API。

设置页内置填写预设，方便快速带出常见 Base URL 和模型名：

- DeepSeek：`https://api.deepseek.com`，默认 `deepseek-v4-pro`。
- 豆包 / 火山方舟：`https://ark.cn-beijing.volces.com/api/v3`，模型名需与控制台已开通模型或推理接入点保持一致。
- 自定义兼容接口：用于其他 OpenAI-compatible 文本生成模型，需手动填写 Base URL、模型名和 API Key。

## 反馈生成逻辑

### 一对一反馈

一对一反馈保留四段结构：

1. 课堂学习内容
2. 课堂表现与知识掌握情况
3. 课后建议
4. 作业安排

生成前，课堂学习内容和课堂表现必须填写真实信息。课后建议和作业安排也建议写清楚；如果本节课确实没有额外建议或额外作业，可以使用快捷确认“本次无额外建议”“本次无额外作业”，最终反馈会自然表达为暂无额外安排，而不会出现内部缺失提示。

AI 只润色老师输入中的事实，不新增知识点、课堂行为、掌握情况、建议、作业、原因判断或长期评价。低质量输入会得到较短的反馈，高质量输入会保留更多具体信息。

### 原始记录整理

原始记录整理服务于喜欢一次性输入全部课堂内容的老师。它的作用是把老师的原始课堂记录分类到四大板块：

- `lesson_summary`：课堂学习内容
- `performance_summary`：课堂表现与知识掌握情况
- `advice_summary`：课后建议
- `homework_plan`：作业安排

整理完成后，前端会显示哪些信息已经覆盖、哪些还需要补充或确认。整理失败时，后端有本地兜底分类逻辑，尽量不让用户流程被模型返回格式阻断。

### 晚辅反馈

晚辅反馈的用户侧口径是“晚辅情况”，不再局限于作业完成情况。老师填写的晚辅情况可以包含作业完成、订正、纪律、学习状态、主要问题、表扬点和建议等信息。

后端字段名仍保留 `homework_summary`，这是为了兼容既有数据库和接口；前端展示和文案语义都按“晚辅情况”处理。

晚辅反馈生成以自然家长消息为主：无样例时通常 1 个自然段，信息较多时最多 2 段。老师没写建议时，AI 只允许补一句很轻的方向性提醒，并且必须贴近已有事实，不能变成具体训练安排、家长任务或额外作业。

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

未启用个人风格时，一对一反馈会使用项目内置默认样例作为基础表达参考。启用个人风格后，系统不会再混入默认样例，避免默认基底干扰老师自己的写法。个人风格只学习语气、排版、段落节奏和标题习惯，不迁移样例中的事实、问题、建议方向或学生经历。

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
