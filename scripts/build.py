import os
import re
import subprocess
from datetime import datetime


def get_clean_title(content):
    line = content.strip().split("\n")[0].strip()
    if line.startswith("#"):
        return line.lstrip("#").strip()
    return line[:15]


def parse_entries_with_lines(filepath):
    """
    Parses a markdown file split by '===' delimiters into entries,
    recording the exact 1-indexed start and end line ranges in HEAD.
    """
    try:
        content = subprocess.check_output(
            ["git", "show", f"HEAD:{filepath}"]
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        return []

    lines = content.splitlines(keepends=True)
    entries = []
    current_lines = []
    start_line = 1

    for line_idx, line in enumerate(lines, start=1):
        if re.match(r"^\s*(?<!=)={3}(?!=)\s*$", line):
            text = "".join(current_lines).strip()
            if text:
                entries.append(
                    {
                        "content": text,
                        "title": get_clean_title(text),
                        "start_line": start_line,
                        "end_line": line_idx - 1,
                    }
                )
            current_lines = []
            start_line = line_idx + 1
        else:
            current_lines.append(line)

    final_text = "".join(current_lines).strip()
    if final_text:
        entries.append(
            {
                "content": final_text,
                "title": get_clean_title(final_text),
                "start_line": start_line,
                "end_line": len(lines),
            }
        )

    return entries


def get_entry_blame_info(filepath, start_line, end_line):
    """
    Runs git blame across the entry's line range to identify:
    1. The latest modification commit & date touching this entry.
    2. The original creation commit & date of this entry.
    """
    cmd = [
        "git",
        "blame",
        "-L",
        f"{start_line},{end_line}",
        "--line-porcelain",
        filepath,
    ]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode(
            "utf-8"
        )
    except subprocess.CalledProcessError:
        return None, None

    latest_ts = 0
    latest_hash = None
    oldest_ts = float("inf")
    oldest_hash = None

    current_hash = None

    for line in raw.splitlines():
        if len(line) == 40 and not line.startswith(" "):
            current_hash = line.split()[0]
        elif line.startswith("author-time "):
            ts = int(line.split()[1])
            if ts > latest_ts:
                latest_ts = ts
                latest_hash = current_hash
            if ts < oldest_ts:
                oldest_ts = ts
                oldest_hash = current_hash

    latest_date = (
        datetime.fromtimestamp(latest_ts).strftime("%Y-%m-%d")
        if latest_ts
        else "Unknown"
    )
    oldest_date = (
        datetime.fromtimestamp(oldest_ts).strftime("%Y-%m-%d")
        if oldest_ts != float("inf")
        else "Unknown"
    )

    return {
        "latest": {"hash": latest_hash, "date": latest_date},
        "created": {"hash": oldest_hash, "date": oldest_date},
    }


def get_entry_line_history(filepath, start_line, end_line):
    """
    Uses git log -L to track historical revisions of this specific block.
    Extracts each commit hash, date, and diff/patch for collapsible history.
    """
    cmd = [
        "git",
        "log",
        "-L",
        f"{start_line},{end_line}:{filepath}",
        "--pretty=format:COMMIT:%H|%ad",
        "--date=short",
        "-p",
    ]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode(
            "utf-8"
        )
    except subprocess.CalledProcessError:
        return []

    history = []
    blocks = raw.split("COMMIT:")

    for b in blocks:
        b = b.strip()
        if not b:
            continue
        lines = b.splitlines()
        header = lines[0]
        h, d = header.split("|")
        patch = "\n".join(lines[1:]).strip()
        history.append({"hash": h, "date": d, "patch": patch})

    return history


def build():
    if not os.path.exists("dist"):
        os.makedirs("dist")

    y = datetime.now().year
    year_range = "2026" if y == 2026 else f"2026-{y}"
    back_to_main = "[Back to main](https://panayang.blog.apich.org)"
    footer = f"\n\n---\n<center><small>{back_to_main} | Copyright &copy; {year_range} Xinyu Yang</small></center>\n"

    if not os.path.exists("blog"):
        return

    blogs = [f for f in os.listdir("blog") if f.endswith(".md")]
    catalog = {}

    for b in blogs:
        filepath = os.path.join("blog", b)
        entries = parse_entries_with_lines(filepath)

        for idx, entry in enumerate(entries):
            filename = f"{b.replace('.md', '')}_{idx}"
            blame = get_entry_blame_info(
                filepath, entry["start_line"], entry["end_line"]
            )

            if blame and blame["latest"]["hash"]:
                latest = blame["latest"]
                created_year = blame["created"]["date"][:4]
            else:
                latest = {"hash": "0000000", "date": "Unknown"}
                created_year = str(y)

            if created_year not in catalog:
                catalog[created_year] = {}
            if b not in catalog[created_year]:
                catalog[created_year][b] = []

            output_md = f"dist/{filename}.md"
            output_html = f"dist/{filename}.html"

            md_content = f"**Last Modified:** `{latest['hash'][:7]}` on {latest['date']}\n\n"
            md_content += f"# {entry['title']}\n\n{entry['content']}\n\n### Revision History\n\n"

            # Historical tracking via git log -L
            history = get_entry_line_history(
                filepath, entry["start_line"], entry["end_line"]
            )
            for rev in history:
                md_content += (
                    f"<details><summary>Commit: <code>{rev['hash'][:7]}</code> | "
                    f"Date: {rev['date']}</summary>\n\n"
                    f"```diff\n{rev['patch']}\n```\n\n</details>\n"
                )

            with open(output_md, "w", encoding="utf-8") as f:
                f.write(md_content + footer)

            subprocess.run(
                [
                    "pandoc",
                    output_md,
                    "--standalone",
                    "--css=style.css",
                    "-o",
                    output_html,
                ],
                check=False,
            )

            catalog[created_year][b].append(
                {"title": entry["title"], "url": f"{filename}.html"}
            )

    # Generate yearly archive pages
    for year, files in catalog.items():
        year_md = f"# Archive {year}\n\n"
        for b, posts in files.items():
            year_md += f"\n## {b.replace('.md', '')}\n"
            for p in posts:
                year_md += f"* [{p['title']}]({p['url']})\n"

        with open(f"dist/{year}.md", "w", encoding="utf-8") as f:
            f.write(year_md + footer)

        subprocess.run(
            [
                "pandoc",
                f"dist/{year}.md",
                "--standalone",
                "--css=style.css",
                "-o",
                f"dist/{year}.html",
            ],
            check=False,
        )

    # Generate main index
    index_md = "# Blog Index\n\n" + "\n".join(
        [f"* [{yr}](./{yr}.html)" for yr in sorted(catalog.keys(), reverse=True)]
    )
    with open("dist/index.md", "w", encoding="utf-8") as f:
        f.write(index_md + footer)

    subprocess.run(
        [
            "pandoc",
            "dist/index.md",
            "--standalone",
            "--css=style.css",
            "-o",
            "dist/index.html",
        ],
        check=False,
    )


if __name__ == "__main__":
    build()
