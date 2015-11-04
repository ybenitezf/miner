# miner

```miner``` es una pequeña herramienta que permite hacer el pre-procesamiento 
de archivos de log para los formatos de log de acceso de Squid-proxy cache y 
Apache Common Log.

Esta herramienta permite la impletación de plugins que recibirán instancias de
```LogEntry``` (```SQUIDLogEntry``` o ```CommonLogEntry``` según corresponda)
dejando en mano del autor del plugin lo referente a procesar cada una de las
entradas.

## configuración e instalación

1.- Clonar el repositorio:
```bash
$ git clone https://github.com/ybenitezf/miner.git
$ cd miner
```
2.- Configurar: con un editor de texto cualquiera editar el archivo 
```config.ini```, en la sección ```[main]``` solo se encuentran los valores de
configuración para ```miner```, para los plugins es necesario adicionar una
sección nueva para cada uno si es que lo necesitan, como ejemplo se incluye la
configuración para el plugin ```CategoryClassifier```, como convención la
sección de configuración para cada plugin debe llamarse igual al plugin.

El la sección ```main```, el parámetro ```logfile``` indica de donde se leeran
las entradas de log, logfile puede ser una carpeta o el camino a un solo
archivo. En el caso de que sea una carpeta en esta deben encontrarse los
archivos de log a procesar.

```data_dir``` es la carpeta donde los pluggins pueden guardar datos
adicionales o temporales, siguiendo como convención hacerlo en una subcarpeta de
esta con el nombre del plugin.

3.- Poner en la carpeta logs los archivos de log a procesar.

4.- ejecutar miner:

```bash
$ python miner.py
```

## ¿Cómo implementar un plugin?

### Ejemplo 1

En forma de ejemplo vamos construir un plugin que cuente la cantidad veces que
un usuario entro en facebook, al final la salida de nuestro plugin sera un
archivo de texto con dos columnas por linea de la forma:

```usuario, cantidad```

Para esto vamos a añadir un modulo al directorio ```plugins``` en la raíz de
miner, a este lo vamos a llamar ```cuetafb.py``` con el código:

```python
from parser.logParser import LogObserverPlugin, SQUIDLogEntry, CommonLogEntry

class CuentaFB(LogObserverPlugin):

    def __init__(self, *args, **kwargs):
        super(CuentaFB, self).__init__(*args, **kwargs)

    def notificar(self, entry):
        pass
    
    def writeOutput(self):
        pass
```
