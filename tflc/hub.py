__author__ = 'Zhang Shaojun'
"""
modified from ryu~
thanks
"""

import traceback
import eventlet
import eventlet.event
import eventlet.queue
import eventlet.semaphore
import eventlet.timeout
import eventlet.wsgi
import greenlet
from cfg import LOG

getcurrent = eventlet.getcurrent
patch = eventlet.monkey_patch
sleep = eventlet.sleep
listen = eventlet.listen
connect = eventlet.connect

def spawn(*args, **kwargs):
    def _launch(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except greenlet.GreenletExit:
            pass
        except:
            LOG.error('hub: uncaught exception: %s', traceback.format_exc())

    return eventlet.spawn(_launch, *args, **kwargs)

def spawn_after(seconds, *args, **kwargs):
    def _launch(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except greenlet.GreenletExit:
            pass
        except:
            LOG.error('hub: uncaught exception: %s', traceback.format_exc())

    return eventlet.spawn_after(seconds, _launch, *args, **kwargs)

def kill(thread):
    thread.kill()

def joinall(threads):
    for t in threads:
        try:
            t.wait()
        except greenlet.GreenletExit:
            pass

Queue = eventlet.queue.Queue
QueueEmpty = eventlet.queue.Empty
Semaphore = eventlet.semaphore.Semaphore
BoundedSemaphore = eventlet.semaphore.BoundedSemaphore
Timeout = eventlet.timeout.Timeout

class StreamServer(object):
    def __init__(self, listen_info, handle=None, spawn='default'):
        self.server = eventlet.listen(listen_info)
        self.handle = handle

    def serve_forever(self):
        while True:
            sock, addr = self.server.accept()
            spawn(self.handle, sock, addr)

class Event(object):
    def __init__(self):
        self._ev = eventlet.event.Event()
        self._cond = False

    def _wait(self, timeout=None):
        while not self._cond:
            self._ev.wait()

    def _broadcast(self):
        self._ev.send()
        self._ev = eventlet.event.Event()

    def is_set(self):
        return self._cond

    def set(self):
        self._cond = True
        self._broadcast()

    def clear(self):
        self._cond = False

    def wait(self, timeout=None):
        if timeout is None:
            self._wait()
        else:
            try:
                with Timeout(timeout):
                    self._wait()
            except Timeout:
                pass

        return self._cond


class LoggingWrapper(object):
    def write(self, message):
        LOG.info(message.rstrip('\n'))

class WSGIServer(StreamServer):
    def serve_forever(self):
        self.logger = LoggingWrapper()
        eventlet.wsgi.server(self.server, self.handle, self.logger)
