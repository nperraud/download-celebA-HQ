# download-celebA-HQ
Python script to download and create the celebA-HQ dataset.

To get the celebA-HQ dataset, you need to 
 a) download the celebA dataset `download_celebA.py` ,
 b) download some extra files `download_celebA_HQ.py`,
 c) do some processing to get the HQ images `make_HQ_images.py`.

The size of the final dataset is 89G. However, you will need a bit more storage to be able to run the scripts.

# Usage
1) Clone the repository
```
git clone https://github.com/nperraud/download-celebA-HQ.git
cd download-celebA-HQ
```

2) Install necessary packages (Because specific versions are required Conda is recomended)
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

3) Run the scripts
```
python download_celebA.py ./
python download_celebA_HQ.py ./
python make_HQ_images.py ./

```
where `./` is the directory where you wish the data to be saved.

4) Go watch a movie, theses scripts will take a few hours to run depending on your internet connection and your CPU power. The final HQ images will be saved as `.npy` files in the `./celebA-HQ` folder.

## Windows
The script may work on windows, though I have not tested this solution personnaly

Step 2 becomes
 * Install miniconda https://conda.io/miniconda.html or anaconda
 * Create a new environement
 ```
 conda create -n celebaHQ python=3
 source activate celebaHQ
 ```
 * Install the packages
 ```
 conda  install -c anaconda jpeg=8d tqdm requests pillow==3.1.1 urllib3 numpy cryptography scipy
  ```
 * Install 7zip 

The rest should be unchanged.

## Docker

If you have Docker installed, skip the previous installation steps and run the following command from the root directory of this project:

`docker build -t celeba . && docker run -it -v $(pwd):/data celeba`

By default, this will create the dataset in same directory. To put it elsewhere, replace `$(pwd)` with the absolute path to the desired output directory.

# Outliers
It seems that the dataset has a few outliers. A of problematic images is stored in `bad_images.txt`. Please report if you find other outliers.

# Remark
This script is likely to break somewhere, but if it executes until the end, you should obtain the correct dataset.

# Sources
This code is inspired by these files
* https://github.com/tkarras/progressive_growing_of_gans/blob/master/dataset_tool.py
* https://github.com/andersbll/deeppy/blob/master/deeppy/dataset/celeba.py
* https://github.com/andersbll/deeppy/blob/master/deeppy/dataset/util.py

# Citing the dataset
You probably want to cite the paper "Progressive Growing of GANs for Improved Quality, Stability, and Variation" that was submitted to ICLR 2018 by Tero Karras (NVIDIA), Timo Aila (NVIDIA), Samuli Laine (NVIDIA), Jaakko Lehtinen (NVIDIA and Aalto University).
