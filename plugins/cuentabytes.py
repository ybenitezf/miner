# coding: utf-8
__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'
__doc__ = """CuentaBytes

Este plugin produce como salida un archivo en formato ARFF donde las instancias
tendrán la forma:

usuario, bytes sitio 1, bytes sitio 2, ..., bytes sitio n

Donde:
    usuario: nombre del usuario
    bytes sitio X: es la cantidad de bytes descargados por el usuario en el 
                   sitio X

Dependiendo de la configuración usuario puede ser el nombre del usuario o el 
número IP del cliente.

Los sitios a tener en cuenta se darán por medio de un parametro de 
configuración.

Configuración
===============================================================================

Ejemplo de sección de configuración

[CuentaBytes]
usuarios=1
sitios=sitios.txt
salida=cuentabytes.arff

Si el parámetro 'usuarios' es 1 entonces se tendrán en cuenta los nombres
de los usuarios, en caso contrario se usarán los números IP de los clientes.

El parámetro 'sitios' debe ser el nombre de un archivo de texto el cual tendrá
un nombre de sitio por linea y son los que se tendrán en cuenta para contabilizar
los registros de log. Este archivo debe encontrarse en la carpeta CuentaBytes 
dentro del directorio configurado para los datos de los plugins 
(ver documentación de config.ini en [1]), por ejemplo:

facebook.com
google.com
youtube.com

'salida' es el nombre del archivo de salida, será reescrito en caso de existir

[1] https://github.com/ybenitezf/miner/wiki#configuraci%C3%B3n
"""

from parser.logParser import LogObserverPlugin, SQUIDLogEntry
import sys
import os.path

class CuentaBytes(LogObserverPlugin):

    def __init__(self, *args, **kwargs):
        super(CuentaBytes, self).__init__(*args, **kwargs)
        self.habilitado = False
        try:
            self.usuarios = self.config.getboolean('CuentaBytes','usuarios')
            site_file = self.config.get('CuentaBytes', 'sitios')
            data_dir = self.config.get('main', 'data_dir')
            m_path = os.path.join(data_dir, 'CuentaBytes')
            m_path = os.path.join(m_path, site_file)
            self.site_list = []
            for s in open(m_path, 'r'):
                self.site_list.append(s.strip('\n\r '))
            self.habilitado = True
            # almacen para los sumadores
            self.values = dict()
        except:
            # fallar en silencio
            self.habilitado = False


    def notificar(self, entry):
        if isinstance(entry, SQUIDLogEntry) and self.habilitado:
            sitio = entry.get_remote_host()
            key = entry.userId
            if not self.usuarios:
                self.key = entry.clientIP
            if not self.values.has_key(key):
                vector = [0 for i in self.site_list]
                self.values[key] = vector
            
            control = -1
            for i, v in enumerate(self.site_list):
                if sitio == v:
                    control = i
                    break
            if control >= 0:
                self.values[key][control] += entry.size

    def writeOutput(self):
        self.dump_arff(open(
            self.config.get('CuentaBytes', 'salida'),'w'))

    def dump_arff(self,of):
        of.write("@RELATION    cuentabytes\n")
        of.write("\n")
        of.write("@ATTRIBUTE    client    string\n")
        self.dump_categories_names(of)
        of.write("\n")
        of.write("@DATA\n")
        for k,v in self.values.iteritems():
            res = ''
            for item in v:
                res += repr(item) + ","
            of.write("{0},{1}\n".format(repr(k), res[:-1]))

    def dump_categories_names(self, of):
        for cat in self.site_list:
            of.write("@ATTRIBUTE    {0}    numeric\n".format(cat))
