# coding: utf-8
from urlparse import urlparse
from parser.logParser import SQUIDLogEntry, CommonLogEntry, LogObserverPlugin
import os
import os.path
import sqlite3

class Category(object):
    def __init__(self, directory, name):
        super(Category, self).__init__()
        urls = os.path.join(directory, 'urls')
        if os.path.exists(urls):
            self.urls = urls
        else:
            self.urls = None
        domains = os.path.join(directory, 'domains')
        if os.path.exists(domains):
            self.domains = domains
        else:
            self.domains = None
        self.name = name
        self.cache = dict()

    def is_in(self, entry, db):
        result = False
        a_comparar = "esto no se encuentra nunca !!!"
        if isinstance(entry, SQUIDLogEntry):
            a_comparar = entry.get_remote_host()
        elif isinstance(entry, CommonLogEntry):
            r = urlparse(entry.uri)
            a_comparar = reduce(
                lambda x,y: x + y + '/', r.path.split('/')[:-1], ''
            )

        if a_comparar in self.cache.keys():
            return self.cache[a_comparar]

        result = self.internal_is_in(a_comparar,db=db)
        self.cache[a_comparar] = result
        return result

    def internal_is_in(self, a_comparar, db=None):
        """Search if entry match on urls or domains for this category"""
        assert isinstance(db, sqlite3.Connection)
        cur = db.cursor()
        try:
            results = cur.execute(
                '''SELECT id FROM Category WHERE name = ? AND content MATCH ?;
                ''', (self.name, a_comparar)
            )
        except sqlite3.OperationalError:
            # ignore this kind of errors, normally means the string
            # is to large for FTS to handle
            return False
        except Exception, e:
            print "Error: ", repr(e)
            print a_comparar
            print "-------------"
            cur.close()
            return False

        if results.fetchall():
            cur.close()
            return True

        cur.close()
        return False

    def load_to_database(self):
        dms = u''
        u = u''
        if self.domains:
            for line in open(self.domains, 'r'):
                try:
                    dms += unicode(line)
                except UnicodeDecodeError, e:
                    print "Domain error: {0}".format(line)
        if self.urls:
            for line in open(self.urls, 'r'):
                try:
                    u += unicode(line)
                except UnicodeDecodeError, e:
                    print "Url error: {0}".format(line)
        content = dms + u
        return content

class CategoryClassifier(LogObserverPlugin):
    """

    [CategoryClassifier]
    categorias=categorias
    output=categ.arff

    Donde:
        categorias - es el nombre de un directorio dentro del cual se tomaran
                    como categoria cada una de las carpetas dentro de este
        output - archivo de salida en formato ARFF
    """

    def __init__(self, *args, **kwargs):
        super(CategoryClassifier, self).__init__(*args, **kwargs)
        self.configurado = True
        try:
            self.categories = []
            classes_dir = self.config.get('CategoryClassifier', 'categorias')
            data_dir = self.config.get('main', 'data_dir')
            data_dir = os.path.join(data_dir, 'CategoryClassifier')
            classes_dir = os.path.join(data_dir, classes_dir)
            db_dir = os.path.join(data_dir, 'database.db')
            (dirpath, categories, filenames) = os.walk(classes_dir).next()
            # self.define_tables()
            for cat in categories:
                c = Category(os.path.join(dirpath, cat), cat)
                self.categories.append(c)
            # chequear BD
            if not os.path.exists(db_dir):
                self.build_database(db_dir)
            self.db = sqlite3.connect(db_dir)
            self.define_tables()
            self.vectors = dict()
        except Exception, e:
            self.configurado = False

    def define_tables(self):
        cur = self.db.cursor()
        cur.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS category USING fts4(
            id INTEGER PRIMARY KEY,
            name VARCHAR(20),
            content TEXT,
        );
        ''')
        self.db.commit()

    def clear_database(self):
        cur = self.db.cursor()
        cur.execute("TRUNCATE TABLE category;")
        self.db.commit()

    def build_database(self, db_dir):
        self.db = sqlite3.connect(db_dir)
        self.define_tables()
        cur=self.db.cursor()
        id=0
        for cat in self.categories:
            print "Dumping {0} into database.".format(cat.name)
            name=cat.name
            id += 1
            conent=cat.load_to_database()
            cur.execute('INSERT INTO category(id, name, content) VALUES(?,?,?)', (id,name, conent))
            self.db.commit()
            print "Done!."

    def notificar(self, entry):
        if isinstance(entry, SQUIDLogEntry) and self.configurado:
            if entry.action in self.actions:
                vector = self.do_classification(entry)
                if entry.userId in self.vectors.keys():
                    self.merge(self.vectors[entry.userId], vector)
                else:
                    self.vectors[entry.userId] = vector
        elif isinstance(entry, CommonLogEntry) and self.configurado:
            vector = self.do_classification(entry)
            if entry.clientIP in self.vectors.keys():
                self.merge(self.vectors[entry.clientIP], vector)
            else:
                self.vectors[entry.clientIP] = vector

    def merge(self, old, new):
        c = 0
        for item in old:
            if new[c] == 1:
                old[c] = 1
            else:
                old[c] = item
            c += 1

    def do_classification(self, entry):
        vector = []
        for cat in self.categories:
            if cat.is_in(entry, self.db):
                vector.append(1)
            else:
                vector.append(0)

        return vector

    def writeOutput(self):
        if self.configurado:
            self.dump_arff(open(
                self.config.get('CategoryClassifier', 'output'),'w'))

    def dump_arff(self,of):
        of.write("@RELATION    categoryclassifier\n")
        of.write("\n")
        of.write("@ATTRIBUTE    client    string\n")
        self.dump_categories_names(of)
        of.write("\n")
        of.write("@DATA\n")
        for k,v in self.vectors.iteritems():
            res = ''
            for item in v:
                res += repr(item) + ","
            of.write("{0},{1}\n".format(repr(k), res[:-1]))

    def dump_categories_names(self, of):
        for cat in self.categories:
            of.write("@ATTRIBUTE    {0}    integer\n".format(cat.name))
