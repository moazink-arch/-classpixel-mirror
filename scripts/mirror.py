import os
import re
import requests

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

def rewrite_js_urls(content):
    """Find and replace image URLs inside JavaScript blocks (like the GAMES array)."""
    # Pattern to find thumb: "https://img.gamemonetize.com/...jpg"
    pattern = r'thumb:"https://img\.gamemonetize\.com/([^"]+\.jpg)"'
    matches = re.findall(pattern, content)
    if matches:
        print(f"Found {len(matches)} JavaScript image URLs to rewrite.")
        for match in matches:
            # The match is like "someid/512x384.jpg" or "someid/512x384.jpg?something"
            # We need to replace / with _ to match the downloaded filenames
            safe_filename = match.replace('/', '_')
            local_path = f'/img/gamemonetize/{safe_filename}'
            full_url = f'https://img.gamemonetize.com/{match}'
            content = content.replace(f'thumb:"{full_url}"', f'thumb:"{local_path}"')
    return content

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

                # Find ALL GameMonetize URLs (from HTML attributes)
                pattern = r'https://img\.gamemonetize\.com/([^\s"\'()<>]+\.jpg)'
                matches = re.findall(pattern, content)
                
                pattern2 = r'https://img\.gamemonetize\.com/([^\s"\'()<>]+\.jpg\?[^\s"\'()<>]*)'
                matches2 = re.findall(pattern2, content)
                
                all_matches = list(set(matches + matches2))

                # If we find HTML image URLs, download and rewrite
                if all_matches:
                    total_urls += len(all_matches)
                    print(f"\n📸 Found {len(all_matches)} image URLs in {filepath}")

                    for match in all_matches:
                        clean_match = match.split('?')[0] if '?' in match else match
                        full_url = f'https://img.gamemonetize.com/{match}'
                        safe_filename = clean_match.replace('/', '_')
                        local_path = f'img/gamemonetize/{safe_filename}'

                        if download_image(full_url, local_path):
                            img_count += 1
                            content = content.replace(full_url, f'/{local_path}')
                            if '?' in match:
                                clean_url = f'https://img.gamemonetize.com/{clean_match}'
                                content = content.replace(clean_url, f'/{local_path}')

                # NEW: Also rewrite JavaScript thumb URLs
                content = rewrite_js_urls(content)

                # Write the updated HTML back if any changes were made
                if all_matches or 'thumb:"' in content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Updated: {filepath}")

    print(f"\n📊 Summary: Downloaded {img_count} out of {total_urls} unique images.")
    return img_count

if __name__ == '__main__':
    print("🚀 Starting image download and HTML rewrite process...")
    if os.path.exists('site_content'):
        os.chdir('site_content')
        print("📁 Changed to site_content directory.")
    else:
        print("⚠️ site_content directory not found!")
        exit(1)

    os.makedirs('img/gamemonetize', exist_ok=True)
    downloaded = process_html_files('.')
    print("✅ Process complete!")
