import tarfile
import zipfile
import gzip
import os
import hashlib
import sys
if sys.version_info[0] > 2:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
import numpy as np
from subprocess import Popen


def require_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return None


def checksum(filename, method='sha1'):
    data = open(filename, 'rb').read()
    if method == 'sha1':
        return hashlib.sha1(data).hexdigest()
    elif method == 'md5':
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError('Invalid method: %s' % method)
    return None


def download(url, target_dir='./data/', filename=None):
    require_dir(target_dir)
    if filename is None:
        filename = url_filename(url)
    filepath = os.path.join(target_dir, filename)
    urlretrieve(url, filepath)
    return filepath


def url_filename(url):
    return url.split('/')[-1].split('#')[0].split('?')[0]


def archive_extract(filepath, target_dir):
    target_dir = os.path.abspath(target_dir)
    if tarfile.is_tarfile(filepath):
        with tarfile.open(filepath, 'r') as tarf:
            # Check that no files get extracted outside target_dir
            for name in tarf.getnames():
                abs_path = os.path.abspath(os.path.join(target_dir, name))
                if not abs_path.startswith(target_dir):
                    raise RuntimeError('Archive tries to extract files '
                                       'outside target_dir.')
            tarf.extractall(target_dir)
    elif zipfile.is_zipfile(filepath):
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(target_dir)
    elif filepath[-3:].lower() == '.gz':
        with gzip.open(filepath, 'rb') as gzipf:
            with open(filepath[:-3], 'wb') as outf:
                outf.write(gzipf.read())
    elif filepath[-2:].lower() == '.z':
        if os.name != 'posix':
            raise NotImplementedError('Only Linux and Mac OS X support .Z '
                                      'compression.')
        cmd = 'gzip -d %s' % filepath
        retval = Popen(cmd, shell=True).wait()
        if retval != 0:
            raise RuntimeError(
                'Archive file extraction failed for %s.' % filepath)
    else:
        raise ValueError('% is not a supported archive file.' % filepath)


def download_celabA(datasets_dir='datasets'):

    _ALIGNED_IMGS_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AADIKlz8PR9zr6Y20qbkunrba/Img/img_align_celeba.zip?dl=1',
        'b7e1990e1f046969bd4e49c6d804b93cd9be1646')

    _PARTITIONS_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AADxLE5t6HqyD8sQCmzWJRcHa/Eval/list_eval_partition.txt?dl=1',
        'fb3d89825c49a2d389601eacb10d73815fd3c52d')

    _ATTRIBUTES_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AAC7-uCaJkmPmvLX2_P5qy0ga/Anno/list_attr_celeba.txt?dl=1',
        '225788ff6c9d0b96dc21144147456e0388195617')

    name = 'celeba'
    n_imgs = 202599
    data_dir = os.path.join(datasets_dir, name)
    npz_path = os.path.join(data_dir, name + '.npz')
    img_dir = os.path.join(data_dir, 'img_align_celeba')

    url, sha1 = _ALIGNED_IMGS_URL
    print('Downloading {}'.format(url))
    filepath = download(url, datasets_dir)
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)
    # os.remove(filepath)

    print('Extract archive {}'.format(filepath))
    archive_extract(filepath, data_dir)
    print('Done!')

    url, sha1 = _PARTITIONS_URL
    print('Downloading {}'.format(url))
    filepath = download(url, datasets_dir)
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)
    partitions = [[], [], []]
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            img_name, partition = line.strip().split(' ')
            if int(img_name[:6]) != i + 1:
                raise ValueError('Parse error.')
            partition = int(partition)
            partitions[partition].append(i)
    train_idxs, val_idxs, test_idxs = map(np.array, partitions)
    # os.remove(filepath)
    n_imgsd = sum([1 for file in os.listdir(img_dir) if file[-4:] == '.jpg'])
    assert (n_imgsd == n_imgs)

    url, sha1 = _ATTRIBUTES_URL
    print('Downloading {}'.format(url))
    filepath = download(url, datasets_dir)
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)
    attributes = []
    with open(filepath, 'r') as f:
        f.readline()
        attribute_names = f.readline().strip().split(' ')
        for i, line in enumerate(f):
            fields = line.strip().replace('  ', ' ').split(' ')
            img_name = fields[0]
            if int(img_name[:6]) != i + 1:
                raise ValueError('Parse error.')
            attr_vec = np.array(map(int, fields[1:]))
            attributes.append(attr_vec)
    attributes = np.array(attributes)
    # os.remove(filepath)

    with open(npz_path, 'wb') as f:
        np.savez(
            f,
            train_idxs=train_idxs,
            val_idxs=val_idxs,
            test_idxs=test_idxs,
            attribute_names=attribute_names,
            attributes=attributes)
    return True

if __name__ == '__main__':
    download_celabA()
