#!/bin/env python3
import os
import platform
import requests
import subprocess
import threading
import socket
import time
import re
from argparse import ArgumentParser

def start_bee_node(bee_path, stop_flag):
    """Starts the Bee node in a separate thread."""

    command = [bee_path, "start", "--swap-enable=false", "--full-node=false", "--blockchain-rpc-endpoint=", "--password=beeget"]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while not stop_flag.is_set():
        # Simulate some work the Bee node might do (replace with actual Bee logic)
        time.sleep(0)

    # Bee node should terminate when stop_flag is set
    process.terminate()
    process.wait()  # Wait for the process to fully exit

def download_latest_bee():
    """Downloads the latest Bee binary for the current architecture from the releases page.

    Saves the downloaded file to the user's ~/.local/bin directory.

    Raises:
        RuntimeError: If the download fails or the architecture is not supported.
    """

    url = "https://api.github.com/repos/ethersphere/bee/releases/latest"
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download latest Bee release: {e}")

    data = response.json()
    assets = data.get('assets', [])

    # Determine OS and architecture
    os_name = platform.system().lower()
    arch = platform.machine()  # Get machine architecture
  
    # Define filename based on OS and architecture
    filename_map = {
        ('linux', 'x86_64'): 'bee-linux-amd64',
        ('linux', 'arm64'): 'bee-linux-arm64',
        ('darwin', 'x86_64'): 'bee-darwin-amd64',  # macOS
        ('darwin', 'arm64'): 'bee-darwin-arm64',  # macOS
        ('windows', 'x86_64'): 'bee-windows-amd64.exe',  # Windows executable
    }
  
    download_url = None
    for asset in assets:
        if asset['name'] == filename_map.get((os_name, arch)):
            download_url = asset['browser_download_url']
            break
  
    if not download_url:
        raise RuntimeError(f"Bee binary not found for architecture: {os_name}-{arch}")
  
    # Determine download directory based on OS
    download_dir = None
    if os_name == 'windows':
        download_dir = os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Local'))
    else:
        download_dir = os.path.join(os.path.expanduser('~'), '.local', 'bin')  # Common location for Linux/macOS
  
    # Create download directory if it doesn't exist
    if download_dir and not os.path.exists(download_dir):
        os.makedirs(download_dir)
  
    # Construct download path
    download_path = os.path.join(download_dir, os.path.basename(download_url))


    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Create the .local/bin directory if it doesn't exist
        os.makedirs(os.path.dirname(download_path), exist_ok=True)  # Create parent directories if needed

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download Bee binary: {e}")
    except OSError as e:  # Handle potential OS errors during directory creation
        raise RuntimeError(f"Failed to create directory structure: {e}")

    # Make downloaded binary executable (if necessary)
    if os.name == 'posix':
        os.chmod(download_path, 0o755)  # Grant execute permissions

    return download_path

def query_bee_api(swarmhash):
    """Downloads the latest Bee binary, starts the Bee node, and queries the Bee API using the provided swarmhash.

    Args:
        swarmhash (str): The swarmhash to query.

    Raises:
        RuntimeError: If the download fails, the architecture is not supported,
                       or the Bee API call fails.
    """

    bee_path = download_latest_bee()  # Download Bee if not already present

    if not os.path.exists(bee_path):
        raise RuntimeError("Bee binary not found. Please ensure it's downloaded or installed.")

    stop_flag = threading.Event()  # Create an event object

    # Start Bee node in a separate thread
    bee_thread = threading.Thread(target=start_bee_node, args=(bee_path, stop_flag))
    bee_thread.daemon = True  # Set as daemon thread
    bee_thread.start()

    # Construct the Bee API URL with swarmhash
    bee_url = f"http://localhost:1633/bzz/{swarmhash}"

    # Wait for Bee to be reachable on port 1633 (with timeout)
    max_retries = 30
    retry_count = 0
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # Set a 1-second timeout for connect
            sock.connect(("localhost", 1633))
            break  # Success, connected to the Bee node
        except (socket.timeout, ConnectionRefusedError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise RuntimeError(f"Bee node failed to start after {max_retries} retries.")
            time.sleep(1)  # Wait a second before retrying

    try:
        response = requests.get(bee_url, stream=True)
        response.raise_for_status()  # Raise exception for non-200 status codes

        # Extract filename from Content-Disposition header (if available)
        content_disposition = response.headers.get("Content-Disposition")
        filename = None
        if content_disposition:
            # Use regular expression or parsing to extract filename
            match = re.search(r'filename="(.*?)"', content_disposition)
            if match:
                filename = match.group(1)

        # Fallback filename if not found in header
        if not filename:
            filename = f"downloaded_file_{swarmhash}.dat"

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"Downloaded file: {filename}")

        # Signal the Bee node to stop after download
        stop_flag.set()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download file using Bee API: {e}")


    # Signal the Bee node to stop after download
    stop_flag.set()

    # Wait for the Bee thread to finish (with timeout)
    bee_process = bee_thread.join(timeout=1)  # Wait for the thread to finish (with timeout)
    if bee_process is not None:
        # Terminate if still running after timeout
        bee_process.terminate()

if __name__ == "__main__":
    parser = ArgumentParser(description="Download file from Bee node using swarmhash.")
    parser.add_argument("swarmhash", help="The swarmhash of the file to download.")
    args = parser.parse_args()

    try:
        query_bee_api(args.swarmhash)
    except RuntimeError as e:
        print(f"Error: {e}")
