# LocalManus 优先预置技能 (Skill) 路线图

基于对 GitHub 顶级开源项目（如 OpenInterpreter, AutoGPT, LangChain）的调研以及 LocalManus 独特的 **Firecracker + AgentScope** 架构，我为您提取了以下四个最值得优先实现的“杀手级”技能。

## 1. 核心设计原则 (Skill Best Practices)
在实现以下技能前，建议遵循行业通用的技能开发规范：
-   **Schema 驱动**：每个 Skill 必须包含完善的输入输出 JSON Schema，方便 AgentScope 的 Planner 进行参数对齐。
-   **环境标签**：明确标注该 Skill 是否需要进入 **Firecracker** 沙箱运行（如涉及执行 Python 代码或安装依赖）。
-   **观测性日志**：Skill 执行过程中的每一步 Stdout 必须带上 `[Skill: Name]` 前缀，以便前端 WebSocket 实时展示。

---

## 2. 优先实现的四大预置技能

### 第一优先级：DevScope - 全栈工程专家 (Full-Stack Coding)
**功能**：自主创建、修改及测试完整的 Web 应用程序或脚本项目。
-   **能力详情**：
    -   **多文件管理**：支持跨目录的文件读写，管理复杂的项目结构（如 Next.js 或 FastAPI 项目）。
    -   **全栈预览**：在 Firecracker 沙箱内启动 Web 服务（如 `npm run dev`），并通过端口转发或安全代理供前端实时预览。
    -   **Git 集成**：自动初始化 Git 仓库，生成规范的提交记录。
    -   **LocalManus 特色**：利用 Firecracker 的快照功能快速保存开发状态（Checkpoint），方便用户随时回滚或分支尝试。
-   **推荐理由**：这是通用 Agent 进化为“程序员”的关键一步，充分发挥了隔离环境执行复杂构建任务的优势。

### 第二优先级：DataScope - 深度数据分析师 (Code Interpreter)
**功能**：在 Firecracker 沙箱中执行 Python 或 R 代码，处理 CSV/Excel 数据。
-   **能力详情**：
    -   自动读取上传的表格文件。
    -   利用 `pandas` 进行清洗，利用 `matplotlib/plotly` 生成可视化图表。
    -   **LocalManus 特色**：利用 Firecracker 的 **VSOCK** 快速回传生成的图片二进制流，前端直接预览。
-   **推荐理由**：这是 Agent 最具生产力的能力，Firecracker 的隔离性让执行复杂脚本无后顾之忧。

### 第二优先级：IntelSearch - 深度调研专家 (Research Agent)
**功能**：自主搜索互联网、抓取内容并生成综述报告。
-   **能力详情**：
    -   集成 `Tavily` 或 `Serper` 搜索 API。
    -   内置 `Readability` 解析器，提取网页正文，去除广告。
    -   **LocalManus 特色**：即便网页包含恶意脚本，在沙箱内抓取也能确保宿主机绝对安全。
-   **推荐理由**：它是“Omnibox”处理复杂提问（如“对比最近三年的 AI 芯片市场份额”）的核心引擎。

### 第三优先级：Studio-Render - 结构化文稿渲染 (Structured Output)
**功能**：将 Agent 生成的大纲实时转化为专业的 PPTX 或 PDF。
-   **能力详情**：
    -   基于 `python-pptx` 或 `Pandoc` 的后端渲染引擎。
    -   预置多种排版模板。
    -   **LocalManus 特色**：用户在聊天框输入修改意见，Agent 动态调整渲染代码，实现“所见即所得”的编辑体验。
-   **推荐理由**：对应 PRD 中的“演示文稿生成”核心卖点，直接产出可交付成果。

### 第四优先级：Doc-Transformer - 全能文档处理 (Utility)
**功能**：跨格式文档转换与深度总结。
-   **能力详情**：
    -   PDF 转 Markdown、Word 转 PDF。
    -   视频链接 (Bili/YouTube) 提取字幕并总结重点。
    -   **LocalManus 特色**：支持多文件批处理，利用沙箱并行执行提高吞吐量。
-   **推荐理由**：极低成本实现的高价值高频率工具，能快速建立用户粘性。

---

## 3. 实现路线建议 (Roadmap)
1.  **Week 1**: 建立 Skill Registry（技能注册中心），实现 **DataScope** (基础版 Python 代码执行)。
2.  **Week 2**: 完善沙箱网络配置，接入 **IntelSearch**。
3.  **Week 3**: 设计 **Studio-Render** 模板体系，实现首个 PPTX 导出。
