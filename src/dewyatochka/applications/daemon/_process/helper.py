# -*- coding: UTF-8

""" Helper threads management

Classes
=======
    HelpersManager -- Manages helper threads required by plugins
"""

__all__ = ['HelpersManager']

import threading

from dewyatochka.core.application import Service, Application
from dewyatochka.core.plugin.helper_sys.service import Environment


# Interval between helpers state checks
_PERSISTENT_HELPERS_CHECK_INTERVAL = 60


class HelpersManager(Service):
    """ Manages helper threads required by plugins """

    def __init__(self, application: Application):
        """ Initialize service & attach an application to it

        :param Application application:
        """
        super().__init__(application)

        self._thread = threading.Thread(name='%s[Worker]' % self.name(), target=self._run)

    def start(self):
        """ Start manager

        :return None:
        """
        self._thread.start()

    def wait(self):
        """ Wait until stopped

        :return None:
        """
        if self._thread.is_alive():
            self.log.debug('Waiting for thread "%s"', self._thread.name)
            self._thread.join()

    def _run(self):
        """ Perform helpers control

        :return None:
        """
        try:
            self._start_all()
            self._monitor()
        except Exception as e:
            self.application.fatal_error(__name__, e)

    def _start_all(self):
        """ Start all the helpers

        :return None:
        """
        for helper_env in self.application.registry.helper.plugins:
            self._start_helper(helper_env)

    def _monitor(self):
        """ Monitor helpers state

        :return None:
        """
        self.application.sleep(_PERSISTENT_HELPERS_CHECK_INTERVAL)

        while self.application.running:
            alive_threads = {thread.name for thread in threading.enumerate()}
            self.log.debug('Checking helpers state')

            for helper_env in self.application.registry.helper.plugins:
                if self._get_thread_name(helper_env) not in alive_threads:
                    self.log.warn('Helper %s died, trying to restart', helper_env)
                    self._start_helper(helper_env)
                else:
                    self.log.debug('Helper %s is running', helper_env)

            self.application.sleep(_PERSISTENT_HELPERS_CHECK_INTERVAL)

    def _start_helper(self, helper_env):
        """ Start helper

        :param Environment helper_env:
        :return None:
        """
        self.log.debug('Starting helper %s', helper_env)
        threading.Thread(
            name=self._get_thread_name(helper_env),
            target=helper_env,
            kwargs={'logger': self.log},
            daemon=True
        ).start()

    @staticmethod
    def _get_thread_name(env: Environment) -> str:
        """ Get thread name for the helper

        :param Environment env:
        :return str:
        """
        return '%s[Worker]' % env

    @classmethod
    def name(cls) -> str:
        """ Get service unique name

        :return str:
        """
        return 'helpers_manager'
