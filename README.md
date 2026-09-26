# 弓道纪要 · 传统弓箭制作工艺传承平台

传统弓箭制作技艺多靠口传心授：匠人围在木工坊里讨论胎角比例、训弓技巧、木料选材，
这些经验如果不记录就会随人流失。弓道纪要把这套口传知识沉淀成可检索的工艺档案，
并同步给非遗保护中心。

前后端分离的全栈应用：

- **后端**（`backend/`，FastAPI）：匠人档案、手艺人交流（含 WebSocket 实时消息）、
  录音上传与处理（保留木工坊环境声底 → 转写口传知识 → 标记匠人流派）、
  生成工艺档案、邮件发送至非遗保护中心。
- **前端**（`frontend/`，React + TypeScript + Tailwind）：角弓拆解图、木材纹理库、
  手艺人交流、音频上传、工艺档案。

## 目录结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 应用与路由注册
│   │   ├── database.py        # 引擎 / 会话 / Base
│   │   ├── models.py          # SQLAlchemy 模型
│   │   ├── schemas.py         # Pydantic 请求/响应模型
│   │   ├── api/
│   │   │   ├── craftsmen.py   # 匠人档案
│   │   │   ├── messages.py    # 交流消息 + WebSocket
│   │   │   ├── audio.py       # 录音上传/处理/转写查询
│   │   │   ├── archives.py    # 工艺档案生成/导出/邮件
│   │   │   └── materials.py   # 木料与弓部件 + 种子数据
│   │   └── services/
│   │       ├── audio_service.py         # librosa 环境声保留 + 降噪
│   │       ├── transcription_service.py # Whisper 转写 + 关键词提取
│   │       ├── diarization_service.py   # pyannote 说话人分离 + 流派预测
│   │       ├── archive_service.py       # OpenAI 档案摘要 + HTML 生成
│   │       └── email_service.py         # 邮件发送
│   └── tests/                 # pytest 测试
├── frontend/                  # React + TS 前端
├── requirements.txt           # 轻量依赖（可离线跑测试）
├── requirements-ml.txt        # Whisper / pyannote / librosa 等重型可选依赖
├── docker-compose.yml
├── CLAUDE.md                  # 本仓库工程规则，动手前先读
└── README.md
```

## 运行方式

后端（Python 3.11+）：

```bash
pip install -r requirements.txt
cd backend && uvicorn app.main:app --reload --port 8000    # http://localhost:8000
```

种子数据（首次运行后调一次）：

```bash
curl -X POST http://localhost:8000/api/materials/seed-data
```

测试：

```bash
cd backend && python -m pytest -q
```

`requirements.txt` 只含轻量依赖。Whisper / pyannote / librosa（见 `requirements-ml.txt`）与
`OPENAI_API_KEY`、SMTP 配置都是**可选的**：未安装模型、未配置密钥时，语音与摘要走确定性的
离线分支，因此后端与测试可在无网络、无 GPU、不调用任何外部 API 的环境下跑通。

## HTTP 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| GET/POST | `/api/craftsmen/` | 匠人列表 / 新建（支持 `skip`、`limit`） |
| GET/PUT/DELETE | `/api/craftsmen/{id}` | 匠人详情 / 更新 / 删除 |
| GET/POST | `/api/messages/` | 交流消息列表 / 发送 |
| WS | `/api/messages/ws` | 实时消息广播 |
| GET | `/api/audio/recordings` | 录音列表 |
| GET | `/api/audio/recordings/{id}` | 录音详情 |
| POST | `/api/audio/upload` | 上传录音（表单 `file`，查询参数 `workshop`） |
| POST | `/api/audio/process/{id}` | 触发处理（后台任务） |
| GET | `/api/audio/recordings/{id}/transcripts` | 该录音的转写片段（含说话人与流派） |
| GET | `/api/audio/recordings/{id}/diarization` | 该录音的说话人分段 |
| GET/POST | `/api/archives/` | 档案列表 |
| GET | `/api/archives/{id}` | 档案详情 |
| POST | `/api/archives/generate/{recording_id}` | 依据某条已转写录音生成档案 |
| GET | `/api/archives/{id}/html` | 导出档案 HTML |
| POST | `/api/archives/send-email` | 把档案邮件发给非遗保护中心 |
| GET/POST | `/api/materials/woods` | 木料列表 / 新建 |
| GET/POST | `/api/materials/bow-parts` | 弓部件列表 / 新建 |
| POST | `/api/materials/seed-data` | 写入种子数据 |

## 行为规格（验收标准）

本节是本次修复的验收依据，逐条以本节为准。

### A. 请求校验与错误语义

1. 接收 JSON body 的写接口，在必填字段缺失、类型不符、或取值非法时，必须返回 `422`
   （FastAPI 的校验错误）并带可读的错误信息；**不得**接受空字符串之类的无效值。
2. 字符串型必填字段（如匠人 `name`、消息 `content`、木料 `name`、弓部件 `name`）必须
   **去除首尾空白后非空**；仅含空白的值一律视为非法。
3. 数值型查询参数越界必须被拒绝：`skip` 不得为负、`limit` 必须为正且在合理上界内
   （如 `1..200`）；非法取值返回 `422`，不得静默返回空列表或全量数据。
4. 资源不存在必须返回 `404`（JSON 错误体），不得是 `500`。

### B. 数据完整性

5. 创建消息时若 `craftsman_id` 指向不存在的匠人，必须返回 `404`，**不得**写入一条悬空外键的记录。
   `craftsman_id` 缺省（`null`）是允许的（匿名发言）。
6. 删除匠人时，其名下的消息与转写不应留下指向已删除记录的悬空引用；具体策略按规格实现并保持一致。
7. 种子数据接口 `POST /api/materials/seed-data` 必须幂等：重复调用不得产生重复记录，
   返回体需如实反映本次是否写入（`woods_added` / `bow_parts_added` / `craftsmen_added`）。

### C. 录音上传

8. 上传必须按扩展名白名单校验（`wav` / `mp3` / `m4a` / `flac` / `aac` / `ogg`）；
   非白名单（如 `.exe`、`.sh`）或无扩展名必须返回 `400`，**不得**当作音频接收。
9. 上传返回的 `filename` 必须是**原始文件名**（含中文），不得携带任何路径成分
   （`../../etc/passwd.wav` 必须规整为 `passwd.wav`）；落盘文件名必须去重且不得逃逸出上传目录。
10. 上传接口在未提供文件时必须返回 `422`。

### D. 实时消息（WebSocket）

11. `ConnectionManager` 必须能容忍异常输入：客户端发送**非法 JSON** 时，连接不得崩溃，
    也不得让该连接残留在 `active_connections` 里；应把连接安全地摘除（或返回错误提示后继续存活）。
12. 广播必须对单个坏连接免疫：当某个连接发送失败（例如已关闭）时，必须把它摘除并**继续向其余
    连接广播**，不得因为一个坏连接就让后续所有连接收不到消息。
13. 连接正常断开（含异常断开）时必须从 `active_connections` 中摘除；重复摘除不应抛异常。

### E. 工艺档案与邮件

14. `archive_service.generate_archive_summary` 在**未配置 `OPENAI_API_KEY`**（服务不可用）时，
    允许返回确定性的离线摘要，但结果必须可识别（带 `is_fallback` 之类的标记）。
15. 一旦**真的发起**了 OpenAI 调用但失败（网络错误、`429`、鉴权失败等），必须把异常向上抛出；
    不得改用离线摘要冒充成功结果并落库。
16. `POST /api/archives/send-email` 只有在**确实投递成功**时才把 `sent_to_feiyi` 置为 `1`
    并写入 `sent_at`；未配置邮件服务或投递失败时必须保持 `sent_to_feiyi=0`，并返回失败状态
    （`4xx`/`5xx` 或明确标记 `success=false` 且**不**改动记录的已发送状态）。
17. 生成档案的前置条件不变：录音必须已处于 `transcribed` 状态，否则返回 `400`。

### F. 不得回归的既有正确行为

18. `/health`、匠人 CRUD、消息列表/发送、木料与弓部件查询、录音上传与列表、档案列表/详情/HTML 导出
    必须保持可用。
19. `diarization_service.predict_school` 在文本命中多个流派关键词时，必须给出**确定且可解释**的结果
    （置信度反映命中数占比）；无任何命中时返回「未知流派」且置信度为 `0`。
20. `transcription_service.extract_keywords` 的分类口径保持不变（材料 / 工艺 / 结构 / 技术 / 其他）。

## 变更说明

本次修复以「行为规格」为验收标准，逐条修正了以下缺陷（根因 → 修法）：

- **必填字符串接受空白值**：`schemas.py` 的 `name` / `school` / `content` 等字段只声明了
  `str` 类型，空字符串与纯空白都能通过校验。→ 新增统一的 `field_validator`，
  去除首尾空白后为空即返回 422，入库值同时被规整（去首尾空白）。
- **分页参数无边界**：`skip` / `limit` 是普通 `int` 参数，负数与 `limit=0` 被静默接受。
  → 全部列表接口改用 `Query(0, ge=0)` 与 `Query(100, ge=1, le=200)`，越界返回 422。
- **消息外键悬空**：`POST /api/messages/` 不校验 `craftsman_id` 是否存在；删除匠人后其名下
  消息仍指向已删除记录。→ 创建消息时匠人不存在返回 404（`craftsman_id=null` 的匿名发言
  仍允许）；删除匠人时将其消息与转写的 `craftsman_id` 置空（转为匿名），不留悬空引用。
- **种子数据返回体不诚实**：重复调用虽然不会重复写入，但返回的 `message` 永远是
  "seeded successfully"。→ 返回体按本次实际写入情况给出 `message`，
  `woods_added` / `bow_parts_added` / `craftsmen_added` 如实反映是否写入。
- **上传不做类型校验、文件名未规整**：任何扩展名（含无扩展名）都被当作录音接收，
  且 `filename` 原样回显可能携带 `../../` 路径成分。→ 按扩展名白名单
  （wav/mp3/m4a/flac/aac/ogg）校验，非白名单或无扩展名返回 400；文件名先做
  `basename` 规整（兼容 Windows 反斜杠路径），落盘文件使用 UUID 名，不会逃逸出上传目录；
  未提供文件时由 `File(...)` 返回 422。
- **WebSocket 连接泄漏与广播中断**：收到非法 JSON 时异常逃逸出循环，连接永久残留在
  `active_connections`；广播时一个坏连接抛异常会中断后续所有连接；`disconnect` 用
  `list.remove`，重复摘除会抛 `ValueError`。→ 非法 JSON 回错误提示后连接继续存活；
  `finally` 保证断开（含异常断开）一定摘除；广播逐个 `try`，坏连接摘除后继续发给其余
  连接；`disconnect` 改为幂等。WebSocket 写入消息同样走 `MessageCreate` 校验与匠人存在性
  检查。前端"偶尔卡死收不到新消息"即广播中断所致，已随后端修复。
- **档案摘要失败伪装成功**：`archive_service` 把真实 OpenAI 调用的异常吞掉并改用离线
  模板返回。→ 未配置 `OPENAI_API_KEY` 时走离线摘要且结果带 `is_fallback: true` 标记
  （落库档案的 `content.is_fallback` 同样置真）；一旦真实发起调用且失败，异常直接向上
  抛出，不再落库伪装成功。
- **邮件假装发送**：`send-email` 只要响应带 `mock_mode` 就标记 `sent_to_feiyi=1`。
  → 只有 `success=true`（确实投递成功）才标记已发送并写入 `sent_at`；未配置 SMTP 或
  投递失败时响应为 `success=false` 且档案保持未发送状态。前端 `Archives.tsx` 同步修正，
  不再把 `mock_mode` 当作发送成功提示。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic v2、SQLite；Whisper / pyannote / librosa / OpenAI 为可选
- 前端：React 18、TypeScript、Tailwind CSS、Vite、axios
- 测试：pytest（`backend/tests`）

## 许可证

MIT License
