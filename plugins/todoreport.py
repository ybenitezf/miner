# coding: utf-8

from parser.logParser import LogObserverPlugin, SQUIDLogEntry
from core.pydal import DAL, Field
import sys
import os.path

"""
Ejemplo de configuración:


[TodoReport]
salida=out.arff
sitios=sitios.txt
categorias=categorias
"""


class Category(object):
    def __init__(self, db, directory, name):
        self.db = db
        super(Category, self).__init__()
        urls = os.path.join(directory, 'urls')
        lista_domains = []
        lista_urls = []
        if os.path.exists(urls):
            for line in open(urls, 'r'):
                lista_urls.append(line.strip())
        domains = os.path.join(directory, 'domains')
        if os.path.exists(domains):
            for line in open(domains, 'r'):
                lista_domains.append(line.strip())
        self.name = name
        self.cache = dict()
        pk = db.categoria.insert(nombre=name,
                            dominios=lista_domains,
                            urls=lista_urls)
        db.commit()
        self.record = db.categoria(pk)


    def is_in(self, entry):
        for d in self.record.dominios:
            if d in entry.uri:
                return True
        for u in self.record.urls:
            if u in entry.uri:
                return True

        return False


class TodoReport(LogObserverPlugin):

    def __init__(self, *args, **kwargs):
        super(TodoReport, self).__init__(*args, **kwargs)
        self.configurado = True
        # tipos de contenido a tener en cuenta
        self.content_types_list = ['text/html']
        # lista de códigos de respuesta del servidor remoto a tener en cuenta
        self.return_codes = ['200']

        self.categorias = list()

        self.db = DAL('sqlite:memory')
        self.definir_tablas()

        try:
            # leer configuración e inicializar
            data_dir = self.config.get('main', 'data_dir')
            data_dir = os.path.join(data_dir, 'TodoReport')

            # intenta configurar la lista de sitios
            try:
                site_file = self.config.get('TodoReport', 'sitios')
                for l in open(os.path.join(data_dir, site_file), "r"):
                    l = l.strip('\n\r ')
                    if l:
                        self.db.sitios.insert(nombre_host=l)
                self.db.commit()
                self.usar_sitios = True
            except:
                self.usar_sitios = False

            # categorias
            #

            try:
                classes_dir = self.config.get('TodoReport', 'categorias')
                classes_dir = os.path.join(data_dir, classes_dir)
                (dirpath, categories, filenames) = os.walk(classes_dir).next()
                cats = list()
                for cat in categories:
                    c = Category(self.db, os.path.join(dirpath, cat), cat)
                    cats.append(c)

                self.categorias = cats
            except:
                pass


        except Exception, e:
            # si esto pasa el plugin no esta configurado y no dara salida
            # ni procesará las entradas
            self.configurado = False
            print e

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

        # categorias
        db.define_table("categoria",
                        Field("nombre", "string"),
                        Field("dominios", "list:string"),
                        Field("urls", "list:string"))
        db.define_table("usuario_categoria",
                        Field("usuario_id", "reference usuarios"),
                        Field("categoria_id", "reference categoria"))

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

                for categ in self.categorias:
                    if categ.is_in(entry):
                        c_u = db.usuario_categoria(usuario_id=usuario.id,
                                                   categoria_id=categ.record.id)
                        if c_u is None:
                            c_u = db.usuario_categoria.insert(usuario_id=usuario.id,
                                                   categoria_id=categ.record.id)

                db.commit()


    def writeOutput(self):
        if self.configurado:
            self.dump_arff(open(
                self.config.get('TodoReport', 'salida'),'w'))

    def dump_arff(self,of):
        db = self.db
        of.write("@RELATION    internet\n")
        of.write("\n")
        of.write("@ATTRIBUTE    usuario    string\n")
        self.nombres_secciones(of)
        of.write("@ATTRIBUTE    bytes    numeric\n")
        of.write("@ATTRIBUTE    cantidad    integer\n")
        of.write("@ATTRIBUTE    tiempo_proxy    numeric\n")
        for categ in self.categorias:
            of.write("@ATTRIBUTE    {}    integer\n".format(categ.name))
        of.write("\n")
        of.write("@DATA\n")
        sitios = db(db.sitio_usuario.id > 0).select(db.sitio_usuario.host, distinct=True)
        total = db(db.usuarios.id > 0).count()
        contador = 0
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
            res += "{},".format(segundos)

            for categ in self.categorias:
                c_u = db.usuario_categoria(usuario_id=usuario.id,
                                            categoria_id=categ.record.id)
                if c_u is None:
                    res += "0,"
                else:
                    res += "1,"

            of.write("{}\n".format(res[:-1]))
            stat = (contador * 100) / total
            out = "TodoReport: {0:.2f}".format(stat)
            sys.stdout.write("\r%s           " % out)
            sys.stdout.flush()
            contador += 1


    def nombres_secciones(self, of):
        db = self.db
        query = (db.sitio_usuario.id > 0)
        for s in db(query).select(db.sitio_usuario.host, distinct=True):
            of.write("@ATTRIBUTE    {}_b    numeric\n".format(s.host))
            of.write("@ATTRIBUTE    {}_c    integer\n".format(s.host))
