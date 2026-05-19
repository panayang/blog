import os
import subprocess
from datetime import datetime

def get_history(filepath):
    log = subprocess.check_output(["git", "log", "--pretty=format:%H|%ad", "--date=short", filepath]).decode('utf-8')
    history = []
    for line in log.split('\n'):
        if not line: continue
        h, d = line.split('|')
        content = subprocess.check_output(["git", "show", f"{h}:{filepath}"]).decode('utf-8')
        history.append({'hash': h, 'date': d, 'content': content})
    return history

def build():
    if not os.path.exists('dist'): os.makedirs('dist')
    
    current_year = datetime.now().year
    copyright_year = "2026" if current_year == 2026 else f"2026-{current_year}"
    footer = f"\n\n---\n<center>Copyright &copy; {copyright_year} Xinyu Yang</center>\n"

    blogs = [f for f in os.listdir('blog') if f.endswith('.md')]
    years = {}
    
    for b in blogs:
        history = get_history(os.path.join('blog', b))
        year = history[0]['date'][:4]
        if year not in years: years[year] = []
        years[year].append({'name': b, 'history': history})

    for year, posts in years.items():
        md_content = f"# Archive {year}\n\n"
        for p in posts:
            latest = p['history'][0]
            md_content += f"## {p['name']}\n**Latest Update:** {latest['date']} (`{latest['hash'][:7]}`)\n\n"
            md_content += f"{latest['content']}\n\n"
            md_content += "### History\n"
            for h in p['history'][1:]:
                md_content += f"<details><summary>Commit: {h['hash'][:7]} | Date: {h['date']}</summary>\n\n"
                md_content += f"**Updated to:**\n\n{h['content']}\n\n</details>\n"
        
        md_content += footer
        with open(f"dist/{year}.md", "w") as f: f.write(md_content)
        subprocess.run(["pandoc", f"dist/{year}.md", "--standalone", "--css=style.css", "-o", f"dist/{year}.html"])

    index_md = "# Blog Index\n\n" + "\n".join([f"- [{y}](./{y}.html)" for y in sorted(years.keys(), reverse=True)])
    index_md += footer
    with open("dist/index.md", "w") as f: f.write(index_md)
    subprocess.run(["pandoc", "dist/index.md", "--standalone", "--css=style.css", "-o", "dist/index.html"])

if __name__ == "__main__":
    build()
