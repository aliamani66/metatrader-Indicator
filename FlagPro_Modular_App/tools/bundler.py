import os
import re

def bundle():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_file = os.path.join(base_dir, "index.html")
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    out_file = os.path.join(dist_dir, "FlagPro_Modular_App.html")

    print(f"Bundling FlagPro Modular App from: {base_dir}")
    
    template_file = os.path.join(base_dir, "template.html")
    if os.path.exists(template_file):
        with open(template_file, "r", encoding="utf-8") as f:
            html = f.read()

        def replace_include(match):
            comp_rel = match.group(1).strip()
            comp_path = os.path.join(base_dir, comp_rel)
            if os.path.exists(comp_path):
                with open(comp_path, "r", encoding="utf-8") as cf:
                    return cf.read()
            return match.group(0)

        html = re.sub(r'<!--\s*include:\s*([^\s]+)\s*-->', replace_include, html)
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)
    else:
        with open(index_file, "r", encoding="utf-8") as f:
            html = f.read()

    # 1. Inline CSS
    def replace_css(match):
        css_href = match.group(1)
        css_path = os.path.join(base_dir, css_href)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as cf:
                css_content = cf.read()
            return f"<style>\n{css_content}\n</style>"
        return match.group(0)

    html = re.sub(r'<link\s+rel="stylesheet"\s+href="([^"]+)">', replace_css, html)

    # 2. Inline JavaScript
    def replace_js(match):
        js_src = match.group(1)
        js_path = os.path.join(base_dir, js_src)
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as jf:
                js_content = jf.read()
            return f"<script>\n{js_content}\n</script>"
        return match.group(0)

    html = re.sub(r'<script\s+src="([^"]+)"></script>', replace_js, html)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"Successfully created bundled distribution: {out_file} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    bundle()
