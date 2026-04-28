import nbtlib
import re

def preprocess_snbt(content):
    # Add commas after values that are followed by a newline + key (or closing brace/bracket)
    # Matches end of a value line that's missing a comma
    content = re.sub(
        r'("(?:[^"\\]|\\.)*"|-?\d+\.?\d*[bBsSlLfFdD]?|-?\d+|true|false|[}\]])([ \t]*\n)([ \t]*(?:"[\w:]+"|[\w]+)\s*:)',
        r'\1,\2\3',
        content
    )
    return content

def parse_snbt_file(content):
    content = preprocess_snbt(content)
    nbt = nbtlib.parse_nbt(content)
    return nbt

def snbt_to_json(obj):
    if isinstance(obj, dict):
        return {k: snbt_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [snbt_to_json(i) for i in obj]
    elif isinstance(obj, nbtlib.String):
        return str(obj)
    elif isinstance(obj, (nbtlib.Int, nbtlib.Long, nbtlib.Short, nbtlib.Byte)):
        return int(obj)
    elif isinstance(obj, (nbtlib.Float, nbtlib.Double)):
        return float(obj)
    else:
        return obj