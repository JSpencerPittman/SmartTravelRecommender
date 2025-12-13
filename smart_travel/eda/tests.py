from django.test import TestCase
from .event_dispatcher import EventDispatcher, EmittedEvent


class EventDispatcherTests(TestCase):
    def setUp(self):
        self.dispatcher = EventDispatcher()

    def test_subscribe_to_event(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.assertIn('TEST_EVENT', self.dispatcher._subscriptions)
        self.assertIn('subscriber1', self.dispatcher._subscriptions['TEST_EVENT'])
        self.assertIn('subscriber1', self.dispatcher._subscribers)

    def test_subscribe_multiple_subscribers(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.subscribe('subscriber2', 'TEST_EVENT')

        self.assertEqual(len(self.dispatcher._subscriptions['TEST_EVENT']), 2)
        self.assertIn('subscriber1', self.dispatcher._subscriptions['TEST_EVENT'])
        self.assertIn('subscriber2', self.dispatcher._subscriptions['TEST_EVENT'])

    def test_subscribe_same_subscriber_multiple_times(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')

        self.assertEqual(len(self.dispatcher._subscriptions['TEST_EVENT']), 1)

    def test_subscribe_to_multiple_events(self):
        self.dispatcher.subscribe('subscriber1', 'EVENT1')
        self.dispatcher.subscribe('subscriber1', 'EVENT2')

        self.assertIn('EVENT1', self.dispatcher._subscriptions)
        self.assertIn('EVENT2', self.dispatcher._subscriptions)
        self.assertIn('subscriber1', self.dispatcher._subscriptions['EVENT1'])
        self.assertIn('subscriber1', self.dispatcher._subscriptions['EVENT2'])

    def test_unsubscribe_from_event(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.subscribe('subscriber2', 'TEST_EVENT')

        self.dispatcher.unsuscribe('subscriber1', 'TEST_EVENT')

        self.assertEqual(len(self.dispatcher._subscriptions['TEST_EVENT']), 1)
        self.assertNotIn('subscriber1', self.dispatcher._subscriptions['TEST_EVENT'])
        self.assertIn('subscriber2', self.dispatcher._subscriptions['TEST_EVENT'])

    def test_publish_event(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')

        event_data = {'key': 'value'}
        self.dispatcher.publish('TEST_EVENT', event_data)

        event = self.dispatcher.get_event('subscriber1')
        self.assertIsNotNone(event)
        self.assertEqual(event['name'], 'TEST_EVENT')
        self.assertEqual(event['data'], event_data)

    def test_publish_event_to_multiple_subscribers(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.subscribe('subscriber2', 'TEST_EVENT')

        event_data = {'message': 'Hello'}
        self.dispatcher.publish('TEST_EVENT', event_data)

        event1 = self.dispatcher.get_event('subscriber1')
        event2 = self.dispatcher.get_event('subscriber2')

        self.assertIsNotNone(event1)
        self.assertIsNotNone(event2)
        self.assertEqual(event1['name'], 'TEST_EVENT')
        self.assertEqual(event2['name'], 'TEST_EVENT')
        self.assertEqual(event1['data'], event_data)
        self.assertEqual(event2['data'], event_data)

    def test_publish_nonexistent_event(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.publish('NONEXISTENT_EVENT', {})

        event = self.dispatcher.get_event('subscriber1')
        self.assertIsNone(event)

    def test_get_event_empty_queue(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')

        event = self.dispatcher.get_event('subscriber1')
        self.assertIsNone(event)

    def test_get_event_nonexistent_subscriber(self):
        event = self.dispatcher.get_event('nonexistent')
        self.assertIsNone(event)

    def test_get_event_order(self):
        self.dispatcher.subscribe('subscriber1', 'EVENT1')
        self.dispatcher.subscribe('subscriber1', 'EVENT2')

        self.dispatcher.publish('EVENT1', {'num': 1})
        self.dispatcher.publish('EVENT2', {'num': 2})

        event1 = self.dispatcher.get_event('subscriber1')
        event2 = self.dispatcher.get_event('subscriber1')

        self.assertEqual(event1['name'], 'EVENT1')
        self.assertEqual(event1['data']['num'], 1)
        self.assertEqual(event2['name'], 'EVENT2')
        self.assertEqual(event2['data']['num'], 2)

    def test_publish_with_empty_data(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')
        self.dispatcher.publish('TEST_EVENT')

        event = self.dispatcher.get_event('subscriber1')
        self.assertIsNotNone(event)
        self.assertEqual(event['name'], 'TEST_EVENT')
        self.assertEqual(event['data'], {})

    def test_multiple_events_in_queue(self):
        self.dispatcher.subscribe('subscriber1', 'TEST_EVENT')

        self.dispatcher.publish('TEST_EVENT', {'count': 1})
        self.dispatcher.publish('TEST_EVENT', {'count': 2})
        self.dispatcher.publish('TEST_EVENT', {'count': 3})

        event1 = self.dispatcher.get_event('subscriber1')
        event2 = self.dispatcher.get_event('subscriber1')
        event3 = self.dispatcher.get_event('subscriber1')

        self.assertEqual(event1['data']['count'], 1)
        self.assertEqual(event2['data']['count'], 2)
        self.assertEqual(event3['data']['count'], 3)

        event4 = self.dispatcher.get_event('subscriber1')
        self.assertIsNone(event4)
