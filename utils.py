ENCODING = "shift-jis"

def prefixLines(lines: str, prefix: str) -> str:
    return "\n".join([prefix + l for l in lines.split("\n")])
