import os
import subprocess
from datetime import datetime

def get_clean_title(content):
    line = content.strip().split('\n')[0].strip()
    if line.startswith('#'):
        return line.lstrip('#').strip()
    return line[:15]

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
        title = get_clean_title(entry_content)
        filename = f"{os.path.basename(filepath).replace('.md', '')}_{idx}"
        result.append({'title': title, 'content': entry_content, 'filename': filename, 'commits': commits})
    return result

def build():
    if not os.path.exists('dist'): os.makedirs('dist')
    
    y = datetime.now().year
    year_range = "2026" if y == 2026 else f"2026-{y}"
    footer = f"\n\n---\n<center><small>Copyright &copy; {year_range} Xinyu Yang</small></center>\n"

    blogs = [f for f in os.listdir('blog') if f.endswith('.md')]
    catalog = {}

    for b in blogs:
        entries = get_blog_entries(os.path.join('blog', b))
        for entry in entries:
            year = entry['commits'][0]['date'][:4]
            if year not in catalog: catalog[year] = {}
            if b not in catalog[year]: catalog[year][b] = []
            
            output_md = f"dist/{entry['filename']}.md"
            latest = entry['commits'][0]
            
            md_content = f"**Last Modified:** `{latest['hash'][:7]}` on {latest['date']}\n\n"
            md_content += f"# {entry['title']}\n\n{entry['content']}\n\n### History\n"
            
            last_content = None
            idx = int(entry['filename'].split('_')[-1])
            
            for h in entry['commits']:
                h_content = subprocess.check_output(["git", "show", f"{h['hash']}:{os.path.join('blog', b)}"]).decode('utf-8')
                es = h_content.split('===')
                if idx < len(es):
                    current_entry_content = es[idx].strip()
                    if current_entry_content != last_content:
                        md_content += f"<details><summary>Commit: {h['hash'][:7]} | Date: {h['date']}</summary>\n\n{current_entry_content}\n\n</details>\n"
                        last_content = current_entry_content
            
            with open(output_md, "w", encoding='utf-8') as f: f.write(md_content + footer)
            subprocess.run(["pandoc", output_md, "--standalone", "--css=style.css", "-o", output_md.replace('.md', '.html')])
            catalog[year][b].append({'title': entry['title'], 'url': f"{entry['filename']}.html"})

    for year, files in catalog.items():
        year_md = f"# Archive {year}\n\n"
        for b, posts in files.items():
            year_md += f"## {b.replace('.md', '')}\n"
            for p in posts:
                year_md += f"* [{p['title']}]({p['url']})\n"
        with open(f"dist/{year}.md", "w", encoding='utf-8') as f: f.write(year_md + footer)
        subprocess.run(["pandoc", f"dist/{year}.md", "--standalone", "--css=style.css", "-o", f"dist/{year}.html"])

    index_md = "# Blog Index\n\n" + "\n".join([f"* [{y}](./{y}.html)" for y in sorted(catalog.keys(), reverse=True)])
    with open("dist/index.md", "w", encoding='utf-8') as f: f.write(index_md + footer)
    subprocess.run(["pandoc", "dist/index.md", "--standalone", "--css=style.css", "-o", "dist/index.html"])

if __name__ == "__main__":
    build()
