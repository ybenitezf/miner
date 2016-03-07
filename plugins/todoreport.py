# coding: utf-8

from parser.logParser import LogObserverPlugin, SQUIDLogEntry
from core.pydal import DAL, Field
import sys
import os.path


class TodoReport(LogObserverPlugin):
    
    def __init__(self, *args, **kwargs):
        super(TodoReport, self).__init__(*args, **kwargs)
        self.configurado = True
        # tipos de contenido a tener en cuenta
        self.content_types_list = ['text/html']
        # lista de códigos de respuesta del servidor remoto a tener en cuenta
        self.return_codes = ['200']
        
        self.db = DAL('sqlite:memory')
        self.definir_tablas()
        
        try:
            # leer configuración e inicializar
            pass
        except:
            # si esto pasa el plugin no esta configurado y no dara salida
            # ni procesará las entradas
            self.configurado = False
        
        self.configurado = False if self.db is None else self.configurado
            
    def definir_tablas(self):
        db = self.db
        db.define_table("usuarios",
            Field("nombre", "string", length=50))
        
        db.define_table("sitio_usuario",
            Field("usuario_id", "reference usuarios"),
            Field("host", "string"),
            Field("bytes", "float"),
            Field("cantidad", "integer"))
            
    def notificar(self, entry):
        db = self.db

        if isinstance(entry, SQUIDLogEntry) and self.configurado:
            # procesar entradas del log de squid
            cond = (entry.contentType in self.content_types_list)
            cond = cond and (entry.code in self.return_codes)
            cond = cond and (entry.action in self.actions)
            if cond:
                usuario = db.usuarios(nombre=entry.userId)
                if usuario is None:
                    u_id = db.usuarios.insert(nombre=entry.userId)
                    usuario = db.usuarios(u_id)
                st_ur = db.sitio_usuario(usuario_id=usuario.id,
                                         host=entry.get_remote_host())
                if st_ur is None:
                    db.sitio_usuario.insert(usuario_id=usuario.id,
                                            host=entry.get_remote_host(),
                                            bytes=entry.size,
                                            cantidad=1)
                else:
                    st_ur.update_record(bytes=(st_ur.bytes + entry.size),
                                        cantidad=(st_ur.cantidad + 1))
                db.commit()
        
        
    def writeOutput(self):
        if self.configurado:
            self.dump_arff(open(
                self.config.get('TodoReport', 'salida'),'w'))
            
    def dump_arff(self,of):
        of.write("@RELATION    internet\n")
        of.write("\n")
        of.write("@ATTRIBUTE    usuario    string\n")
        self.nombres_secciones(of)
        of.write("\n")
        of.write("@DATA\n")
        db = self.db
        sitios = db(db.sitio_usuario.id > 0).select(db.sitio_usuario.host, distinct=True)
        for usuario in db(db.usuarios.id > 0).select():
            res = '{},'.format(repr(usuario.nombre))
            for sitio in sitios:
                st_ur = db.sitio_usuario(usuario_id=usuario.id,
                                         host=sitio.host)
                if st_ur is None:
                    res += "0,0,"
                else:
                    res += "{},{},".format(st_ur.bytes, st_ur.cantidad)
            of.write("{}\n".format(res[:-1]))
            

    def nombres_secciones(self, of):
        db = self.db
        query = (db.sitio_usuario.id > 0)
        for s in db(query).select(db.sitio_usuario.host, distinct=True):
            of.write("@ATTRIBUTE    {}_b    numeric\n".format(s.host))
            of.write("@ATTRIBUTE    {}_c    integer\n".format(s.host))