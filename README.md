# 教师反馈助手

面向一对一辅导老师、晚辅老师和班课老师的本地优先反馈工作台。项目支持学生管理、课后反馈生成、晚辅月度反馈、班课班级管理、课堂图片资料识别、个人反馈风格样例和账号级模型配置，目标是把日常教学记录整理成可复用、可检索、可直接发给家长的反馈正文。

## 功能概览

- 账号体系：邮箱验证码注册/登录、JWT 鉴权、当前账号信息读取和退出登录。
- 一对一学生：创建、查看、编辑、删除学生，维护年级和科目。
- 一对一课后反馈：新增、生成、保存、查看、编辑、删除反馈，支持反馈标题、课堂内容、课堂表现、课后建议、作业安排、AI 初稿和最终反馈。
- 反馈效率工具：反馈表单草稿自动保存、历史反馈按时间筛选、一对一和晚辅反馈查询、最终反馈一键复制。
- AI 反馈生成：支持 OpenAI-compatible Chat Completions API；没有启用个人风格样例时按标准四段结构生成，启用样例后按老师个人风格生成，也可在单次新增反馈中临时停用个人风格。
- 课堂资料识别：支持上传 JPG、PNG、WEBP 课堂图片和 PDF，调用视觉模型提炼知识点、题型和易错点；该功能可选，识别图片/PDF 会消耗更多视觉模型额度。
- 个人风格样例：维护个人反馈样例，支持新增、查看详情、编辑、启用/停用、删除；生成时只学习语气、结构和详略，最多启用 5 条参与生成，支持从已保存反馈一键设为样例。
- 晚辅模块：维护晚辅班级、批量录入晚辅学生，生成和管理晚辅月度作业反馈，并可按月份查询全部晚辅反馈。
- 班课模块：维护班课班级，当前支持创建、查看、编辑、删除班级和反馈查询占位入口。
- 本地数据：默认使用 SQLite，本地自动建表；API Key 加密存储，不在前端回显明文。

## 技术栈

- 前端：Vue 3 + Vite
- 后端：FastAPI + SQLite
- 网络请求：原生 `fetch`，通过 Vite 代理访问后端 `/api`
- 邮箱验证码：SMTP，默认按 QQ 邮箱配置
- AI 接入：OpenAI-compatible Chat Completions API，文本模型和视觉模型分开配置

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
AI_MODEL=deepseek-v4-flash
ALLOW_GLOBAL_AI_FALLBACK=false
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

登录网页后进入「设置」页面，为当前老师账号配置模型：

- 反馈生成模型：用于生成一对一课后反馈和晚辅月度反馈。
- 图片识别模型：用于识别讲义、板书、作业、错题照片和 PDF 课堂资料。
- 个人反馈风格样例：用于让生成结果更贴近老师自己的表达习惯；没有启用样例时，一对一反馈默认按课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排四段结构输出；启用样例后会优先学习样例里的标题格式、段落结构、语气和详略，但仍必须覆盖四类课堂信息。

每个老师账号的模型配置相互独立。API Key 会加密保存在 SQLite 数据库中，前端只显示是否已配置，不回显明文。

`backend/.env` 中的 `AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 只作为本地开发兜底配置。默认 `ALLOW_GLOBAL_AI_FALLBACK=false`，未配置个人 API Key 的老师不会共用全局模型。只有显式设为 `true` 时，后端才会启用全局兜底。

内置模型预设会尽量跟随各厂商 OpenAI-compatible 官方文档更新。若控制台提示模型无权限或未开通，可优先保留 Base URL，只把模型名改成账号控制台显示的可用模型或推理接入点 ID。

当前内置预设重点覆盖：

- DeepSeek：`https://api.deepseek.com`，默认 `deepseek-v4-flash`。
- 阿里云百炼：`https://dashscope.aliyuncs.com/compatible-mode/v1`，默认 `qwen3.6-plus`；若账号未开放可改用控制台可见的 Qwen 模型。
- Kimi / Moonshot：`https://api.moonshot.ai/v1`，文本默认 `kimi-k2.6`。
- 智谱 AI：`https://open.bigmodel.cn/api/paas/v4`，文本默认 `glm-4-flash-250414`，视觉默认 `glm-4.6v-flash`。
- OpenAI：`https://api.openai.com/v1`，默认 `gpt-5.4-mini`；若账号未开放可改用 `gpt-4.1-mini` 等可用模型。
- 火山方舟豆包视觉：`https://ark.cn-beijing.volces.com/api/v3`，默认 `doubao-1.5-vision-pro-32k`；若控制台要求推理接入点，模型名填写 `ep-...`。

### 个人风格样例

样例标题只用于在样例库中管理和查找，不直接参与 AI 学习。AI 实际读取的是“反馈样例”正文内容。

如果希望 AI 学习标题格式或固定段落结构，请把标题行和完整正文结构一起粘贴到“反馈样例”正文中，例如：

```text
晨钰第3次数学课（4.26）

📖1.课堂学习内容：
……
```

建议启用 3-5 条自己满意的真实反馈样例，尽量覆盖不同学生、不同课次和不同表现类型。若担心串用真实学生名，可先把样例中的姓名匿名化为“学生A / 学生B”。

新增课后反馈时，「课堂内容填写」区域提供「填写参考」入口，可打开可拖动、可调整大小的参考示例浮窗。参考内容只帮助老师理解四个核心字段和“内容补充”应该写什么；“内容补充”用于放漏写或暂时不知道归到哪一栏的补充事实，不是要求 AI 偏向某个部分。参考示例不会保存进反馈，也不是个人风格样例。

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
- `/api/settings/vision`：图片识别模型配置
- `/api/settings/style-examples`：个人反馈风格样例
- `/api/students`、`/api/students/{student_id}/feedbacks`：一对一学生与课后反馈
- `/api/feedbacks`、`/api/feedbacks/{feedback_id}`：反馈查询、详情、编辑与删除
- `/api/evening/*`：晚辅班级、晚辅学生、月度反馈和按月份查询全部晚辅反馈
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
3. 把代码差异翻译成用户和维护者能理解的记录，例如“新增反馈查询页”“增加图片识别模型配置”，而不是“修改 App.vue”。
4. 若变化影响安装、启动、配置、API、数据安全或项目定位，同步更新 README。
5. 提交文档时可以使用类似 `docs: 更新 README 和 CHANGELOG` 的信息；功能提交可以使用 `feat:`、`fix:`、`refactor:`、`docs:` 这类前缀。

## 当前状态

这是一个本地优先的教学反馈助手应用，功能已经从最初的一对一 MVP 扩展到一对一反馈、晚辅月度反馈、班课班级管理、图片识别和个性化风格生成。后续可以继续围绕部署、备份、测试覆盖、权限边界和 README/CHANGELOG 维护流程做工程化完善。
