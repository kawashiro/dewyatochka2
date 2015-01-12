# -*- coding: UTF-8

"""
Helpers management
"""

__all__ = ['HelpersManager']

from dewyatochka.core import plugin, application
import threading
import time

# Interval between helpers state checks
_PERSISTENT_HELPERS_CHECK_INTERVAL = 60


class HelpersManager(application.Service):
    """
    Controls all registered helpers
    """

    # Dict with handlers associated with their own threads names
    _helpers_dict = {}

    def start(self):
        """
        Start manager
        :return: void
        """
        threading.Thread(
            name='dewyatochka.helpers_manager',
            target=self.run
        ).start()

    def run(self):
        """
        Perform helpers control
        :return: void
        """
        logger = self.application.log(__name__)

        try:
            for thread_name in self._helpers:
                logger.debug('Starting helper thread %s', thread_name)
                self._start_helper(thread_name)

            while True:
                check_at = time.time() + _PERSISTENT_HELPERS_CHECK_INTERVAL
                while time.time() < check_at:
                    if not self.application.running:
                        return
                    time.sleep(1)

                logger.debug('Checking helpers state')
                alive_threads = set(thread.name for thread in threading.enumerate())
                for thread_name in self._helpers:
                    if thread_name not in alive_threads:
                        logger.warn('Helper %s died, trying to restart', thread_name)
                        self._start_helper(thread_name)
                    else:
                        logger.debug('Helper %s is running', thread_name)
        except Exception as e:
            self.application.error(__name__, e)
            self.application.log(__name__).critical('Fatal error: Helpers manager failed')

    def _start_helper(self, helper_name):
        """
        Start helper by name
        :param helper_name: str
        :return: void
        """
        def _helper_wrapper(_helper, _application):
            """
            :param _helper: callable
            :param _application: Application
            :return:void
            """
            try:
                _helper(_application)
            except Exception as e:
                _application.log(__name__).error(
                    'Helper %s.%s failed: %s',
                    _helper.__module__,
                    _helper.__name__,
                    e
                )
                raise
        try:
            helper_fn = self._helpers[helper_name]
            threading.Thread(
                name=helper_name,
                target=_helper_wrapper,
                daemon=True,
                args=(helper_fn, self.application)
            ).start()
        except KeyError:
            raise RuntimeError('Helper %s is not registered' % helper_name)

    @property
    def _helpers(self):
        """
        Threads getter
        :return: dict
        """
        if not self._helpers_dict:
            self._helpers_dict = {self._get_thread_name(fn): fn for fn in plugin.get_helpers()}

        return self._helpers_dict

    @staticmethod
    def _get_thread_name(fn):
        """
        Get thread name for the helper
        :param fn: callable
        :return: str
        """
        return 'dewyatochka.helper.%s.%s' % (fn.__module__, fn.__name__)
