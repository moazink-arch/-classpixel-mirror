import os
import re
import requests
from urllib.parse import urlparse

# Setup session with browser headers to avoid 403
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://classpixelgames.com/',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def download_image(url, local_path):
    """Download an image using the session with proper headers."""
    try:
        response = session.get(url, timeout=15)
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
        print(f"⚠️ Error downloading {url}: {e}")
        return False

def process_html_files(directory):
    """Find all HTML files, extract image URLs, download them, and rewrite HTML."""
    img_count = 0
    total_urls = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find ALL GameMonetize image URLs (both img src and CSS background)
                pattern = r'https://img\.gamemonetize\.com/([^\s"\'()]+\.jpg)'
                matches = re.findall(pattern, content)
                if not matches:
                    continue

                total_urls += len(matches)
                print(f"\n📄 Found {len(matches)} image URLs in {filepath}")

                # Process each unique URL (avoid duplicates)
                for match in set(matches):
                    full_url = f'https://img.gamemonetize.com/{match}'
                    # Create a safe filename by replacing slashes with underscores
                    safe_filename = match.replace('/', '_')
                    local_path = f'img/gamemonetize/{safe_filename}'

                    if download_image(full_url, local_path):
                        img_count += 1
                        # Replace all occurrences of this URL in the content
                        content = content.replace(full_url, f'/{local_path}')

                # Write the updated HTML back
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated: {filepath}")

    print(f"\n📊 Summary: Downloaded {img_count} out of {total_urls} unique images.")
    return img_count

if __name__ == '__main__':
    print("🚀 Starting image download and HTML rewrite process...")
    # Change to the site_content directory if we're not already there
    if os.path.exists('site_content'):
        os.chdir('site_content')
        print("📁 Changed to site_content directory.")
    else:
        print("⚠️ site_content directory not found! Make sure wget ran successfully.")
        exit(1)

    downloaded = process_html_files('.')
    print("✅ Process complete!")
