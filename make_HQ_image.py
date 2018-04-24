import glob
import os
import PIL
import hashlib
import numpy as np
from PIL import Image
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.backends
import cryptography.hazmat.primitives.kdf.pbkdf2
import cryptography.fernet
import base64
import bz2
import scipy
from scipy import ndimage
import threading
import traceback
import sys
import six.moves.queue as Queue

class ExceptionInfo(object):
    def __init__(self):
        self.value = sys.exc_info()[1]
        self.traceback = traceback.format_exc()


class WorkerThread(threading.Thread):
    def __init__(self, task_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue

    def run(self):
        while True:
            func, args, result_queue = self.task_queue.get()
            if func is None:
                break
            try:
                result = func(*args)
            except:
                result = ExceptionInfo()
            result_queue.put((result, args))

class ThreadPool(object):
    def __init__(self, num_threads):
        assert num_threads >= 1
        self.task_queue = Queue.Queue()
        self.result_queues = dict()
        self.num_threads = num_threads
        for idx in range(self.num_threads):
            thread = WorkerThread(self.task_queue)
            thread.daemon = True
            thread.start()

    def add_task(self, func, args=()):
        assert hasattr(func, '__call__') # must be a function
        if func not in self.result_queues:
            self.result_queues[func] = Queue.Queue()
        self.task_queue.put((func, args, self.result_queues[func]))

    def get_result(self, func): # returns (result, args)
        result, args = self.result_queues[func].get()
        if isinstance(result, ExceptionInfo):
            print('\n\nWorker thread caught an exception:\n' + result.traceback)
            raise result.value
        return result, args

    def finish(self):
        for idx in range(self.num_threads):
            self.task_queue.put((None, (), None))

    def __enter__(self): # for 'with' statement
        return self

    def __exit__(self, *excinfo):
        self.finish()

    def process_items_concurrently(self, item_iterator, process_func=lambda x: x, pre_func=lambda x: x, post_func=lambda x: x, max_items_in_flight=None):
        if max_items_in_flight is None: max_items_in_flight = self.num_threads * 4
        assert max_items_in_flight >= 1
        results = []
        retire_idx = [0]

        def task_func(prepared, idx):
            return process_func(prepared)
           
        def retire_result():
            processed, (prepared, idx) = self.get_result(task_func)
            results[idx] = processed
            while retire_idx[0] < len(results) and results[retire_idx[0]] is not None:
                yield post_func(results[retire_idx[0]])
                results[retire_idx[0]] = None
                retire_idx[0] += 1  
        for idx, item in enumerate(item_iterator):
            prepared = pre_func(item)
            results.append(None)
            self.add_task(func=task_func, args=(prepared, idx))
            while retire_idx[0] < idx - max_items_in_flight + 2:
                for res in retire_result(): yield res
        while retire_idx[0] < len(results):
            for res in retire_result(): yield res


dataset_dir='celeba'
expected_images = 202599
delta_dir = 'celebA-HQ'
num_tasks = 12

celeba_dir = os.path.join(dataset_dir, 'Img/img_celeba')
print('Loading CelebA from {}'.format(celeba_dir))
if len(glob.glob(os.path.join(celeba_dir, '*.jpg'))) != expected_images:
    raise ValueError('Expected to find {} images'.format(expected_images))

with open(os.path.join(dataset_dir, 'Anno', 'list_landmarks_celeba.txt'), 'rt') as file:
    landmarks = [[float(value) for value in line.split()[1:]] for line in file.readlines()[2:]]
    landmarks = np.float32(landmarks).reshape(-1, 5, 2)

print('Loading CelebA-HQ deltas from {}'.format(delta_dir))
expected_dat = 30000

if len(glob.glob(os.path.join(delta_dir, '*.dat'))) != expected_dat:
    raise ValueError('Expected to find {} dat files'.format(expected_dat))

with open(os.path.join('image_list.txt'), 'rt') as file:
    lines = [line.split() for line in file]
    fields = dict()
    for idx, field in enumerate(lines[0]):
        typef = int if field.endswith('idx') else str
        fields[field] = [typef(line[idx]) for line in lines[1:]]

indices = np.array(fields['idx'])


# Must use pillow version 3.1.1 for everything to work correctly.
if getattr(PIL, 'PILLOW_VERSION', '') != '3.1.1':
    raise ValueError('create_celebahq requires pillow version 3.1.1') # conda install pillow=3.1.1

# Must use libjpeg version 8d for everything to work correctly.
img = np.array(PIL.Image.open(os.path.join(celeba_dir, '000001.jpg')))
md5 = hashlib.md5()
md5.update(img.tobytes())
if md5.hexdigest() != '9cad8178d6cb0196b36f7b34bc5eb6d3':
    raise ValueError('create_celebahq requires libjpeg version 8d') # conda install jpeg=8d





def rot90(v):
    return np.array([-v[1], v[0]])

def process_func(idx):
    # Load original image.
    orig_idx = fields['orig_idx'][idx]
    orig_file = fields['orig_file'][idx]
    orig_path = os.path.join(celeba_dir, orig_file)
    img = PIL.Image.open(orig_path)
    # Choose oriented crop rectangle.
    lm = landmarks[orig_idx]
    eye_avg = (lm[0] + lm[1]) * 0.5 + 0.5
    mouth_avg = (lm[3] + lm[4]) * 0.5 + 0.5
    eye_to_eye = lm[1] - lm[0]
    eye_to_mouth = mouth_avg - eye_avg
    x = eye_to_eye - rot90(eye_to_mouth)
    x /= np.hypot(*x)
    x *= max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)
    y = rot90(x)
    c = eye_avg + eye_to_mouth * 0.1
    quad = np.stack([c - x - y, c - x + y, c + x + y, c + x - y])
    zoom = 1024 / (np.hypot(*x) * 2)
    # Shrink.
    shrink = int(np.floor(0.5 / zoom))
    if shrink > 1:
        size = (int(np.round(float(img.size[0]) / shrink)), int(np.round(float(img.size[1]) / shrink)))
        img = img.resize(size, PIL.Image.ANTIALIAS)
        quad /= shrink
        zoom *= shrink
    # Crop.
    border = max(int(np.round(1024 * 0.1 / zoom)), 3)
    crop = (int(np.floor(min(quad[:,0]))), int(np.floor(min(quad[:,1]))), int(np.ceil(max(quad[:,0]))), int(np.ceil(max(quad[:,1]))))
    crop = (max(crop[0] - border, 0), max(crop[1] - border, 0), min(crop[2] + border, img.size[0]), min(crop[3] + border, img.size[1]))
    if crop[2] - crop[0] < img.size[0] or crop[3] - crop[1] < img.size[1]:
        img = img.crop(crop)
        quad -= crop[0:2]
    # Simulate super-resolution.
    superres = int(np.exp2(np.ceil(np.log2(zoom))))
    if superres > 1:
        img = img.resize((img.size[0] * superres, img.size[1] * superres), PIL.Image.ANTIALIAS)
        quad *= superres
        zoom /= superres
    # Pad.
    pad = (int(np.floor(min(quad[:,0]))), int(np.floor(min(quad[:,1]))), int(np.ceil(max(quad[:,0]))), int(np.ceil(max(quad[:,1]))))
    pad = (max(-pad[0] + border, 0), max(-pad[1] + border, 0), max(pad[2] - img.size[0] + border, 0), max(pad[3] - img.size[1] + border, 0))
    if max(pad) > border - 4:
        pad = np.maximum(pad, int(np.round(1024 * 0.3 / zoom)))
        img = np.pad(np.float32(img), ((pad[1], pad[3]), (pad[0], pad[2]), (0, 0)), 'reflect')
        h, w, _ = img.shape
        y, x, _ = np.mgrid[:h, :w, :1]
        mask = 1.0 - np.minimum(np.minimum(np.float32(x) / pad[0], np.float32(y) / pad[1]), np.minimum(np.float32(w-1-x) / pad[2], np.float32(h-1-y) / pad[3]))
        blur = 1024 * 0.02 / zoom
        img += (scipy.ndimage.gaussian_filter(img, [blur, blur, 0]) - img) * np.clip(mask * 3.0 + 1.0, 0.0, 1.0)
        img += (np.median(img, axis=(0,1)) - img) * np.clip(mask, 0.0, 1.0)
        img = PIL.Image.fromarray(np.uint8(np.clip(np.round(img), 0, 255)), 'RGB')
        quad += pad[0:2]    
    # Transform.
    img = img.transform((4096, 4096), PIL.Image.QUAD, (quad + 0.5).flatten(), PIL.Image.BILINEAR)
    img = img.resize((1024, 1024), PIL.Image.ANTIALIAS)
    img = np.asarray(img).transpose(2, 0, 1)
    # Verify MD5.
    md5 = hashlib.md5()
    md5.update(img.tobytes())
    assert md5.hexdigest() == fields['proc_md5'][idx]
    # # Load delta image and original JPG.
    # with zipfile.ZipFile(os.path.join(delta_dir, 'deltas%05d.zip' % (idx - idx % 1000)), 'r') as zip:
    #     delta_bytes = zip.read('delta%05d.dat' % idx)
    with open(os.path.join(delta_dir,'delta%05d.dat' % idx), 'rb') as file:
        delta_bytes = file.read()
    with open(orig_path, 'rb') as file:
        orig_bytes = file.read()
    # Decrypt delta image, using original JPG data as decryption key.
    algorithm = cryptography.hazmat.primitives.hashes.SHA256()
    backend = cryptography.hazmat.backends.default_backend()
    salt = bytes(orig_file, 'ascii')
    kdf = cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC(algorithm=algorithm, length=32, salt=salt, iterations=100000, backend=backend)
    key = base64.urlsafe_b64encode(kdf.derive(orig_bytes))
    delta = np.frombuffer(bz2.decompress(cryptography.fernet.Fernet(key).decrypt(delta_bytes)), dtype=np.uint8).reshape(3, 1024, 1024)
    # Apply delta image.
    img = img + delta
    # Verify MD5.
    md5 = hashlib.md5()
    md5.update(img.tobytes())
    assert md5.hexdigest() == fields['final_md5'][idx]
    return img

num_threads=num_tasks
with ThreadPool(num_threads) as pool:
    for img_num, img in enumerate(pool.process_items_concurrently(indices.tolist(), process_func=process_func, max_items_in_flight=num_tasks)):
        print('Create image number {}'.format(img_num))
        img = process_func(img_num)
        np.save(os.path.join(delta_dir, 'imgHQ%05d' % img_num), [img])

# for img_num in range(expected_dat):
#     print('Create image number {}'.format(img_num))
#     img = process_func(img_num)
#     np.save(os.path.join(delta_dir, 'imgHQ%05d' % img_num), [img])
