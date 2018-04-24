# download-celebA-HQ
Python script to download and create the celebA-HQ dataset.



# Usage
1) Clone the repository
```
git clone https://github.com/nperraud/download-celebA-HQ.git
cd download-celebA-HQ
```

2) Install necessary packages (Becase specific versions are required Conda is recomended)
 * Install miniconda https://conda.io/miniconda.html
 * Create a new environement
 ```
 	conda create -n celebaHQ python=3
 	source activate celebaHQ
 ```
 * Install the packages

 ```
	conda install jpeg=8d tqdm requests pillow==3.1.1 urllib3 numpy cryptography scipy
	pip install opencv-python==3.4.0.12 cryptography==2.1.4
 ```
 * Install 7zip (On Ubuntu)
 ```
 	sudo apt-get install p7zip-full
 ```

3) Run the script
```
python download.py ./
```
where `./` is the directory where you wish the data to be saved.


# Remark
This script is likely to break somewhere, but if it executes until the end, you should obtain the correct dataset.
