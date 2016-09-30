__author__ = 'Zhang Shaojun'

# basic event, other events are derived from this class
class EventTFLCPMsgBase(object):
    def __init__(self, msg=None):
        super(EventTFLCPMsgBase, self).__init__()
        self.msg = msg

# Message Event Definition
# only down message generate Events
class EventTFLCPHelloDown(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPHelloDown, self).__init__(msg)

class EventTFLCPRoleAssign(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPRoleAssign, self).__init__(msg)

class EventTFLCPGidReply(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPGidReply, self).__init__(msg)

class EventTFLCPFlowMod(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPFlowMod, self).__init__(msg)

class EventTFLCPDpMigration(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPDpMigration, self).__init__(msg)

class EventTFLCPCtrlPoolChange(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPCtrlPoolChange, self).__init__(msg)

class EventTFLCPEchoRequest(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPEchoRequest, self).__init__(msg)

class EventTFLCPBarrierRequest(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPBarrierRequest, self).__init__(msg)

# event dispatcher class
# use event class as key
# in dispatch_event(), the event is an event object
class EventDispatcher(object):
    def __init__(self):
        self._events = dict()

    def __del__(self):
        """
        empty the _events dict
        """
        self._events = None

    def has_listener(self, event_cls, listener):
        """
        return true if listener is register to ev_type
        """
        if event_cls in self._events.keys():
            return listener in self._events[event_cls]
        else:
            return False

    def dispatch_event(self, event):
        """
        dispatch an instance of Event class
        """
        if event.__class__ in self._events.keys():
            listeners = self._events[event.__class__]
            for listener in listeners:
                listener(event)

    def add_event_listener(self, event_cls, listener):
        """
        add an event listener for an event type
        """
        if not self.has_listener(event_cls, listener):
            listeners = self._events.get(event_cls, [])
            listeners.append(listener)
            self._events[event_cls] = listeners

    def rmv_event_listener(self, event_cls, listener):
        """
        remove the listener from the event type
        """
        if self.has_listener(event_cls, listener):
            listeners = self._events[event_cls]
            if len(listeners) == 1:
                del self._events[event_cls]
            else:
                listeners.remove(listener)
                self._events[event_cls] = listeners
