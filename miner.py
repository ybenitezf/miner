#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser
from parser.logParser import Parser, LogObserverPlugin
from os import path
from importlib import import_module
import sys

def import_plugins(plug_list):
    """
    Dada una lista de plugins para activar intenta importar los modulos correspondinetes
    desde la carpeta plugins
    """
    import_base = path.join(path.dirname(path.abspath(__file__)), 'plugins')
    sys.path.append(import_base)
    print "Cargando plugins:"
    for plug in plug_list:
        try:
            import_module(plug)
            print "{0}: OK".format(plug)
        except ImportError, e:
            print "{0}: ERR {1}".format(plug, e)


def main():
    config = ConfigParser()
    # leer archivo de configuración
    config.read('config.ini')
    # obtener lista de plugins
    p_list = config.get('main', 'plugins')
    p_list = p_list.split(',')
    # cargar los lugins
    import_plugins(p_list)
    # inicializar el parser
    par = Parser(config.get('main', 'logfile'))
    # incializar cada uno de los plugins
    plugs = LogObserverPlugin.get_plugins(parser=par, config=config)
    # inciar el procesamiento de los logs
    par.parse()
    # notificar a cada plugin para que escriba sus archivos de salida
    for p in plugs:
        p.writeOutput()
    return 0

if __name__ == '__main__':
    main()
