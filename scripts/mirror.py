import os
import re
import requests

def download_image(url, local_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {url}")
            return True
        else:
            print(f"Failed: {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def process_html_files(directory):
    img_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                pattern = r'https://img\.gamemonetize\.com/([^"\')]+\.jpg)'
                matches = re.findall(pattern, content)
                if matches:
                    print(f"Found {len(matches)} images in {filepath}")
                    for match in matches:
                        full_url = f'https://img.gamemonetize.com/{match}'
                        safe_filename = match.replace('/', '_')
                        local_path = f'img/gamemonetize/{safe_filename}'
                        if download_image(full_url, local_path):
                            img_count += 1
                            content = content.replace(full_url, f'/{local_path}')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated: {filepath}")
    print(f"Total images downloaded: {img_count}")

if __name__ == '__main__':
    print("Starting mirror process...")
    process_html_files('site_content')
    print("Done!")
