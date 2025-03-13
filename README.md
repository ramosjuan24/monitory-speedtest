# monitory-speedtest
App para monitorear datos Upload y Download de servicio Internet 


### Instalación y Configuracion de Python

brew install python

python3 --version
which python3 ---> /opt/homebrew/bin/python3

echo 'alias python="python3"' >> ~/.zshrc
source ~/.zshrc

pip3 --version

echo 'alias pip="pip3"' >> ~/.zshrc
source ~/.zshr

### **Configurando Ambiente Virtual**

pip install virtualenv

python3 -m venv mi_entorno

source mi_entorno/bin/activate

python3 -m pip install

**desactivar ambiente virtual**

deactivate

python3 -m pip install --break-system-packages dash plotly speedtest-cli


### Ejecutar Proyecto

Instalar 

pip install dash plotly speedtest-cli
pip kaleido
pip reportlab

recuerda copiar el archivo network_monitor.py en el entorno virtual
cp network_monitor.py /.mi_entorno

python network_monitor.py

Uninstall
pip uninstall speedtest speedtest-cli -y
pip install speedtest-cli
