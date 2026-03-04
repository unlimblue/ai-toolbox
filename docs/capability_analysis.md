# OpenClaw 能力扫描报告

## OpenClaw 原生工具能力

### 1. 文件与代码操作
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `read` | 读取文件内容 | ✅ 代码中可复用 |
| `write` | 创建/覆盖文件 | ✅ 代码中可复用 |
| `edit` | 精确文本编辑 | ✅ 代码中可复用 |
| `exec` | 执行 shell 命令 | ⚠️ 部分覆盖（CLI）|
| `process` | 管理后台进程 | ❌ 未覆盖 |

### 2. 网络与信息检索
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `web_search` | Brave 搜索 | ❌ **未覆盖** |
| `web_fetch` | 获取网页内容 | ❌ **未覆盖** |
| `browser` | 浏览器自动化 | ❌ **未覆盖** |

### 3. 多媒体处理
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `image` | 图像分析 (Vision) | ❌ **未覆盖** |
| `pdf` | PDF 文档分析 | ❌ **未覆盖** |
| `tts` | 文本转语音 | ❌ **未覆盖** |

### 4. 系统与设备
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `canvas` | 画布呈现 | ❌ **未覆盖** |
| `nodes` | 节点设备控制 | ❌ **未覆盖** |

### 5. 通讯与协作
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `message` | 消息发送 (Discord等) | ⚠️ Discord Bot 部分覆盖 |

### 6. AI 会话管理
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `sessions_spawn` | 生成子代理 | ❌ **未覆盖** |
| `subagents` | 子代理管理 | ❌ **未覆盖** |
| `session_status` | 会话状态 | ❌ **未覆盖** |

### 7. 记忆与上下文
| 工具 | 功能 | ai-toolbox 覆盖 |
|------|------|----------------|
| `memory_search` | 语义搜索记忆 | ❌ **未覆盖** |
| `memory_get` | 获取记忆片段 | ❌ **未覆盖** |

---

## ai-toolbox 当前能力

### 已覆盖
| 能力 | 实现方式 |
|------|----------|
| ✅ AI 文本对话 | Kimi (Coding)、OpenRouter |
| ✅ 流式响应 | 支持 SSE 流式 |
| ✅ 多提供商切换 | 工厂模式实现 |
| ✅ Discord Bot | 独立模块，斜杠命令 |
| ✅ CLI 工具 | `ai-toolbox chat` |
| ✅ REST API | FastAPI 服务 |
| ✅ 单元测试 | pytest 全覆盖 |

---

## 未覆盖的高价值能力

### 高优先级（推荐添加）

#### 1. 图像/视觉模型支持 🔥
**用途**：分析图片、OCR、图像生成

**实现建议**：
```python
# 添加到 providers/
class VisionClient(BaseProvider):
    async def analyze_image(self, image_url: str, prompt: str) -> str:
        # 支持 GPT-4V、Claude Vision、Gemini Vision
        pass
```

**调用方式**：
```bash
ai-toolbox vision --image photo.jpg --prompt "描述这张图片"
```

#### 2. 网络搜索集成 🔥
**用途**：实时信息检索、RAG 增强

**实现建议**：
```python
# 新模块: src/ai_toolbox/tools/search.py
class SearchTool:
    async def search(self, query: str) -> list[SearchResult]:
        # 集成 DuckDuckGo、Brave、Google
        pass
```

**调用方式**：
```bash
ai-toolbox search "最新 AI 新闻" --provider duckduckgo
ai-toolbox chat --prompt "总结搜索结果" --context-search "AI新闻"
```

#### 3. 文档处理（PDF/Word）
**用途**：文档分析、内容提取

**实现建议**：
```python
# 新模块: src/ai_toolbox/tools/documents.py
class DocumentProcessor:
    async def extract_text(self, file_path: str) -> str:
        # 支持 PDF、DOCX、TXT
        pass
```

#### 4. 工具调用/函数调用 (Function Calling) 🔥
**用途**：让 AI 调用外部工具、自动化工作流

**实现建议**：
```python
# 扩展 providers/base.py
class ToolEnabledProvider(BaseProvider):
    async def chat_with_tools(
        self, 
        messages, 
        tools: list[Tool],
        **kwargs
    ) -> ChatResponse:
        # 支持 OpenAI/Claude function calling
        pass
```

**使用场景**：
- AI 自己决定何时搜索网页
- AI 调用计算器解决数学问题
- AI 读取本地文件分析

### 中优先级

#### 5. 语音处理（TTS/STT）
**用途**：语音交互

**实现建议**：
```python
# 新模块: src/ai_toolbox/tools/voice.py
class VoiceTool:
    async def text_to_speech(self, text: str, voice: str) -> bytes:
        # 集成 ElevenLabs、OpenAI TTS
        pass
    
    async def speech_to_text(self, audio: bytes) -> str:
        # 集成 Whisper
        pass
```

#### 6. 代码执行沙箱
**用途**：安全执行 AI 生成的代码

**实现建议**：
```python
# 新模块: src/ai_toolbox/tools/sandbox.py
class CodeSandbox:
    async def execute(self, code: str, language: str) -> ExecutionResult:
        # Docker 沙箱执行 Python、JavaScript 等
        pass
```

#### 7. 浏览器自动化
**用途**：网页抓取、自动化操作

**实现建议**：
```python
# 新模块: src/ai_toolbox/tools/browser.py
class BrowserTool:
    async def scrape(self, url: str) -> str:
        # 使用 Playwright 抓取网页
        pass
    
    async def screenshot(self, url: str) -> bytes:
        # 网页截图
        pass
```

### 低优先级

#### 8. 多代理协作
**用途**：复杂任务分解给多个专业代理

#### 9. 记忆/上下文管理
**用途**：长期记忆、会话上下文持久化

#### 10. 画布呈现
**用途**：可视化展示结果

---

## 推荐开发路线图

### Phase 1: 工具调用 (Function Calling)
让 AI 能够调用工具，实现自动化工作流

### Phase 2: 视觉模型 + 搜索
扩展多模态能力和实时信息获取

### Phase 3: 文档处理 + 语音
增强文件处理和交互方式

### Phase 4: 沙箱 + 浏览器
实现安全的代码执行和网页自动化

---

## 与 OpenClaw 的关系

**互补定位**：
- **OpenClaw**: 系统级工具、环境控制、多模态输入
- **ai-toolbox**: AI 模型统一管理、对外 API、Discord 集成

**协同使用**：
```python
# OpenClaw 调用 ai-toolbox
from ai_toolbox.providers import create_provider

client = create_provider("kimi", api_key)
response = await client.chat(messages)

# ai-toolbox 调用 OpenClaw 工具
# 通过 OpenClaw 提供的 web_search、browser 等工具
```