import os
import subprocess
from datetime import datetime

def get_blog_entries(filepath):
    content = subprocess.check_output(["git", "show", f"HEAD:{filepath}"]).decode('utf-8')
    entries = content.split('===')
    log = subprocess.check_output(["git", "log", "--pretty=format:%H|%ad", "--date=short", filepath]).decode('utf-8')
    
    commits = []
    for line in log.split('\n'):
        if not line: continue
        h, d = line.split('|')
        commits.append({'hash': h, 'date': d})
    
    result = []
    for idx, entry_content in enumerate(entries):
        if not entry_content.strip(): continue
        title = entry_content.strip().split('\n')[0].replace('#', '').strip()
        filename = f"{os.path.basename(filepath).replace('.md', '')}_{idx}"
        result.append({'title': title, 'content': entry_content, 'filename': filename, 'commits': commits})
    return result

def build():
    if not os.path.exists('dist'): os.makedirs('dist')
    
    current_year = datetime.now().year
    copyright_year = "2026" if current_year == 2026 else f"2026-{current_year}"
    footer = f"\n\n---\n<center>Copyright &copy; {copyright_year} Xinyu Yang</center>\n"

    blogs = [f for f in os.listdir('blog') if f.endswith('.md')]
    catalog = {}

    for b in blogs:
        entries = get_blog_entries(os.path.join('blog', b))
        for entry in entries:
            year = entry['commits'][0]['date'][:4]
            if year not in catalog: catalog[year] = {}
            if b not in catalog[year]: catalog[year][b] = []
            
            output_md = f"dist/{entry['filename']}.md"
            md_content = f"# {entry['title']}\n\n{entry['content']}\n\n### History\n"
            for h in entry['commits']:
                h_content = subprocess.check_output(["git", "show", f"{h['hash']}:{os.path.join('blog', b)}"]).decode('utf-8')
                es = h_content.split('===')
                idx = int(entry['filename'].split('_')[-1])
                if idx < len(es):
                    md_content += f"<details><summary>Commit: {h['hash'][:7]} | Date: {h['date']}</summary>\n\n{es[idx]}\n\n</details>\n"
            
            md_content += footer
            with open(output_md, "w") as f: f.write(md_content)
            subprocess.run(["pandoc", output_md, "--standalone", "--css=style.css", "-o", output_md.replace('.md', '.html')])
            catalog[year][b].append({'title': entry['title'], 'url': f"{entry['filename']}.html"})

    for year, files in catalog.items():
        year_md = f"# Archive {year}\n\n"
        for b, posts in files.items():
            year_md += f"## {b.replace('.md', '')}\n"
            for p in posts:
                year_md += f"- [{p['title']}]({p['url']})\n"
        year_md += footer
        with open(f"dist/{year}.md", "w") as f: f.write(year_md)
        subprocess.run(["pandoc", f"dist/{year}.md", "--standalone", "--css=style.css", "-o", f"dist/{year}.html"])

    index_md = "# Blog Index\n\n" + "\n".join([f"- [{y}](./{y}.html)" for y in sorted(catalog.keys(), reverse=True)])
    index_md += footer
    with open("dist/index.md", "w") as f: f.write(index_md)
    subprocess.run(["pandoc", "dist/index.md", "--standalone", "--css=style.css", "-o", "dist/index.html"])

if __name__ == "__main__":
    build()