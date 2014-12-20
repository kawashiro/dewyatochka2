# -*- coding: UTF-8

"""
Dewyatochka daemon application
"""

__all__ = ['Application']

import time
from dewyatochka.core.application import Application as BaseApplication
from dewyatochka.core.config import GlobalConfig, ConferenceConfig
from dewyatochka.core import conference, plugin, log


class Application(BaseApplication):
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

    def _init_logger(self):
        """
        Init logger instance
        :return:
        """
        self.set_log_handler(log.ConsoleHandler(self))

    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        try:
            self._init_config(args[1] if len(args) > 1 else GlobalConfig.DEFAULT_FILE_PATH)
            self._init_logger()

            plugin.load_plugins()

            conf_manager = conference.ConferenceManager(self)
            conf_manager.start()

            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.log(__name__).info('Terminated by user, exiting')
            self.stop()
