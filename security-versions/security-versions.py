__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import re
from typing import List

SECURITY_FILE = "SECURITY.md"
MINOR_ROW_PATTERN = re.compile(r"^\| *\d+\.\d+\.x ", re.MULTILINE)
SEPARATOR_ROW_PATTERN = re.compile(r"^\|[-\s|]*$")


def row(version: str, supported: str) -> str:
    return f"| {version:<7} | {supported:<18} |"


def rewrite_table(lines: List[str], new_minor: str) -> List[str]:
    """
    Replace the rows under the table's separator row with this minor (supported) and everything older (not).
    """
    rewritten = []
    table = "before"
    for line in lines:
        if table == "rows":
            if line.startswith("|"):
                continue
            table = "after"
        rewritten.append(line)
        if table == "before" and SEPARATOR_ROW_PATTERN.match(line):
            rewritten.append(row(f"{new_minor}.x", ":white_check_mark:"))
            rewritten.append(row(f"< {new_minor}", ":x:"))
            table = "rows"
    return rewritten


def main() -> None:
    new_minor = os.environ["VERSION"].rsplit(".", 1)[0]
    if not os.path.exists(SECURITY_FILE):
        return

    with open(SECURITY_FILE) as f:
        security = f.read()

    if not MINOR_ROW_PATTERN.search(security) or re.search(rf"^\| {re.escape(new_minor)}\.x ", security, re.MULTILINE):
        return

    with open(SECURITY_FILE, "w") as f:
        f.write("\n".join(rewrite_table(security.split("\n"), new_minor)))
    print(f"SECURITY.md now supports {new_minor}.x")


if __name__ == "__main__":
    main()
