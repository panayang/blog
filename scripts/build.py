import os
import re
import subprocess
from datetime import datetime


def ensure_full_git_history():
    """Ensure the CI/CD clone has complete git history for accurate blame and log."""
    try:
        is_shallow = (
            subprocess.check_output(
                ["git", "rev-parse", "--is-shallow-repository"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
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
    return line[:30]


def parse_file_entries(content):
    """Splits content by `===` delimiter and tracks exact line ranges (1-indexed)."""
    raw_lines = content.splitlines(keepends=True)
    entries = []
    current_lines = []
    start_line = 1

    for line_idx, line in enumerate(raw_lines, start=1):
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
                "end_line": len(raw_lines),
            }
        )

    return entries


def get_file_blame_map(filepath):
    """Robust porcelain parser mapping 1-based line number to commit hash and author-timestamp."""
    line_map = {}
    try:
        output = subprocess.check_output(
            ["git", "blame", "--line-porcelain", filepath],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return line_map

    current_hash = None
    current_final_line = None
    commit_timestamps = {}

    for line in output.splitlines():
        # Blame header format: <hash> <orig_line> <final_line> [<group_lines>]
        match = re.match(r"^([0-9a-f]{40})\s+\d+\s+(\d+)", line)
        if match:
            current_hash = match.group(1)
            current_final_line = int(match.group(2))
        elif line.startswith("author-time "):
            commit_timestamps[current_hash] = int(line.split()[1])
        elif line.startswith("\t"):
            if current_final_line is not None:
                line_map[current_final_line] = {
                    "hash": current_hash,
                    "time": commit_timestamps.get(current_hash, 0),
                }

    return line_map


def get_commit_history_for_file(filepath):
    """Fetches full commit history for the file ordered newest to oldest."""
    try:
        log = subprocess.check_output(
            [
                "git",
                "log",
                "--pretty=format:%H|%ad",
                "--date=short",
                "--",
                filepath,
            ],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return []

    commits = []
    for line in log.splitlines():
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

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                current_raw = f.read()
        except IOError:
            continue

        entries = parse_file_entries(current_raw)
        blame_map = get_file_blame_map(filepath)
        file_commits = get_commit_history_for_file(filepath)

        commit_date_map = {c["hash"]: c["date"] for c in file_commits}
        fallback_date = file_commits[0]["date"] if file_commits else str(y)
        fallback_hash = file_commits[0]["hash"] if file_commits else "HEAD"

        for idx, entry in enumerate(entries):
            filename = f"{b.replace('.md', '')}_{idx}"

            # Collect only commits that directly touched lines of this entry
            entry_commits = set()
            latest_ts = 0
            latest_hash = fallback_hash
            oldest_ts = float("inf")
            oldest_hash = fallback_hash

            for l_num in range(entry["start_line"], entry["end_line"] + 1):
                info = blame_map.get(l_num)
                if info and info["time"] > 0:
                    entry_commits.add(info["hash"])
                    if info["time"] > latest_ts:
                        latest_ts = info["time"]
                        latest_hash = info["hash"]
                    if info["time"] < oldest_ts:
                        oldest_ts = info["time"]
                        oldest_hash = info["hash"]

            latest_date = (
                commit_date_map.get(latest_hash)
                or (
                    datetime.fromtimestamp(latest_ts).strftime("%Y-%m-%d")
                    if latest_ts > 0
                    else fallback_date
                )
            )
            created_year = (
                commit_date_map.get(oldest_hash, "")[:4]
                or (
                    datetime.fromtimestamp(oldest_ts).strftime("%Y")
                    if oldest_ts != float("inf")
                    else fallback_date[:4]
                )
            )

            if created_year not in catalog:
                catalog[created_year] = {}
            if b not in catalog[created_year]:
                catalog[created_year][b] = []

            output_md = f"dist/{filename}.md"
            output_html = f"dist/{filename}.html"

            # 1. Fix duplicated title:
            # If entry['content'] already starts with a Markdown header '#', do not prepend '# {entry['title']}'
            body_content = entry["content"]
            if body_content.startswith("#"):
                header_section = f"{body_content}\n\n"
            else:
                header_section = f"# {entry['title']}\n\n{body_content}\n\n"

            md_content = f"**Last Modified:** `{latest_hash[:7]}` on {latest_date}\n\n{header_section}### History\n\n"

            # 2. Fix false commits in History:
            # Only consider commits that altered the file, seed current content as baseline,
            # and report earlier versions when the content changed.
            history_blocks = []
            running_content = entry["content"]

            for c in file_commits:
                # Skip checking commits that occurred after the entry's latest modification
                if (
                    latest_ts > 0
                    and c["hash"] not in entry_commits
                    and c["hash"] == file_commits[0]["hash"]
                ):
                    continue

                try:
                    c_content = subprocess.check_output(
                        ["git", "show", f"{c['hash']}:{filepath}"],
                        stderr=subprocess.DEVNULL,
                    ).decode("utf-8", errors="replace")
                except subprocess.CalledProcessError:
                    continue

                past_entries = parse_file_entries(c_content)
                matched_past = None

                for pe in past_entries:
                    if pe["title"] == entry["title"]:
                        matched_past = pe["content"]
                        break

                if not matched_past and idx < len(past_entries):
                    matched_past = past_entries[idx]["content"]

                # If this past commit contains a previous version different from running_content
                if matched_past and matched_past != running_content:
                    history_blocks.append(
                        f"<details><summary>Commit: <code>{c['hash'][:7]}</code> | "
                        f"Date: {c['date']}</summary>\n\n{matched_past}\n\n</details>\n"
                    )
                    running_content = matched_past

            if history_blocks:
                md_content += "".join(history_blocks)
            else:
                md_content += f"*First recorded in commit `{oldest_hash[:7]}` on {commit_date_map.get(oldest_hash, latest_date)}.*\n"

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

    # Yearly archive pages
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

    # Blog index
    index_md = "# Blog Index\n\n" + "\n".join(
        [
            f"* [{yr}](./{yr}.html)"
            for yr in sorted(catalog.keys(), reverse=True)
        ]
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
