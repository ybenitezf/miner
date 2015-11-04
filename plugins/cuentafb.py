# coding: utf-8
__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'

__doc__ = """Cuenta la cantidad veces que un usuario entra en facebook e 
imprime en la consola al final de la ejecución de miner esa lista"""

from parser.logParser import LogObserverPlugin, SQUIDLogEntry, CommonLogEntry

class CuentaFB(LogObserverPlugin):

    def __init__(self, *args, **kwargs):
        super(CuentaFB, self).__init__(*args, **kwargs)
        # iniciar un diccionario
        self.data = dict()

    def notificar(self, entry):
        if isinstance(entry, SQUIDLogEntry):
            # si la entrada es de un access.log de squid
            if entry.userId != '-':
                # si el usuario se ha definido
                remoto = entry.get_remote_host()
                if remoto.find('facebook.com') >= 0:
                    # debemos contar esta entrada
                    if self.data.has_key(entry.userId):
                        self.data[entry.userId] += 1
                    else:
                        self.data[entry.userId] = 1
    
    def writeOutput(self):
        for usuario in self.data.keys():
            print "{0}, {1}".format(usuario, self.data[usuario])
