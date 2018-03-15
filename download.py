import zipfile
import os
import sys
import requests
import gzip
from tqdm import tqdm


def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response, destination, chunk_size=32 * 1024):
    total_size = int(response.headers.get('content-length', 0))
    with open(destination, "wb") as f:
        for chunk in tqdm(
                response.iter_content(chunk_size),
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=destination):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


if __name__ == '__main__':
    args = parser.parse_args()

	dirpath = str(args[0])
	data_dir = 'celebA-HQ'

	global_data_dir = os.path.join(dirpath, data_dir)
    if os.path.exists(global_data_dir):
        print('Found CelebA-HQ - skip')
        return
    else:
		os.makedirs(global_data_dir, exist_ok=True)

	filenames = [
	    'deltas00000.zip', 'deltas01000.zip', 'deltas02000.zip',
	    'deltas03000.zip', 'deltas04000.zip', 'deltas05000.zip',
	    'deltas06000.zip', 'deltas07000.zip', 'deltas08000.zip',
	    'deltas09000.zip', 'deltas10000.zip', 'deltas11000.zip',
	    'deltas12000.zip', 'deltas13000.zip', 'deltas14000.zip',
	    'deltas15000.zip', 'deltas16000.zip', 'deltas17000.zip',
	    'deltas18000.zip', 'deltas19000.zip', 'deltas20000.zip',
	    'deltas21000.zip', 'deltas22000.zip', 'deltas23000.zip',
	    'deltas24000.zip', 'deltas25000.zip', 'deltas26000.zip',
	    'deltas27000.zip', 'deltas28000.zip', 'deltas29000.zip'
	]

	drive_ids = [
	    '0B4qLcYyJmiz0TXdaTExNcW03ejA', '0B4qLcYyJmiz0TjAwOTRBVmRKRzQ',
	    '0B4qLcYyJmiz0TjNRV2dUamd0bEU', '0B4qLcYyJmiz0TjRWUXVvM3hZZE0',
	    '0B4qLcYyJmiz0TjRxVkZ1NGxHTXc', '0B4qLcYyJmiz0TjRzeWlhLVJIYk0',
	    '0B4qLcYyJmiz0TjVkYkF4dTJRNUk', '0B4qLcYyJmiz0TjdaV2ZsQU94MnM',
	    '0B4qLcYyJmiz0Tksyd21vRmVqamc', '0B4qLcYyJmiz0Tl9wNEU2WWRqcE0',
	    '0B4qLcYyJmiz0TlBCNFU3QkctNkk', '0B4qLcYyJmiz0TlNyLUtOTzk3QjQ',
	    '0B4qLcYyJmiz0Tlhvdl9zYlV4UUE', '0B4qLcYyJmiz0TlpJU1pleF9zbnM',
	    '0B4qLcYyJmiz0Tm5MSUp3ZTZ0aTg', '0B4qLcYyJmiz0TmRZTmZyenViSjg',
	    '0B4qLcYyJmiz0TmVkVGJmWEtVbFk', '0B4qLcYyJmiz0TmZqZXN3UWFkUm8',
	    '0B4qLcYyJmiz0TmhIUGlVeE5pWjg', '0B4qLcYyJmiz0TnBtdW83OXRfdG8',
	    '0B4qLcYyJmiz0TnJQSS1vZS1JYUE', '0B4qLcYyJmiz0TzBBNE8xbFhaSlU',
	    '0B4qLcYyJmiz0TzZySG9IWlZaeGc', '0B4qLcYyJmiz0U05ZNG14X3ZjYW8',
	    '0B4qLcYyJmiz0U0YwQmluMmJuX2M', '0B4qLcYyJmiz0U0lYX1J1Tk5vMjQ',
	    '0B4qLcYyJmiz0U0tBanQ4cHNBUWc', '0B4qLcYyJmiz0U1BRYl9tSWFWVGM',
	    '0B4qLcYyJmiz0U1BhWlFGRXc1aHc', '0B4qLcYyJmiz0U1pnMEI4WXN1S3M'
	]

	for filename, drive_id in zip(filenames, drive_ids):
	    print('Deal with file: ' + filename)
	    save_path = os.path.join(dirpath, filename)

	    if os.path.exists(save_path):
	        print('[*] {} already exists'.format(save_path))
	    else:
	        download_file_from_google_drive(drive_id, save_path)

	    zip_dir = ''
	    with zipfile.ZipFile(save_path) as zf:
	        zip_dir = zf.namelist()[0]
	        zf.extractall(global_data_dir)
	    os.remove(save_path)