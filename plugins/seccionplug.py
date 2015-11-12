# coding: utf-8
__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'

__doc__ = """
SeccionPluggin es un plugin para miner que contabiliza los accesos a 
determinado sitio web usando las entradas en formato CommonLogEntry para
producir un archivo de datos en formato ARFF de la forma:

 usuario, seccion1, sección2, seccion3, ..., seccionn
 
 donde:
 
    usuario: ip del cliente
    seccionk: cantidad de accesos por el usuario en esa sección del sitio web
    
para activar este plugin debe agregarse 'seccionplug' a la lista de plugins 
activos en miner en config.ini.

Configuración
================================================================================
El archivo de configuración debe tener una sección con el nombre SeccionPluggin 
y en esta debe aparecer:

[SeccionPluggin]
secciones=lista_secciones.txt
salida=seccionpluggin.arff

donde:

    secciones - es el nombre del archivo con la lista de las secciones a tener
                en cuenta en el analisis, una por linea, por ejemplo:
                
                /node/add/galeria
                /redaccion/fotos
                
    salida - nombre del archivo de salida

"""

from parser.logParser import LogObserverPlugin, CommonLogEntry
import sys
import os.path

class SeccionPluggin(LogObserverPlugin):
    
    def __init__(self, *args, **kwargs):
        super(SeccionPluggin, self).__init__(*args, **kwargs)
        self.configurado = True
        self.valores = dict()
        try:
            data_dir = self.config.get('main', 'data_dir')
            data_dir = os.path.join(data_dir, 'SeccionPluggin')
            lista_secciones = self.config.get('SeccionPluggin', 'secciones')
            lista_secciones = os.path.join(data_dir, lista_secciones)
            self.secciones = []
            for s in open(lista_secciones, 'r'):
                v = s.strip('\n\r ')
                if v != '':
                    self.secciones.append(v)
        except:
            self.configurado = False
        
    def notificar(self, entry):
        if isinstance(entry, CommonLogEntry) and self.configurado:
            key = entry.clientIP
            if not self.valores.has_key(key):
                self.valores[key] = [0 for i in self.secciones]
            
            for index, item in enumerate(self.secciones):
                if self.secciones[index] in entry.uri:
                    self.valores[key][index] += 1
        
    def writeOutput(self):
        if self.configurado:
            self.dump_arff(open(
                self.config.get('SeccionPluggin', 'salida'),'w'))

    def dump_arff(self,of):
        of.write("@RELATION    seccionpluggin\n")
        of.write("\n")
        of.write("@ATTRIBUTE    client    string\n")
        self.nombres_secciones(of)
        of.write("\n")
        of.write("@DATA\n")
        for k,v in self.valores.iteritems():
            res = ''
            for item in v:
                res += repr(item) + ","
            of.write("{0},{1}\n".format(repr(k), res[:-1]))

    def nombres_secciones(self, of):
        for s in self.secciones:
            of.write("@ATTRIBUTE    {0}    integer\n".format(s))
