# 频道别名映射

## 映射表

| 自然语言 | 配置键 | 频道ID | 用途 |
|----------|--------|--------|------|
| 金銮殿、大殿、朝堂 | jinluan | {{jinluan_channel_id}} | 皇帝召见处 |
| 内阁、议事厅、商议处 | neige | {{neige_channel_id}} | 商议政策处 |
| 兵部、军事部、防务处 | bingbu | {{bingbu_channel_id}} | 军事防务处 |

## 使用场景

当用户说"去内阁"时，你应该前往 `{{neige_channel_id}}` 频道。

当用户说"来大殿"时，指的是 `{{jinluan_channel_id}}` 频道。
