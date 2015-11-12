# coding: utf-8
__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'

__doc__ = """
SerieTemporalPlug es un plugin para miner que contabiliza los accesos a 
determinado sitio web usando las entradas en formato CommonLogEntry para
producir un archivo de datos en formato ARFF de la forma:

 dia, seccion1, sección2, seccion3, ..., seccionn
 
 donde:
 
    dia: es el día del mes
    seccionk: cantidad de accesos por el día del mes en esa sección del sitio 
              web
    
para activar este plugin debe agregarse 'serietemporal' a la lista de plugins 
activos en miner en config.ini.

Configuración
================================================================================
El archivo de configuración debe tener una sección con el nombre SerieTemporalPlug 
y en esta debe aparecer:

[SerieTemporalPlug]
secciones=lista_secciones.txt
salida=serietemporal.arff

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

class SerieTemporalPlug(LogObserverPlugin):
    
    def __init__(self, *args, **kwargs):
        super(SerieTemporalPlug, self).__init__(*args, **kwargs)
        self.configurado = True
        self.valores = dict()
        try:
            # leer configuración e inicializar
            data_dir = self.config.get('main', 'data_dir')
            data_dir = os.path.join(data_dir, 'SerieTemporalPlug')
            lista_secciones = self.config.get('SerieTemporalPlug', 'secciones')
            lista_secciones = os.path.join(data_dir, lista_secciones)
            self.secciones = []
            for s in open(lista_secciones, 'r'):
                v = s.strip('\n\r ')
                if v != '':
                    self.secciones.append(v)
            # inicializar los vectores para cada día
            for dia in range(1, 32):
                self.valores[str(dia)] = [0 for i in self.secciones]
        except:
            # si esto pasa el plugin no esta configurado y no dara salida
            # ni procesará las entradas
            self.configurado = False
        
    def notificar(self, entry):
        if isinstance(entry, CommonLogEntry) and self.configurado:
            key = str(entry.timeStamp.day)
            
            for index, item in enumerate(self.secciones):
                if self.secciones[index] in entry.uri:
                    self.valores[key][index] += 1
        
    def writeOutput(self):
        if self.configurado:
            self.dump_arff(open(
                self.config.get('SerieTemporalPlug', 'salida'),'w'))

    def dump_arff(self,of):
        of.write("@RELATION    serietemporal\n")
        of.write("\n")
        of.write("@ATTRIBUTE    dia    integer\n")
        self.nombres_secciones(of)
        of.write("\n")
        of.write("@DATA\n")
        for dia in range(1, 32):
            k = str(dia)
            v = self.valores[k]
            res = ''
            for item in v:
                res += repr(item) + ","
            of.write("{0},{1}\n".format(dia, res[:-1]))

    def nombres_secciones(self, of):
        for s in self.secciones:
            of.write("@ATTRIBUTE    {0}    integer\n".format(s))
