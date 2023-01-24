# SmartWatch-Visualizer
Visualizer and annotator for CASAS Smart Watch datasets


# Dependencies
This was tested with Python 3.10.

### Arch Linux
```commandline
pamac install python-pygobject
# pamac install python-pygobject-stubs  # Used in development.
pamac install python-geopandas
pamac install python-matplotlib
pamac install python-contextily
```

### Ubuntu Linux
```commandline
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pip
pip3 install geopandas matplotlib contextily
```

### Windows
1. Go to http://www.msys2.org/ and download the x86_64 installer
2. Follow the instructions on the page for setting up the basic environment
3. Run `C:\msys64\mingw64.exe` - a terminal window should pop up
4. Execute `pacman -Suy` (you might need to do this a couple of times for all updates)
5. Execute `pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3 mingw-w64-x86_64-python3-gobject mingw-w64-x86_64-python3-pip mingw-w64-x86_64-python3-matplotlib mingw-w64-x86_64-python3-pandas`
6. To test that GTK 3 is working you can run `gtk3-demo`
7. Download and install Anaconda https://www.anaconda.com/products/distribution#Downloads
8. Open the Anaconda Prompt (`Start->Anaconda3 (64-bit)->Anaconda Prompt`)
9. In anaconda run these 3 commands (you can copy each line then right click to paste)
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create --name smartwatchviz python=3.10 gtk3=3.24.36 matplotlib=3.6.2 geopandas=0.12.2 contextily=1.2.0 pygobject=3.42.2
```
10. Activate the `smartwatchviz` environment by running
```commandline
conda activate smartwatchviz
```
11. cd to the downloaded program directory
```commandline
cd Documents/SmartWatch-Visualizer
```
12. Run the program
```commandline
python viz.py
```

### MacOS
1. Go to https://brew.sh/ and install homebrew
2. Open a terminal
3. Execute `brew install pygobject3 gtk+3`
4. Download and install Anaconda https://www.anaconda.com/products/distribution#Downloads
5. Open the Anaconda Prompt
6. In anaconda run these 3 commands
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create --name smartwatchviz python=3.10 gtk3=3.24.36 matplotlib=3.6.2 geopandas=0.12.2 contextily=1.2.0 pygobject=3.42.2
```
7. Activate the `smartwatchviz` environment by running
```commandline
conda activate smartwatchviz
```
8. cd to the downloaded program directory
```commandline
cd SmartWatch-Visualizer
```
9. Run the program
```commandline
python viz.py
```

