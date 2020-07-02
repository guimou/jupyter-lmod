import json
import os

import lmod

from functools import partial, wraps

from tornado import web
from jupyter_core.paths import jupyter_path
from notebook.base.handlers import IPythonHandler

def jupyter_path_decorator(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        jpath_old = os.environ.get("JUPYTER_PATH")
        await func(self, *args, **kwargs)
        if jpath_old != os.environ.get("JUPYTER_PATH"):
            self.kernel_spec_manager.kernel_dirs = jupyter_path("kernels")
    return wrapper

class Lmod(IPythonHandler):
    @web.authenticated
    async def get(self):
        lang = self.get_query_argument(name="lang", default=None)
        if lang is None:
            result = await lmod.list()
        elif lang == "python":
            result = await lmod.freeze()
        else:
            raise web.HTTPError(400, u'Unknown value for lang argument')
        self.finish(json.dumps(result))

    @web.authenticated
    @jupyter_path_decorator
    async def post(self):
        modules = self.get_json_body().get('modules')
        if not modules:
            raise web.HTTPError(400, u'modules missing from body')
        elif not isinstance(modules, list):
            raise web.HTTPError(400, u'modules argument needs to be a list')
        await lmod.load(*modules)
        self.finish(json.dumps("SUCCESS"))

    @web.authenticated
    @jupyter_path_decorator
    async def delete(self):
        modules = self.get_json_body().get('modules')
        if not modules:
            raise web.HTTPError(400, u'modules missing from body')
        elif not isinstance(modules, list):
            raise web.HTTPError(400, u'modules argument needs to be a list')
        await lmod.unload(*modules)
        self.finish(json.dumps("SUCCESS"))

class LmodModules(IPythonHandler):
    @web.authenticated
    async def get(self):
        result = await lmod.avail()
        self.finish(json.dumps(result))

class LmodModule(IPythonHandler):
    @web.authenticated
    async def get(self, module=None):
        result = await lmod.show(module)
        self.finish(json.dumps(result))

class LmodCollections(IPythonHandler):
    @web.authenticated
    async def get(self):
        result = await lmod.savelist()
        self.finish(json.dumps(result))

    @web.authenticated
    async def post(self):
        name = self.get_json_body().get('name')
        if not name:
            raise web.HTTPError(400, u'name argument missing')
        await lmod.save(name)
        self.finish(json.dumps("SUCCESS"))

    @web.authenticated
    @jupyter_path_decorator
    async def patch(self):
        name = self.get_json_body().get('name')
        if not name:
            raise web.HTTPError(400, u'name argument missing')
        await lmod.restore(name)
        self.finish(json.dumps("SUCCESS"))

class LmodPath(IPythonHandler):
    pass

default_handlers = [
    (r"/lmod", Lmod),
    (r"/lmod/modules", LmodModules),
    (r"/lmod/modules/(.*)", LmodModule),
    (r"/lmod/collections", LmodCollections),
    (r"/lmod/path", LmodPath),
]
