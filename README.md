# 教师一对一反馈助手

一个面向一对一辅导老师的 MVP 网页项目：老师注册登录后，可以管理自己的学生，并在学生专属页面中记录课程内容、调用 AI 生成课后反馈、修改后保存历史记录。

## 技术栈

- 后端：FastAPI + SQLite
- 前端：Vue + Vite
- 邮箱验证码：QQ 邮箱 SMTP
- AI 接入：OpenAI-compatible Chat Completions API

## 项目结构

```text
teacher_assistant/
  backend/          FastAPI 后端
  frontend/         Vue 前端
  README.md
```

## 后端启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

后端启动后可以打开接口文档：

```text
http://127.0.0.1:8000/docs
```

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173
```

## QQ 邮箱配置

编辑 `backend/.env`：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=你的QQ邮箱
SMTP_PASSWORD=你的QQ邮箱授权码
SMTP_FROM=你的QQ邮箱
```

注意：`SMTP_PASSWORD` 不是 QQ 邮箱登录密码，而是 QQ 邮箱设置中生成的 SMTP 授权码。

如果暂时不配置邮箱，验证码会打印在后端终端里，方便本地开发测试。

## AI 配置

登录网页后，进入侧边栏的「设置」页面，为当前老师账号配置自己的模型 API：

- 选择模型供应商，例如 DeepSeek、OpenAI、通义千问、智谱 AI。
- 填写 `API Key`、`Base URL` 和模型名。
- 点击「测试连接」，成功后再保存配置。

每个老师账号的 AI 配置相互独立，API Key 会加密保存在本地 SQLite 数据库里，不会在网页中回显明文。

`backend/.env` 里的下面几项只作为本地开发兜底配置使用，默认不会让所有老师共用：

```env
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
ALLOW_GLOBAL_AI_FALLBACK=false
```

只有把 `ALLOW_GLOBAL_AI_FALLBACK` 改成 `true` 时，未配置个人 API 的老师才会使用 `.env` 中的全局模型配置。
