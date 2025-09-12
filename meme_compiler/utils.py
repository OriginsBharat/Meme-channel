import requests
import os
import logging
from urllib.parse import urlparse

def download_file(url, folder):
    """Downloads a file from a URL to a local folder."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        filename = os.path.join(folder, os.path.basename(urlparse(url).path))
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Successfully downloaded {url} to {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {url}", exc_info=True)
        return None
