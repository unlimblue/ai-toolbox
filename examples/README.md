# 示例

```python
from ai_toolbox import create_provider
from ai_toolbox.providers import ChatMessage

async def main():
    client = create_provider("kimi", api_key="your_key")
    messages = [ChatMessage(role="user", content="你好")]
    response = await client.chat(messages)
    print(response.content)
    await client.close()

import asyncio
asyncio.run(main())
```