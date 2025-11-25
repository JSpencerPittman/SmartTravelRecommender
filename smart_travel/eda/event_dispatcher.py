from typing import Callable, Optional
import threading


class EventDispatcher(object):
    def __init__(self):
        self._subscriptions = dict()

    def register_subscriber(self, event: str, callback: Callable[..., None]):
        if event in self._subscriptions:
            self._subscriptions[event].append(callback)
        else:
            self._subscriptions[event] = [callback]

    def publish_event(self, event: str, event_data: Optional[dict] = None):
        if event in self._subscriptions:
            for subscriber in self._subscriptions[event]:
                thread = threading.Thread(
                    target=subscriber, args=(event_data,), daemon=True
                )
                thread.start()


_dispatcher = EventDispatcher()


def register_subscriber(event_name: str, subscriber: Callable[..., None]):
    _dispatcher.register_subscriber(event_name, subscriber)


def publish_event(event_name: str, event_data: Optional[dict] = None):
    _dispatcher.publish_event(event_name, event_data)
