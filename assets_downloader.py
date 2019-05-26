import pymongo
from credentials import credentials
import os
import hashlib


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
        checksums['file'] = generate_file_md5('assets/' + file)
    return checksums


def get_mongo_checksums(client):
    for file in client.blackfalcon.checksums.find({}):
        print(file)

client = pymongo.MongoClient(
    host=credentials['mongo']['host'],
    port=credentials['mongo']['port'],
    username=credentials['mongo']['username'],
    password=credentials['mongo']['password']
)

print(get_mongo_checksums(client))


# calculate the checksums of the current resources
# compare them to mongo's
# download the files which do not match