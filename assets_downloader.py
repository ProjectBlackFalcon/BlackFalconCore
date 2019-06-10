import pymongo
from credentials import credentials
import os
import hashlib
import json


def generate_file_md5(path, blocksize=2**20):
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def create_assets_checksums():
    checksums = {}
    for file in os.listdir('assets'):
        if file.endswith('.json'):
            checksums[file.replace('.json', '')] = generate_file_md5('assets/' + file)
    return checksums


def get_mongo_checksums(client):
    return {file['filename']: file['checksum_md5'] for file in client.blackfalcon.checksums.find({})}


def get_files_to_update(mongo_checksums, local_checksums):
    files_to_update = []
    for filename, checksum in mongo_checksums.items():
        if not filename in local_checksums.keys() or checksum != local_checksums[filename]:
            print('Checksums don\'t match for', filename)
            files_to_update.append(filename)
    return files_to_update


def download_file(client, filename):
    print('Downloading ' + filename)
    data = client.blackfalcon.files.find_one({'filename': filename})
    with open('assets/' + filename + '.json', 'w', encoding='utf8') as f:
        json.dump(data['payload'], f, ensure_ascii=False)


def remove_deprecated_assets(client):
    local_files = set([path.replace('.json', '') for path in os.listdir(os.path.join(os.path.dirname(__file__), 'assets')) if path.endswith('.json')])
    mongo_files = set([document['filename'] for document in client.blackfalcon.checksums.find({})])
    files_to_remove = local_files - mongo_files
    for file in files_to_remove:
        print('Removing deprecated local file', file)
        os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'assets', file + '.json'))


def update_assets():
    client = pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password']
    )

    remove_deprecated_assets(client)

    mongo_checksums = get_mongo_checksums(client)
    local_checksums = create_assets_checksums()

    files_to_update = get_files_to_update(mongo_checksums, local_checksums)

    [download_file(client, filename) for filename in files_to_update]
    print('All files are up to date')


if __name__ == '__main__':
    update_assets()
