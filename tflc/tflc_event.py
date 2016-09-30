__author__ = 'Zhang Shaojun'

# basic event, other events are derived from this class
class EventTFLCPMsgBase(object):
    def __init__(self, msg=None):
        super(EventTFLCPMsgBase, self).__init__()
        self.msg = msg

# Message Event Definition
# only uplink message generate Events
class EventTFLCPHelloUp(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPHelloUp, self).__init__(msg)

class EventTFLCPDPConnected(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPDPConnected, self).__init__(msg)

class EventTFLCPGidRequest(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPGidRequest, self).__init__(msg)

class EventTFLCPPacketIn(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPPacketIn, self).__init__(msg)

class EventTFLCPLoadReport(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPLoadReport, self).__init__(msg)

class EventTFLCPRoleNotify(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPRoleNotify, self).__init__(msg)

class EventTFLCPEchoReply(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPEchoReply, self).__init__(msg)

class EventTFLCPError(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPError, self).__init__(msg)

class EventTFLCPBarrierReply(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPBarrierReply, self).__init__(msg)

class EventTFLCPHostConnected(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPHostConnected, self).__init__(msg)

class EventTFLCPDatapathLeave(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPDatapathLeave, self).__init__(msg)

class EventTFLCPHostLeave(EventTFLCPMsgBase):
    def __init__(self, msg):
        super(EventTFLCPHostLeave, self).__init__(msg)

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
            print "tflc_event: add_event_listener " + listener.__name__ + " to " + event_cls.__name__

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
