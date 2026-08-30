import os
import re
import requests

# Browser-like session to avoid 403s
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://classpixelgames.com/',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def download_image(url, local_path):
    """Download an image. Returns True on success."""
    try:
        # Skip if already present and non-empty
        if os.path.isfile(local_path) and os.path.getsize(local_path) > 0:
            print(f"⏭️  Already exists: {local_path}")
            return True

        response = session.get(url, timeout=20)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {url}")
            return True
        else:
            print(f"❌ Failed: {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"⚠️  Error downloading {url}: {e}")
        return False

def collect_all_image_urls(content):
    """
    Find every GameMonetize image URL in the file:
    - HTML attributes (src, style, etc.)
    - JavaScript thumb: "..." values inside the GAMES array
    """
    urls = set()

    # 1. Any full https://img.gamemonetize.com/...jpg (with optional query)
    general = re.findall(
        r'https://img\.gamemonetize\.com/[^\s"\'()<>]+\.jpg(?:\?[^\s"\'()<>]*)?',
        content
    )
    urls.update(general)

    # 2. Explicitly capture thumb:"https://..." (covers JS GAMES array)
    thumbs = re.findall(
        r'thumb\s*:\s*"https://img\.gamemonetize\.com/([^"]+\.jpg)"',
        content
    )
    for path in thumbs:
        urls.add(f'https://img.gamemonetize.com/{path}')

    return urls

def to_local_path(remote_url):
    """
    Convert remote URL to the local path convention used by the mirror.
    Example:
      https://img.gamemonetize.com/abc123/512x384.jpg
      → img/gamemonetize/abc123_512x384.jpg
    """
    # Strip query string if present
    clean = remote_url.split('?')[0]
    # Extract the part after the domain
    path = clean.replace('https://img.gamemonetize.com/', '')
    # Replace / with _ for the filename
    safe_name = path.replace('/', '_')
    return f'img/gamemonetize/{safe_name}'

def rewrite_content(content, url_map):
    """
    Replace every remote URL with its local counterpart.
    Handles both plain HTML attributes and thumb:"..." JS strings.
    """
    for remote, local in url_map.items():
        # Leading slash version used in the mirror
        local_with_slash = f'/{local}'

        # 1. Replace full URL anywhere (HTML attributes, etc.)
        content = content.replace(remote, local_with_slash)

        # 2. Explicitly handle the JS form: thumb:"https://..."
        #    (in case the previous replace didn't catch a slightly different form)
        content = content.replace(
            f'thumb:"{remote}"',
            f'thumb:"{local_with_slash}"'
        )
        # Also tolerate optional spaces around the colon
        content = re.sub(
            rf'thumb\s*:\s*"{re.escape(remote)}"',
            f'thumb:"{local_with_slash}"',
            content
        )

    return content

def process_html_files(directory):
    """Walk all HTML files, download missing images, rewrite URLs."""
    img_downloaded = 0
    total_unique = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith('.html'):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Collect every image URL that needs attention
            remote_urls = collect_all_image_urls(content)
            if not remote_urls:
                continue

            total_unique += len(remote_urls)
            print(f"\n📸 {filepath}: {len(remote_urls)} unique image URL(s)")

            # Build remote → local map and download
            url_map = {}
            for remote in remote_urls:
                local = to_local_path(remote)
                url_map[remote] = local

                if download_image(remote, local):
                    img_downloaded += 1

            # Rewrite the HTML/JS content
            new_content = rewrite_content(content, url_map)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Updated: {filepath}")
            else:
                print(f"ℹ️  No changes needed: {filepath}")

    print(f"\n📊 Summary: successfully downloaded {img_downloaded} images "
          f"(processed {total_unique} unique URLs).")
    return img_downloaded

if __name__ == '__main__':
    print("🚀 Starting image download + HTML/JS rewrite…")

    if os.path.exists('site_content'):
        os.chdir('site_content')
        print("📁 Working inside site_content/")
    else:
        print("⚠️  site_content directory not found – aborting.")
        exit(1)

    os.makedirs('img/gamemonetize', exist_ok=True)
    process_html_files('.')
    print("✅ Mirror process complete.")
