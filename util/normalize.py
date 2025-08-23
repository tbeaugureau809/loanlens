import re

def normalize_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())
