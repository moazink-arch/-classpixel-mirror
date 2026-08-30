import os
import re
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://classpixelgames.com/',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def download_image(url, local_path):
    try:
        if os.path.isfile(local_path) and os.path.getsize(local_path) > 0:
            print(f"⏭️  Already exists: {local_path}")
            return True
        r = session.get(url, timeout=20)
        if r.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(r.content)
            print(f"✅ Downloaded: {url}")
            return True
        print(f"❌ Failed: {url} ({r.status_code})")
        return False
    except Exception as e:
        print(f"⚠️  Error {url}: {e}")
        return False

def collect_all_image_urls(content):
    urls = set()
    # Any full GameMonetize URL
    for m in re.findall(r'https://img\.gamemonetize\.com/[^\s"\'()<>]+\.jpg(?:\?[^\s"\'()<>]*)?', content):
        urls.add(m)
    # Explicit thumb: "..." values (GAMES array)
    for path in re.findall(r'thumb\s*:\s*"https://img\.gamemonetize\.com/([^"]+\.jpg)"', content):
        urls.add(f'https://img.gamemonetize.com/{path}')
    return urls

def to_local_path(remote_url):
    clean = remote_url.split('?')[0]
    path = clean.replace('https://img.gamemonetize.com/', '')
    return f'img/gamemonetize/{path.replace("/", "_")}'

def rewrite_content(content, url_map):
    for remote, local in url_map.items():
        local_slash = f'/{local}'
        content = content.replace(remote, local_slash)
        # JS form
        content = re.sub(
            rf'thumb\s*:\s*"{re.escape(remote)}"',
            f'thumb:"{local_slash}"',
            content
        )
    return content

def fix_wget_corruption(content):
    """
    wget --adjust-extension corrupts the template to:
        url('${g.thumb}.html')
    Restore the correct form.
    """
    content = content.replace("${g.thumb}.html", "${g.thumb}")
    content = content.replace("${g.thumb}.HTML", "${g.thumb}")
    # Also catch any other accidental .html appended to image paths inside url()
    content = re.sub(
        r"url\('(/img/gamemonetize/[^']+\.jpg)\.html'\)",
        r"url('\1')",
        content
    )
    return content

def process_html_files(directory):
    downloaded = 0
    total = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(('.html', '.htm')):
                continue
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 1. Fix the wget .html corruption first
            content = fix_wget_corruption(content)

            # 2. Collect & download images
            remote_urls = collect_all_image_urls(content)
            if not remote_urls and "${g.thumb}" not in content:
                # Still write if we fixed corruption
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                continue

            total += len(remote_urls)
            print(f"\n📸 {filepath}: {len(remote_urls)} image URL(s)")

            url_map = {}
            for remote in remote_urls:
                local = to_local_path(remote)
                url_map[remote] = local
                if download_image(remote, local):
                    downloaded += 1

            # 3. Rewrite remote → local
            new_content = rewrite_content(content, url_map)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated: {filepath}")

    print(f"\n📊 Downloaded {downloaded} / {total} unique images.")
    return downloaded

if __name__ == '__main__':
    print("🚀 Mirror: download images + fix JS + rewrite URLs")
    if not os.path.exists('site_content'):
        print("⚠️  site_content/ not found")
        exit(1)
    os.chdir('site_content')
    os.makedirs('img/gamemonetize', exist_ok=True)
    process_html_files('.')
    print("✅ Done.")
