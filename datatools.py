        


        # Load delta image and original JPG.
        with zipfile.ZipFile(os.path.join(delta_dir, 'deltas%05d.zip' % (idx - idx % 1000)), 'r') as zip:
            delta_bytes = zip.read('delta%05d.dat' % idx)
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