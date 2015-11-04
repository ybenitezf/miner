# coding: utf-8
__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'

from parser.logParser import LogObserverPlugin, LogEntry
import sys

class ReporterObserver(LogObserverPlugin):

    def __init__(self, *args, **kwargs):
        super(ReporterObserver, self).__init__(*args, **kwargs)
        self.bytes = 0
        self.count = 0

    def notificar(self, entry):
        """
        Muestra el reporte de bytes leidos de los logs
        """
        if isinstance(entry, LogEntry):
            if self.count >= 1024:
                self.count = 0
                stat = float(self.bytes) / float(1024) # KB
                suf = 'KB'
                if stat > 1024:
                    # esta en
                    stat = float(stat) / float(1024) # MB
                    suf = 'MB'
                if stat > 1024:
                    stat = float(stat) / float(1024) # GB
                    suf = 'GB'
                out = "Log parsed: {0:.2f} {1}".format(stat, suf)
                sys.stdout.write("\r%s                   " % out)
                sys.stdout.flush()
            self.bytes += len(entry.get_raw())
            self.count += 1

    def writeOutput(self):
        pass
