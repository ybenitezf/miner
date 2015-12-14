# coding: utf-8
'''
Este plugin genera una lista ordenada (por la cantidad de bytes descargados)
de los diferentes sitios que aparecen en los logs procesados por miner.

configuración de ejemplo

[ListaSitios]
salida=listado-sitios.txt

parametros:
    salida: nombre del archivo donde se pondrá la lista de sitios
    
En el archivo de salida se incluye un nombre de host, seguido de la cantidad
de bytes descargados, separados por una "," (coma)
'''
from parser.logParser import LogObserverPlugin, SQUIDLogEntry

class ListaSitios(LogObserverPlugin):
    
    def __init__(self, *args, **kwargs):
        super(ListaSitios, self).__init__(*args, **kwargs)
        self.data = dict()
        
    def notificar(self, entry):
        if isinstance(entry, SQUIDLogEntry):
            host = entry.get_remote_host()
            if self.data.has_key(host):
                self.data[host] += entry.size
            else:
                self.data[host] = entry.size
    
    def writeOutput(self):
        # poner los elementos de data en una lista, ordenarlos e imprimir
        # el resultado
        try:
            output = self.config.get('ListaSitios', 'salida')
        except:
            output = "lista_sitios.txt"
        lista = []
        for k, v in self.data.iteritems():
            lista.append((k, v))
        lista.sort(cmp=lambda x,y: cmp(x[1], y[1]), reverse=True)
        with open(output, "w") as out:
            for item in lista:
                out.write("{0},{1}\n".format(item[0],item[1]))