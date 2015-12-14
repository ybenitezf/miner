# -*- coding: utf-8 -*-

__author__ = 'Yoel Benítez Fonseca <ybenitezf@gmail.com>'

class PluginMount(type):
    """Metaclass or class template, this is a minimal plugin framework

    thanks to http://martyalchin.com/2008/jan/10/simple-plugin-framework/
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)

    def get_plugins(self, *args, **kwargs):
        return [p(*args,**kwargs) for p in self.plugins]
