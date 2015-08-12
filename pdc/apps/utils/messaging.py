#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class DummyMessenger(object):
    def __init__(self):
        pass

    def send_message(self, topic, msg):
        pass


class KombuMessenger(object):
    def __init__(self):
        from kombu import Connection, Exchange
        self.conn = Connection(settings.MESSAGE_BUS['URL'],
                               **settings.MESSAGE_BUS.get('OPTIONS', {}))
        self.exchange = Exchange(**settings.MESSAGE_BUS['EXCHANGE'])
        self.messenger = self.conn.Producer()

    def send_message(self, topic, msg):
        self.messenger.publish(msg, exchange=self.exchange, routing_key=topic)


class FedmsgMessenger(object):
    def __init__(self):
        import fedmsg
        self.messenger = fedmsg

    def send_message(self, topic, msg):
        self.messenger.publish(topic=topic, msg=msg)


class ProtonMessenger(object):
    def __init__(self):
        import proton
        self.messenger = proton.Messenger()
        self.messenger.certificate = settings.MESSAGE_BUS['CERT_FILE']
        self.messenger.private_key = settings.MESSAGE_BUS['KEY_FILE']
        self.messenger.start()
        self.message = proton.Message()

    def send_message(self, topic, msg):
        self.message.address = settings.MESSAGE_BUS['URL'] + topic
        self.message.body = msg
        self.messenger.put(self.message)
        self.messenger.send()


class QpidMessenger(object):
    def __init__(self):
        from qpid.messaging import Connection, Message
        from . import transports  # noqa
        self.message_cls = Message
        self.messaging_except_cls = Message
        self.connection = Connection(url=settings.MESSAGE_BUS['ENDPOINTS'][0],
                                     reconnect=True,
                                     socket_timeout=settings.MESSAGE_BUS['SOCKET_TIMEOUT'],
                                     reconnect_timeout=settings.MESSAGE_BUS['CONN_TIMEOUT'],
                                     reconnect_urls=settings.MESSAGE_BUS['ENDPOINTS'],
                                     ssl_certfile=settings.MESSAGE_BUS['CERT_FILE'],
                                     ssl_keyfile=settings.MESSAGE_BUS['KEY_FILE'])

    def send_message(self, topic, msg):
        address = settings.MESSAGE_BUS['QUEUE'] + str(topic)
        message = self.message_cls(msg)
        try:
            self.connection.open()
            session = self.connection.session()
            self.sender = session.sender(address)
            self.sender.send(message, timeout=settings.MESSAGE_BUS['SEND_TIMEOUT'])
        except Exception, e:
            if self.connection.opened():
                self.connection.close()
            if not self.connection.reconnect:
                self.connection.reconnect = True
            logger.warn('Send Message exception: %s.' % str(e))
