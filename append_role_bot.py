
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @ mentions from content."""
        import re
        mentions = []
        # Match <@&role_id> format
        for match in re.finditer(r'<@&(\d+)', content):
            # Map role ID to bot ID
            # This is a simplified version - should use config mapping
            mentions.append(f"role_{match.group(1)}")
        return mentions
