# -*- coding: UTF-8

""" Jabber bot

Classes
=======
    Bot -- Jabber bot service implementation
"""

__all__ = ['Bot']

import threading

from dewyatochka.core.application import Application, Service
from dewyatochka.core.network.xmpp.entity import Message


class Bot(Service):
    """ Jabber bot service implementation """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._reader_thread = threading.Thread(name=self.name() + '[Reader]', target=self._read)
        self._monitor_thread = threading.Thread(name=self.name() + '[Monitor]', target=self._monitor)

    def _monitor(self):
        """ Monitor app state

        :return None:
        """
        try:
            self.application.registry.xmpp.connect()
            self._reader_thread.start()
            self.application.wait()
            self.application.registry.xmpp.disconnect()
        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _read(self):
        """ Run process

        :return None:
        """
        try:
            xmpp_connection = self.application.registry.xmpp

            for message in xmpp_connection.input_stream:
                self.log.debug('Received a message from %s <<< %s >>>', message.sender, str(message))
                self._start_message_processing(message)
        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _start_message_processing(self, message: Message):
        """ Start message processing

        :param Message message:
        :return None:
        """
        message_plugins = self.application.registry.chat.plugins

        for plugin in message_plugins:
            self.log.debug('Passing message processing to a plugin %s', plugin)
            threading.Thread(
                name='%s[Worker][%d]' % (plugin, hash(repr(message))),
                target=plugin,
                kwargs={'logger': self.log, 'message': message},
                daemon=True
            ).start()

    def start(self):
        """ Start thread

        :return None:
        """
        self._monitor_thread.start()

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        for thread in self._reader_thread, self._monitor_thread:
            if thread.is_alive():
                self.log.debug('Waiting for thread "%s"', thread.name)
                thread.join()

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'bot'
