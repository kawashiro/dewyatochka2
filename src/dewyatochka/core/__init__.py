# -*- coding: UTF-8

"""
Dewyatochka core package
"""

__all__ = ['application', 'conference', 'config', 'plugin', 'xmpp', 'DewyatochkaDaemon']

from dewyatochka.core.application import Application
from dewyatochka.core.config import GlobalConfig, ConferenceConfig
from dewyatochka.core import conference, plugin, log


class DewyatochkaDaemon(Application):
    """
    Dewyatochka daemon application
    """
    def _init_config(self, path):
        """
        Init config instance
        :return: void
        """
        config_container = GlobalConfig(self)
        config_container.reload(path)
        self.set_config(config_container)

        conf_config = ConferenceConfig(self)
        conf_config.reload(
            self.config.section('global').get('conferences_config', ConferenceConfig.DEFAULT_FILE_PATH)
        )
        self.set_conferences_config(conf_config)

    def _init_xmpp_worker(self):
        """
        Init xmpp worker thread
        :return: void
        """
        xmpp_worker = conference.Worker(self)
        self.set_xmpp_worker(xmpp_worker)

        self.set_conference_manager(conference.ConferenceManager(self))

    def _init_logger(self):
        """
        Init logger instance
        :return:
        """
        self.set_logger(log.Console(self))

    def _start(self):
        """
        Start threads
        :return: void
        """
        self.xmpp_worker.start()

    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        plugin.load_plugins()

        self._init_config(args[1] if len(args) > 1 else GlobalConfig.DEFAULT_FILE_PATH)
        self._init_xmpp_worker()

        self._start()
