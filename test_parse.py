"""
Test script to diagnose cross-channel task parsing issues.
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/ai-toolbox/src')

from ai_toolbox.multi_bot.config_loader import get_config, MultiBotConfig
from ai_toolbox.multi_bot.models import UnifiedMessage
from ai_toolbox.multi_bot.message_bus import MessageBus

# Create a test message
class TestMessage:
    def __init__(self):
        self.id = "test123"
        self.author_id = "1477269928720466011"  # unlimblue
        self.author_name = "unlimblue"
        self.content = "<@1477314385713037445> 去内阁通知太尉，令其来金銮殿回话"
        self.channel_id = "1478759781425745940"  # 金銮殿
        self.mentions = ["chengxiang"]  # 从mention解析的bot_id
        self.timestamp = __import__('datetime').datetime.now()

# Load config
config = get_config()

print("=== Config Debug ===")
print(f"Channels: {config.channels}")
print(f"Bots: {list(config.bots.keys())}")
print(f"Discord user_id_to_bot: {config.discord_config.get('user_id_to_bot', {})}")

# Create message
msg = TestMessage()

print("\n=== Message Debug ===")
print(f"Content: {msg.content}")
print(f"Channel: {msg.channel_id} (金銮殿)")
print(f"Mentions: {msg.mentions}")

# Parse manually
content = msg.content.lower()
original_content = msg.content

has_mention = "@" in original_content or "<@" in original_content
has_action = any(k in content for k in ["去", "到", "在", "通知", "叫", "传"])

print(f"\n=== Parse Check ===")
print(f"has_mention: {has_mention}")
print(f"has_action: {has_action}")

# Channel aliases
channel_aliases = {
    "金銮殿": "jinluan",
    "大殿": "jinluan",
    "朝堂": "jinluan",
    "内阁": "neige",
    "议事厅": "neige",
    "商议处": "neige",
    "兵部": "bingbu",
    "军事部": "bingbu",
    "防务处": "bingbu",
}

mentioned_channel = None
for alias, channel_key in channel_aliases.items():
    if alias in content:
        mentioned_channel = channel_key
        print(f"Found channel: {alias} -> {channel_key}")
        break

if mentioned_channel:
    target_channel_id = config.resolve_channel_id(mentioned_channel)
    print(f"Target channel ID: {target_channel_id}")
    print(f"Source channel ID: {msg.channel_id}")
    print(f"Same? {target_channel_id == msg.channel_id}")

# Check target bots
target_bots = list(msg.mentions) if msg.mentions else []
print(f"\nInitial target bots: {target_bots}")

# Check content for bot names
for bot_id, bot_config in config.bots.items():
    if bot_id not in target_bots:
        bot_name = bot_config.get('name', '')
        if bot_name and bot_name in original_content:
            print(f"Found bot name in content: {bot_name} ({bot_id})")
            target_bots.append(bot_id)

print(f"Final target bots: {target_bots}")
