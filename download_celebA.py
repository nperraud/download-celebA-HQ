import tarfile
import zipfile
import gzip
import os
import hashlib
import sys
from glob import glob

if sys.version_info[0] > 2:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
from subprocess import Popen
import argparse

parser = argparse.ArgumentParser(description='Download celebA helper')
parser.add_argument('path', type=str)

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


def download(url, target_dir, filename=None):
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
    elif '.7z' in filepath:
        if os.name != 'posix':
            raise NotImplementedError('Only Linux and Mac OS X support .7z '
                                      'compression.')
        print('Using 7z!!!')
        cmd = '7z x {} -o{}'.format(filepath, target_dir)
        retval = Popen(cmd, shell=True).wait()
        if retval != 0:
            raise RuntimeError(
                'Archive file extraction failed for {}.'.format(filepath))
    elif filepath[-2:].lower() == '.z':
        if os.name != 'posix':
            raise NotImplementedError('Only Linux and Mac OS X support .Z '
                                      'compression.')
        cmd = 'gzip -d {}'.format(filepath)
        retval = Popen(cmd, shell=True).wait()
        if retval != 0:
            raise RuntimeError(
                'Archive file extraction failed for {}.'.format(filepath))
    else:
        raise ValueError('{} is not a supported archive file.'.format(filepath))


def download_celabA(dataset_dir):

    _IMGS_URL = ('https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AAAq9krDJxUMh1m0hbbxdnl4a/Img/img_celeba.7z?dl=1',
        '37af560349c7d2e51fcc4461168452c743c9cb96')

    _ALIGNED_IMGS_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AADIKlz8PR9zr6Y20qbkunrba/Img/img_align_celeba.zip?dl=1',
        'b7e1990e1f046969bd4e49c6d804b93cd9be1646')

    _PARTITIONS_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AADxLE5t6HqyD8sQCmzWJRcHa/Eval/list_eval_partition.txt?dl=1',
        'fb3d89825c49a2d389601eacb10d73815fd3c52d')

    _ALIGNED_ATTRIBUTES_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AAC7-uCaJkmPmvLX2_P5qy0ga/Anno/list_attr_celeba.txt?dl=1',
        '225788ff6c9d0b96dc21144147456e0388195617')

    _ATTRIBUTES_URL = (
        'https://www.dropbox.com/sh/8oqt9vytwxb3s4r/AAANSiC4E2KoizMw92lvJTOta/Anno/list_landmarks_celeba.txt?dl=1',
        'ea255cd0ffe98ca88bff23767f7a5ece7710db57')

    n_imgs = 202599
    img_dir_align = os.path.join(dataset_dir, 'Img', 'img_align_celeba')
    img_dir = os.path.join(dataset_dir, 'Img', 'img_celeba')

    url, sha1 = _ALIGNED_IMGS_URL
    print('Downloading {}'.format(url))
    filepath = download(url, dataset_dir)
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)

    print('Extract archive {}'.format(filepath))
    archive_extract(filepath, os.path.join(dataset_dir, 'Img'))
    print('Done!')
    os.remove(filepath)

    n_imgsd = sum([1 for file in os.listdir(img_dir_align) if file[-4:] == '.jpg'])
    assert (n_imgsd == n_imgs)

    url, sha1 = _PARTITIONS_URL
    print('Downloading {}'.format(url))
    filepath = download(url, os.path.join(dataset_dir,'Eval'))
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)

    url, sha1 = _ATTRIBUTES_URL
    print('Downloading {}'.format(url))
    filepath = download(url, os.path.join(dataset_dir,'Anno'))
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)

    url, sha1 = _ALIGNED_ATTRIBUTES_URL
    print('Downloading {}'.format(url))
    filepath = download(url, os.path.join(dataset_dir,'Anno'))
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)

    url, sha1 = _IMGS_URL
    print('Downloading {}'.format(url))
    filepath = download(url, dataset_dir)
    print('Done!')
    print('Check SHA1 {}'.format(filepath))
    if sha1 != checksum(filepath, 'sha1'):
        raise RuntimeError('Checksum mismatch for %s.' % url)

    print('Extract archive {}'.format(filepath))
    archive_extract(filepath, dataset_dir)
    os.remove(filepath)
    filepath = os.path.join(dataset_dir, 'img_celeba.7z.001')
    archive_extract(filepath, os.path.join(dataset_dir, 'Img'))
    print('Done!')

    for file in os.listdir(dataset_dir):
        if file[:14] == 'img_celeba.7z.':
            filepath = os.path.join(dataset_dir, file)
            print('Remove: {}'.format(filepath))
            os.remove(filepath)

    n_imgsd = len(glob(os.path.join(img_dir, '*.jpg')))
    assert (n_imgsd == n_imgs)

    return True

if __name__ == '__main__':
    args = parser.parse_args()
    dirpath = args.path
    dataset_dir = os.path.join(dirpath, 'celebA')
    download_celabA(dataset_dir)
