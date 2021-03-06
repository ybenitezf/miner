# encoding: utf-8
from ConfigParser import ConfigParser
from datetime import datetime
from urlparse import urlsplit
import apachelog

import os
import os.path
from core.plugs import PluginMount
import sys

class LogEntry(object):
    """
    Representa una entrada de archivo de log, para cada tipo de log se tendrá
    una clase que hereda de esta.
    
    atributos:
    
    raw (str): linea de texto de la entrada exactamente como se leyo del log
    offset (int): indice dentro del archivo de texto en que se encontro la 
                  entrada
    """
    def __init__(self, line, offset):
        super(LogEntry, self).__init__()
        self.raw = line
        self.offset = offset

    def get_raw(self):
        """Retorna la entrada exactamente como se leyo desde el log"""
        return self.raw

    @staticmethod
    def build_entry(line, offset):
        """Factoria para entradas de log"""
        parts = line.split()
        squid_log = False
        
        entry = None
        # para debug
        import traceback
#         exc_info = sys.exc_info()
        # ----------
        
        import socket
        try:
            addr = socket.inet_aton(parts[1])
            assert parts[1] == socket.inet_ntoa(addr)
        except socket.error, e:
            # squid access log
            squid_log = True
        except AssertionError:
            squid_log = True    

        try:
            if squid_log:
                # intentar construir un SQUIDLogEntry
                entry = SQUIDLogEntry(line, offset)
            else:
                # intentar construir un CommonLogEntry
                entry = CommonLogEntry(line, offset)
        except Exception, e:
            # sin ocurre un error, el que sea, retornar None
#             traceback.print_exc()
#             sys.exit(0)
            entry = None
        
        return entry

    def get_remote_host(self):
        """Retorna el nombre del host remoto

        En el caso de squid retorna el nombre del host remoto, en el caso de common log retorna
        el IP del cliente accediendo al sitio
        """
        raise NotImplementedError()

    def __str__(self):
        return self.get_raw().strip('\n')

    def __unicode__(self):
        return self.__str__()

class CommonLogEntry(LogEntry):
    """Common Log para apache y compañia
    
    
    atributos y propiedades:
    
    timeStamp (datetime): fecha y hora en que se proceso la petición
    clientIP: número IP del cliente
    action: acción/sección de la página visitada
    uri: url del recurso al que se accedio
    code: código HTTP de la respuesta
    size: tamaño del objeto retornado al usuario sin incluir las cabeceras
    userId: identificador del usuario o '-' en caso de que no se tenga
    """

    def __init__(self, line, offset):
        super(CommonLogEntry, self).__init__(line, offset)
        #self.values = p.parse(line)
        line = line.strip()
        self.values = dict(enumerate(line.split(" ")))
        self.timeElapsed = 0
        t = "{} {}".format(self.values[4], self.values[5])
        self.timeStamp = self.parse_date(t)
        self.clientIP = self.values[1]
        act = "{} {}".format(self.values[6], self.values[7])
        act = act.strip('"')
        if act != '-':
            act = act.split()
            self.action = act[0]
            self.uri = act[1]
        else:
            self.action, self.uri = (act, act)
        self.code = self.values[9]
        try:
            self.size = int(self.values[10])
        except:
            self.size = 0
        self.method = act[0]
        self.userId = self.values[2]
        self.heriarchy = '-'
        self.contentType = '-'

    def get_remote_host(self):
        return self.values[0].split(':')[0]

    def parse_date(self, t):
        date = t
        date = date[1:-1]
        return datetime(int(date[7:11]),
                        int(apachelog.months[date[3:6]]),
                        int(date[0:2]), int(date[12:14]),
                        int(date[15:17]), int(date[18:20]))

class SQUIDLogEntry(LogEntry):
    """Una estrada del access.log que genera squid"""

    def __init__(self, line, offset):
        super(SQUIDLogEntry, self).__init__(line, offset)
        line = line.strip('\n')
#         try:
        fields = line.split()
        self.timeStamp = datetime.fromtimestamp(float(fields[0]))
        self.timeElapsed = float(fields[1])
        self.clientIP = fields[2]
        action, code = fields[3].split('/')
        self.action = action
        self.code = code
        self.size = float(fields[4])
        self.method = fields[5]
        self.uri = fields[6]
            # self.userId = self.clientIP if fields[7] == "-" else fields[7]
        self.userId = fields[7]
        self.heriarchy = fields[8]
        self.contentType = fields[9]
#         except Exception:
#             print e
#             print "Raw: ", line
#             sys.exit()
#             return None

    def get_remote_host(self):
        """Extrae el nombre del servidor remoto"""
        if self.method == 'CONNECT':
            # if the method is connect this field not have a valid
            # URI.
            return self.uri.split(':')[0]
        else:
            r = urlsplit(self.uri)
            # in some cases when it come as hostname:port
            # urlsplit fail, this solve it
            return r.netloc.split(':')[0]


class LogObserverPlugin(object):
    """Observador de log, será notificado cuando se lea una entrada del log y es la clase base
    para los plugins de Miner, vease reporter.py en la carpeta plugins para ejemplo

    Todos los objetos deben implementar notificar() y writeOutput()
    """

    __metaclass__ = PluginMount

    def __init__(self, parser=None, config=None):
        assert isinstance(parser, Parser)
        assert isinstance(config, ConfigParser)
        super(LogObserverPlugin, self).__init__()
        self.actions = ['TCP_MISS', 'TCP_REFRESH_MISS',
                        'TCP_CLIENT_REFRESH', 'TCP_CLIENT_REFRESH_MISS',
                        ]
        parser.add_observer(self)
        self.config = config

    def notificar(self, entry):
        assert NotImplementedError()


    def writeOutput(self):
        assert NotImplementedError()


class Parser(object):
    lfn = None
    observers = []

    def __init__(self, log_file_name):
        super(Parser, self).__init__()
        self.lfn = log_file_name
        self.log_list = []

    def build_log_list(self):
        """Si es un directorio entonces construye una lista con lo archivos de log dentro de este"""
        for item in os.walk(self.lfn):
            (dirpath, dirnames, filenames) = item
            for log in filenames:
                if 'log' in log:
                    self.log_list.append(os.path.join(dirpath, log))

    def add_observer(self, observer):
        """Registrar observador"""
        assert isinstance(observer, LogObserverPlugin)
        self.observers.append(observer)

    def notificar_observadores(self, entry):
        """Notificar a cada uno de los observadores"""
        for observer in self.observers:
            observer.notificar(entry)

    def parse(self):
        """Parsea el log de squid y notifica a los observadores"""
        if os.path.isdir(self.lfn):
            self.build_log_list()
            for item in self.log_list:
                print "\nParsing log: {0}".format(item)
                log = open(item, 'r')
                for line in log:
                    entry = LogEntry.build_entry(line, 0)
                    self.notificar_observadores(entry)
                print "\nTask done !"
        else:
            log = open(self.lfn, 'r')
            print "\nParsing log: {0}".format(self.lfn)
            for line in log:
                entry = LogEntry.build_entry(line, 0)
                self.notificar_observadores(entry)
            print "\nTask done !"
