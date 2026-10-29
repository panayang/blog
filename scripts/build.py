import os
import re
import subprocess
from datetime import datetime


def ensure_full_git_history():
    """Ensure the CI/CD clone has complete git history for accurate blame and log."""
    try:
        is_shallow = subprocess.check_output(
            ["git", "rev-parse", "--is-shallow-repository"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        if is_shallow == "true":
            subprocess.run(
                ["git", "fetch", "--unshallow"],
                check=False,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def get_clean_title(content):
    line = content.strip().split("\n")[0].strip()
    if line.startswith("#"):
        return line.lstrip("#").strip()
    return line[:25]


def parse_file_entries(content):
    """
    Splits content by `===` delimiter and tracks 1-based start and end line numbers.
    """
    raw_lines = content.splitlines(keepends=True)
    entries = []
    current_lines = []
    start_line = 1

    for line_idx, line in enumerate(raw_lines, start=1):
        if re.match(r"^\s*(?<!=)={3}(?!=)\s*$", line):
            text = "".join(current_lines).strip()
            if text:
                entries.append({
                    "content": text,
                    "title": get_clean_title(text),
                    "start_line": start_line,
                    "end_line": line_idx - 1,
                })
            current_lines = []
            start_line = line_idx + 1
        else:
            current_lines.append(line)

    final_text = "".join(current_lines).strip()
    if final_text:
        entries.append({
            "content": final_text,
            "title": get_clean_title(final_text),
            "start_line": start_line,
            "end_line": len(raw_lines),
        })

    return entries


def get_file_blame_map(filepath):
    """
    Runs `git blame --line-porcelain` once for the entire file.
    Returns a dictionary mapping line_number (1-indexed) -> (commit_hash, timestamp).
    """
    line_map = {}
    try:
        output = subprocess.check_output(
            ["git", "blame", "--line-porcelain", filepath],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return line_map

    current_hash = None
    current_time = 0

    for line in output.splitlines():
        if len(line) >= 40 and not line.startswith("\t") and " " in line:
            parts = line.split()
            if len(parts[0]) == 40:
                current_hash = parts[0]
        elif line.startswith("author-time "):
            current_time = int(line.split()[1])
        elif line.startswith("\t"):
            # A line starting with tab is the actual line content; signifies end of block
            line_no = len(line_map) + 1
            line_map[line_no] = {
                "hash": current_hash or "0000000",
                "time": current_time,
            }

    return line_map


def get_commit_history_for_file(filepath):
    """Fetches list of commits for the file sorted from newest to oldest."""
    try:
        log = subprocess.check_output(
            ["git", "log", "--pretty=format:%H|%ad", "--date=short", filepath],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return []

    commits = []
    for line in log.split("\n"):
        if not line.strip():
            continue
        h, d = line.split("|")
        commits.append({"hash": h, "date": d})
    return commits


def build():
    ensure_full_git_history()

    if not os.path.exists("dist"):
        os.makedirs("dist")

    y = datetime.now().year
    year_range = "2026" if y == 2026 else f"2026-{y}"
    back_to_main = "[Back to main](https://panayang.blog.apich.org)"
    footer = f"\n\n---\n<center><small>{back_to_main} | Copyright &copy; {year_range} Xinyu Yang</small></center>\n"

    if not os.path.exists("blog"):
        return

    blogs = sorted([f for f in os.listdir("blog") if f.endswith(".md")])
    catalog = {}

    for b in blogs:
        filepath = os.path.join("blog", b)

        # Read current content
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                current_raw = f.read()
        except IOError:
            continue

        entries = parse_file_entries(current_raw)
        blame_map = get_file_blame_map(filepath)
        file_commits = get_commit_history_for_file(filepath)

        # Fallback timestamp from file if git blame yields nothing
        fallback_date = file_commits[0]["date"] if file_commits else str(y)
        fallback_hash = file_commits[0]["hash"] if file_commits else "HEAD"

        for idx, entry in enumerate(entries):
            filename = f"{b.replace('.md', '')}_{idx}"

            # Calculate exact last-modified and creation time within entry lines
            latest_ts = 0
            latest_hash = fallback_hash
            oldest_ts = float("inf")
            oldest_hash = fallback_hash

            for l_num in range(entry["start_line"], entry["end_line"] + 1):
                info = blame_map.get(l_num)
                if info and info["time"] > 0:
                    if info["time"] > latest_ts:
                        latest_ts = info["time"]
                        latest_hash = info["hash"]
                    if info["time"] < oldest_ts:
                        oldest_ts = info["time"]
                        oldest_hash = info["hash"]

            latest_date = (
                datetime.fromtimestamp(latest_ts).strftime("%Y-%m-%d")
                if latest_ts > 0
                else fallback_date
            )
            created_year = (
                datetime.fromtimestamp(oldest_ts).strftime("%Y")
                if oldest_ts != float("inf")
                else fallback_date[:4]
            )

            if created_year not in catalog:
                catalog[created_year] = {}
            if b not in catalog[created_year]:
                catalog[created_year][b] = []

            output_md = f"dist/{filename}.md"
            output_html = f"dist/{filename}.html"

            md_content = f"**Last Modified:** `{latest_hash[:7]}` on {latest_date}\n\n"
            md_content += f"# {entry['title']}\n\n{entry['content']}\n\n### History\n"

            # Match revisions across past commits using title matching
            # (Solves index shifting without relying on fragile line tracking)
            last_recorded_content = None
            for c in file_commits:
                try:
                    c_content = subprocess.check_output(
                        ["git", "show", f"{c['hash']}:{filepath}"],
                        stderr=subprocess.DEVNULL,
                    ).decode("utf-8", errors="replace")
                except subprocess.CalledProcessError:
                    continue

                past_entries = parse_file_entries(c_content)
                matched_past = None

                # 1. Match by exact title
                for pe in past_entries:
                    if pe["title"] == entry["title"]:
                        matched_past = pe["content"]
                        break

                # 2. Fallback to index if title was changed or empty
                if not matched_past and idx < len(past_entries):
                    matched_past = past_entries[idx]["content"]

                if matched_past and matched_past != last_recorded_content:
                    md_content += (
                        f"<details><summary>Commit: {c['hash'][:7]} | Date: {c['date']}</summary>\n\n"
                        f"{matched_past}\n\n</details>\n"
                    )
                    last_recorded_content = matched_past

            with open(output_md, "w", encoding="utf-8") as f:
                f.write(md_content + footer)

            subprocess.run(
                ["pandoc", output_md, "--standalone", "--css=style.css", "-o", output_html],
                check=False,
            )

            catalog[created_year][b].append({
                "title": entry["title"],
                "url": f"{filename}.html",
            })

    # Yearly archive files
    for year, files in catalog.items():
        year_md = f"# Archive {year}\n\n"
        for b, posts in files.items():
            year_md += f"\n## {b.replace('.md', '')}\n"
            for p in posts:
                year_md += f"* [{p['title']}]({p['url']})\n"

        with open(f"dist/{year}.md", "w", encoding="utf-8") as f:
            f.write(year_md + footer)

        subprocess.run(
            ["pandoc", f"dist/{year}.md", "--standalone", "--css=style.css", "-o", f"dist/{year}.html"],
            check=False,
        )

    # Index page
    index_md = "# Blog Index\n\n" + "\n".join(
        [f"* [{yr}](./{yr}.html)" for yr in sorted(catalog.keys(), reverse=True)]
    )
    with open("dist/index.md", "w", encoding="utf-8") as f:
        f.write(index_md + footer)

    subprocess.run(
        ["pandoc", "dist/index.md", "--standalone", "--css=style.css", "-o", "dist/index.html"],
        check=False,
    )


if __name__ == "__main__":
    build()
