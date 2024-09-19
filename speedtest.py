import requests
import time
import re
import sys

# URLs for the two files in their repositories
url_0 = 'https://iptv-org.github.io/iptv/index.m3u'
url_00 = 'https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u'
#url_list =['https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u']

# Threshold in KB/s. URLs slower than this will be removed.
SPEED_THRESHOLD_KBPS = 100  # Example: 100 KB/s

def is_url_ipv6(url):
    # Check if the URL contains an IPv6 address by looking for square brackets
    return bool(re.search(r'\[.*?\]', url))
    
# Function to process and modify the #EXTINF metadata
def modify_extinf(extinf_line, index):
    # Change the tvg-id to 's' + index and the group-title to 'general'
    modified_line = re.sub(r'tvg-id="[^"]+"', f'tvg-id="s{index}"', extinf_line)
    #modified_line = re.sub(r'group-title="[^"]+"', 'group-title="general"', modified_line)
    return modified_line

# Function to fetch the content of an .m3u file
def fetch_m3u_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch {url}")
        return None

def is_valid_media_type(response):
    content_type = response.headers.get('Content-Type', '')
    if "video" in content_type or "application" in content_type:
        return True
    return False

# Function to check if the URL's speed is above the threshold
def is_url_speed_acceptable(url):
    # Comment out the IPv6 check if you don't want to use it
    if is_url_ipv6(url):
        print(f"Skipping IPv6 URL: {url}")
        return False
    
    #test_duration=10
    try:
        # Make a GET request and fetch a small chunk of the file
        response = requests.get(url, stream=True, timeout=15)
        
        # If the request is not successful, return False
        if response.status_code != 200:
            return False

        if not is_valid_media_type(response):
            print(f"Invalid media type: {response.headers.get('Content-Type')}")
            return False

        # Start measuring time
        start_time = time.time()
        # Read a small chunk (e.g., 1024 bytes)
        chunk_size = 1024*500
        chunk=next(response.iter_content(chunk_size=chunk_size), None)

        # End measuring time
        end_time = time.time()

        # If no chunk is received, return False
        if chunk is None:
            return False

        # Calculate download speed (KB/s)
        download_time = end_time - start_time
        speed_kbps = (len(chunk) / 1024) / download_time

        print(f"URL: {url} | Speed: {speed_kbps:.2f} KB/s")

        # Return True if speed is above threshold, False otherwise
        return speed_kbps >= SPEED_THRESHOLD_KBPS

    except requests.RequestException:
        return False

# Function to extract and validate URLs and #EXTINF lines from the .m3u content
def process_m3u(content):
    lines = content.readlines()
    valid_lines = []
    index=0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        try:
          # Check if it's an #EXTINF line, and the next line is the URL
          if line.startswith('#EXTINF') and (i + 1) < len(lines):
            extinf_line = line  # Store the #EXTINF line
            url_line = lines[i + 1]  # Store the URL line
            if url_line.startswith('http'):
               if(is_url_speed_acceptable(url_line)):
                    # Add both the #EXTINF and the URL if speed is acceptable
                    index+=1
                    modified_extinf = modify_extinf(extinf_line, index)
                    valid_lines.append(extinf_line)
                    valid_lines.append(url_line)
               else:
                    print(f"failed stream: {url_line}")
               i += 2  # Skip to the next pair (#EXTINF and URL)
          else:
            # Add non-#EXTINF lines (if there are any) such as comments
            if line.startswith('#EXTM3U'):
               valid_lines.append(line)
            i += 1

        except Exception as e:
            i+=2
            continue
            
    return "".join(valid_lines)

file1=sys.argv[1]
with open(file1,'r') as files:
    # Iterate over each URL, fetch and process content
      processed_content = process_m3u(files)  # Process content

with open('testnew.m3u','w+') as f:
     f.write(processed_content)
