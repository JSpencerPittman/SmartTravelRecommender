from queue import Queue
from typing import TypedDict, Optional


class EmittedEvent(TypedDict):
    name: str
    data: dict


class EventDispatcher(object):
    def __init__(self):
        self._subscriptions = dict()  # Event -> Subscriber
        self._subscribers = {}  # Subscriber -> Queue

    def subscribe(
        self,
        name: str,
        event: str,
    ):
        if event in self._subscriptions:
            if name not in self._subscriptions[event]:
                self._subscriptions[event].append(name)
        else:
            self._subscriptions[event] = [name]

        if name not in self._subscribers:
            self._subscribers[name] = Queue()

    def unsuscribe(self, name: str, event: str):
        if event in self._subscriptions:
            for idx, subscriber in enumerate(self._subscriptions[event]):
                if subscriber == name:
                    self._subscriptions[event].pop(idx)
                    break

    def publish(self, event: str, data: dict = {}):
        if event in self._subscriptions:
            for subscriber in self._subscriptions[event]:
                self._subscribers[subscriber].put(EmittedEvent(name=event, data=data))

    def get_event(self, name: str) -> Optional[EmittedEvent]:
        if name in self._subscribers and not self._subscribers[name].empty():
            return self._subscribers[name].get()
        return None


_dispatcher = EventDispatcher()


def subscribe(name: str, event: str):
    return _dispatcher.subscribe(name, event)


def unsuscribe(name: str, event: str):
    return _dispatcher.subscribe(name, event)


def publish(event_name: str, data: dict = {}):
    _dispatcher.publish(event_name, data)


def get_event(name: str) -> Optional[EmittedEvent]:
    return _dispatcher.get_event(name)
