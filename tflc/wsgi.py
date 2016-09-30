__author__ = 'Zhang Shaojun'
"""
modified according to ryu~
thanks!
"""

import inspect
import webob.dec
from routes import Mapper
from routes.util import URLGenerator
import hub
import cfg


def route(name, path, methods=None, requirements=None):
    def _route(controller_method):
        controller_method.routing_info = {
            'name': name,
            'path': path,
            'methods': methods,
            'requirements': requirements,
        }
        return controller_method
    return _route

class ControllerBase(object):
    special_vars = ['action', 'controller']

    def __init__(self, req, link, data, **config):
        self.req = req
        self.link = link
        self.parent = None
        for name, value in config.items():
            setattr(self, name, value)

    def __call__(self, req):
        action = self.req.urlvars.get('action', 'index')
        if hasattr(self, '__before__'):
            self.__before__()

        kwargs = self.req.urlvars.copy()
        for attr in self.special_vars:
            if attr in kwargs:
                del kwargs[attr]

        return getattr(self, action)(req, **kwargs)

class wsgify_hack(webob.dec.wsgify):
    def __call__(self, environ, start_response):
        self.kwargs['start_response'] = start_response
        return super(wsgify_hack, self).__call__(environ, start_response)


class WebSocketManager(object):

    def __init__(self):
        self._connections = []

    def add_connection(self, ws):
        self._connections.append(ws)

    def delete_connection(self, ws):
        self._connections.remove(ws)

    def broadcast(self, msg):
        for connection in self._connections:
            connection.send(msg)


class WSGIApplication(object):
    def __init__(self, **config):
        self.config = config
        self.mapper = Mapper()
        self.registory = {}
        self._wsmanager = WebSocketManager()
        super(WSGIApplication, self).__init__()
        # XXX: Switch how to call the API of Routes for every version
        match_argspec = inspect.getargspec(self.mapper.match)
        if 'environ' in match_argspec.args:
            # New API
            self._match = self._match_with_environ
        else:
            # Old API
            self._match = self._match_with_path_info

    def _match_with_environ(self, req):
        match = self.mapper.match(environ=req.environ)
        return match

    def _match_with_path_info(self, req):
        self.mapper.environ = req.environ
        match = self.mapper.match(req.path_info)
        return match

    @wsgify_hack
    def __call__(self, req, start_response):
        match = self._match(req)

        if not match:
            return webob.exc.HTTPNotFound()

        req.start_response = start_response
        req.urlvars = match
        link = URLGenerator(self.mapper, req.environ)

        data = None
        name = match['controller'].__name__
        if name in self.registory:
            data = self.registory[name]

        controller = match['controller'](req, link, data, **self.config)
        controller.parent = self
        return controller(req)

    def register(self, controller, data=None):
        methods = inspect.getmembers(controller,
                                     lambda v: inspect.ismethod(v) and
                                     hasattr(v, 'routing_info'))
        for method_name, method in methods:
            routing_info = getattr(method, 'routing_info')
            name = routing_info['name']
            path = routing_info['path']
            conditions = {}
            if routing_info.get('methods'):
                conditions['method'] = routing_info['methods']
            requirements = routing_info.get('requirements') or {}
            self.mapper.connect(name,
                                path,
                                controller=controller,
                                requirements=requirements,
                                action=method_name,
                                conditions=conditions)
        if data:
            self.registory[controller.__name__] = data

    @property
    def websocketmanager(self):
        return self._wsmanager


class WSGIServer(hub.WSGIServer):
    def __init__(self, application, **config):
        super(WSGIServer, self).__init__((cfg.WSGI_API_HOST, cfg.WSGI_API_PORT),
                                         application, **config)

    def __call__(self):
        self.serve_forever()


def start_service(app_mgr):
    for instance in app_mgr.contexts.values():
        if instance.__class__ == WSGIApplication:
            return WSGIServer(instance)

    return None
