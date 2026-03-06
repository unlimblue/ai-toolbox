"""
Test the fixed channel selection logic.
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/ai-toolbox/src')

from ai_toolbox.multi_bot.config_loader import get_config

config = get_config()

# Test content
content = "去内阁通知太尉，令其来金銮殿回话".lower()
original_content = "<@1477314385713037445> 去内阁通知太尉，令其来金銮殿回话"
source_channel_id = "1478759781425745940"  # 金銮殿

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

print("=== Old Logic (First Match) ===")
mentioned_channel = None
for alias, channel_key in channel_aliases.items():
    if alias in content:
        mentioned_channel = channel_key
        print(f"Found: {alias} -> {channel_key}")
        break

if mentioned_channel:
    target_id = config.resolve_channel_id(mentioned_channel)
    print(f"Target: {target_id}")
    print(f"Source: {source_channel_id}")
    print(f"Same? {target_id == source_channel_id}")

print("\n=== New Logic (Prefer Cross-Channel) ===")
mentioned_channels = []
for alias, channel_key in channel_aliases.items():
    if alias in content:
        channel_id = config.resolve_channel_id(channel_key)
        if channel_id:
            mentioned_channels.append((channel_key, channel_id, alias))
            print(f"Found: {alias} -> {channel_key} ({channel_id})")

# Select target channel
mentioned_channel = None
target_channel_id = None

for channel_key, channel_id, alias in mentioned_channels:
    if channel_id != source_channel_id:
        mentioned_channel = channel_key
        target_channel_id = channel_id
        print(f"\n✅ Selected cross-channel: {alias} ({channel_id})")
        break

if not mentioned_channel and mentioned_channels:
    mentioned_channel = mentioned_channels[0][0]
    target_channel_id = mentioned_channels[0][1]
    print(f"\n⚠️ No cross-channel found, using first: {mentioned_channels[0][2]}")

print(f"\nTarget: {target_channel_id}")
print(f"Source: {source_channel_id}")
print(f"Same? {target_channel_id == source_channel_id}")
print(f"Is cross-channel? {target_channel_id != source_channel_id}")
