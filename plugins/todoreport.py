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
            data_dir = self.config.get('main', 'data_dir')
            m_path = os.path.join(data_dir, 'TodoReport')
            
            # intenta configurar la lista de sitios
            try:
                site_file = self.config.get('TodoReport', 'sitios')
                for l in open(os.path.join(m_path, site_file), "r"):
                    l = l.strip('\n\r ')
                    if l:
                        self.db.sitios.insert(nombre_host=l)
                self.db.commit()
                self.usar_sitios = True
            except:
                self.usar_sitios = False
                
            
        except:
            # si esto pasa el plugin no esta configurado y no dara salida
            # ni procesará las entradas
            self.configurado = False
        
        self.configurado = False if self.db is None else self.configurado
            
    def definir_tablas(self):
        db = self.db
        db.define_table("usuarios",
            Field("nombre", "string", length=50),)
        
        db.define_table("sitio_usuario",
            Field("usuario_id", "reference usuarios"),
            Field("host", "string"),
            Field("bytes", "float"),
            Field("cantidad", "integer"),
            Field("tiempo_proxy", "integer"))
        
        # sitios a tener en cuenta, si se configuran
        db.define_table("sitios",
            Field("nombre_host", "string"))
        
    def tiene_sitio(self, entry):
        assert isinstance(entry, SQUIDLogEntry)
        db = self.db
        query = (db.sitios.id > 0)
        
        for sitio in db(query).select(db.sitios.ALL):
            if sitio.nombre_host in entry.uri:
                return True
        
        return False
            
    def notificar(self, entry):
        db = self.db

        if isinstance(entry, SQUIDLogEntry) and self.configurado:
            # procesar entradas del log de squid
            cond = (entry.contentType in self.content_types_list)
            cond = cond and (entry.code in self.return_codes)
            cond = cond and (entry.action in self.actions)
            if cond and self.usar_sitios:
                cond = cond and self.tiene_sitio(entry)
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
                                            cantidad=1,
                                            tiempo_proxy=entry.timeElapsed)
                else:
                    st_ur.update_record(bytes=(st_ur.bytes + entry.size),
                                        cantidad=(st_ur.cantidad + 1),
                                        tiempo_proxy=(st_ur.tiempo_proxy + entry.timeElapsed))
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
        of.write("@ATTRIBUTE    bytes    numeric\n")
        of.write("@ATTRIBUTE    cantidad    integer\n")
        of.write("@ATTRIBUTE    tiempo_proxy    numeric\n")
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
            
            sum_bytes = db.sitio_usuario.bytes.sum()
            sum_cantidad = db.sitio_usuario.cantidad.sum()
            query  = (db.sitio_usuario.usuario_id == usuario.id)
            sum_bytes =  db(query).select(sum_bytes).first()[sum_bytes]
            sum_cantidad =  db(query).select(sum_cantidad).first()[sum_cantidad]
            res += "{},{},".format(sum_bytes, sum_cantidad)
            
            m_segundos = db.sitio_usuario.tiempo_proxy.sum()
            m_segundos = db(query).select(m_segundos).first()[m_segundos]
            segundos = m_segundos / 1000
            res += "{}".format(segundos)
            
            #of.write("{}\n".format(res[:-1]))
            of.write("{}\n".format(res))
            

    def nombres_secciones(self, of):
        db = self.db
        query = (db.sitio_usuario.id > 0)
        for s in db(query).select(db.sitio_usuario.host, distinct=True):
            of.write("@ATTRIBUTE    {}_b    numeric\n".format(s.host))
            of.write("@ATTRIBUTE    {}_c    integer\n".format(s.host))