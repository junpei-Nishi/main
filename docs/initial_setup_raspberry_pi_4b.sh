# Install dependecies
cd
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y git htop mlocate
sudo apt-get install -y cmake
sudo apt-get install -y libtiff5-dev libjasper-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install -y libxvidcore-dev libx264-dev
sudo apt-get install -y libcairo2-dev
sudo apt-get install -y libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt-get install -y libgtk2.0-dev libgtk-3-dev
sudo apt-get install -y libatlas-base-dev gfortran
sudo apt-get install -y libhdf5-dev libhdf5-103
sudo apt-get install -y libqtgui4 libqtwebkit4 libqt4-test
sudo apt-get install -y llvm
sudo apt-get install -y libusb-1.0-0-dev cython
sudo apt-get install -y libblas-dev liblapack-dev

# Make a temp dir
mkdir temp
cd temp

# Install QT
wget https://github.com/koendv/qt5-opengl-raspberrypi/releases/download/v5.12.5-1/qt5-opengl-dev_5.12.5_armhf.deb
sudo apt install -y ./qt5-opengl-dev_5.12.5_armhf.deb

# Install sip
mkdir src
cd src
wget https://www.riverbankcomputing.com/static/Downloads/sip/4.19.14/sip-4.19.14.tar.gz
tar -xvzf sip-4.19.14.tar.gz
cd sip-4.19.14
python3 configure.py --sip-module=PyQt5.sip
make
sudo make install
cd ~/temp

# Install PyQt5
wget https://www.riverbankcomputing.com/static/Downloads/PyQt5/5.12/PyQt5_gpl-5.12.tar.gz
tar -xvzf PyQt5_gpl-5.12.tar.gz
cd PyQt5_gpl-5.12
LD_LIBRARY_PATH=/usr/lib/qt5.12/lib python3 configure.py --confirm-license --qmake=/usr/lib/qt5.12/bin/qmake QMAKE_LFLAGS_RPATH=
make
sudo make install
cd ~/temp

# Install PyQt Webengine
wget https://www.riverbankcomputing.com/static/Downloads/PyQtWebEngine/5.12/PyQtWebEngine_gpl-5.12.tar.gz
tar -xvzf PyQtWebEngine_gpl-5.12.tar.gz
cd PyQtWebEngine_gpl-5.12
LD_LIBRARY_PATH=/usr/lib/qt5.12/lib python3 configure.py --qmake=/usr/lib/qt5.12/bin/qmake
make
sudo make install
cd ~/temp

# Build libuvc
cd ~/temp/src
git clone https://github.com/pupil-labs/libuvc
cd libuvc
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
cd ~/temp

# Build libjpeg-turbo
cd ~/temp/src
wget -O libjpeg-turbo.tar.gz https://sourceforge.net/projects/libjpeg-turbo/files/1.5.1/libjpeg-turbo-1.5.1.tar.gz/download
tar xvzf libjpeg-turbo.tar.gz
cd libjpeg-turbo-1.5.1
./configure --with-pic --prefix=/usr/local
sudo make install
sudo ldconfig
cd ~/temp

# Install pip
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo python3 get-pip.py

# Install cython
sudo pip install cython

# Configrue udev rules
echo 'SUBSYSTEM=="usb",  ENV{DEVTYPE}=="usb_device", GROUP="plugdev", MODE="0664"' | sudo tee /etc/udev/rules.d/10-libuvc.rules > /dev/null
sudo udevadm trigger

# Install pyuvc
cd ~/temp/src
git clone https://github.com/pupil-labs/pyuvc.git
cd pyuvc
sudo python3 setup.py install
cd ~/temp

# Install python libraries
sudo apt-get install -y python3-joblib python3-seaborn python3-opencv python3-scipy python3-skimage python3-sklearn python3-pandas python3-sklearn-pandas python3-numpy python3-matplotlib python3-imageio python3-pyqtgraph python3-jinja2 python3-serial python3-six

# Install pip libraries
sudo pip install wrapt -U --ignore-installed
sudo pip install --default-timeout=1000 tensorflow==1.13.1
sudo pip install --default-timeout=1000 keras==2.2.4
sudo pip install -r ~/Desktop/sdtest/requirements.txt -U --ignore-installed
sudo pip install pyqtdeploy
sudo pip install --default-timeout=1000 opencv-contrib-python
sudo pip install GitPython
sudo pip install pyod
sudo pip install fbs[sentry]==0.8.3
sudo pip install PyInstaller==3.4
sudo pip install pybind11

# Build Scipy
cd ~/temp/src
git clone https://github.com/scipy/scipy
cd scipy
sudo python3 setup.py install
cd ~/temp

# Upscale swap size
sudo sed -i -e "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/g" /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart
cat /etc/dphys-swapfile | grep CONF_SWAPSIZE

# Fix a bug of cv2
LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
echo "export LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1" >> ~/.bashrc
source ~/.bashrc