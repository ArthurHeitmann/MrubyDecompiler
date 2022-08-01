ENCODING = "utf-8"

def prefixLines(lines: str, prefix: str) -> str:
    return "\n".join([prefix + l for l in lines.split("\n")])
