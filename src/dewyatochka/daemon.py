# -*- coding: UTF-8

"""
Dewyatochka daemon application
"""

__all__ = ['Application']

import os
import sys
import time
import argparse
import fcntl
from dewyatochka.core.application import Application as BaseApplication
from dewyatochka.core.config import GlobalConfig, ConferenceConfig
from dewyatochka.core import conference, plugin, log, helper


class Application(BaseApplication):
    """
    Dewyatochka daemon application
    """

    # Lock file name
    _lock_file = None

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

    def _init_logger(self, is_daemon):
        """
        Init logger instance
        :param is_daemon:
        :return: void
        """
        logger = log.FileHandler(self) if is_daemon else log.STDOUTHandler(self)
        self.set_log_handler(logger)

    def _start_daemon(self):
        """
        Daemonize main process
        :return: void
        """
        import resource
        import signal

        pid = os.fork()
        if pid != 0:
            os._exit(0)
        pid = os.fork()
        if pid != 0:
            os._exit(0)

        signal.signal(signal.SIGTERM, lambda *args: self.stop(2))

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            maxfd = 1024
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:
                pass

        os.open(os.devnull, os.O_RDWR)
        os.dup2(0, 1)
        os.dup2(1, 2)

    def _lock_acquire(self):
        """
        Create lock-file
        :return: void
        """
        lock_file = self.config.section('global').get('lock_file', GlobalConfig.DEFAULT_LOCK_FILE)

        if os.path.isfile(lock_file):
            raise RuntimeError('Process is already running!')

        self._lock_file = open(lock_file, 'w')
        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)
        self._lock_file.write(str(os.getpid()))
        self._lock_file.flush()

    def _lock_release(self):
        """
        Remove lock if needed
        :return:
        """
        if self._lock_file and not self._lock_file.closed:
            fcntl.flock(self._lock_file, fcntl.LOCK_UN)
            self._lock_file.close()
            os.unlink(self._lock_file.name)

    def _wait(self):
        """
        Wait until is not stopped
        :return: void
        """
        while self.running:
            # TODO: Try to check until all critical threads are stopped
            time.sleep(1)

    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return:
        """
        try:
            args_parser = argparse.ArgumentParser()
            args_parser.add_argument('--config',
                                     help='Path to config file to use',
                                     default=GlobalConfig.DEFAULT_FILE_PATH)
            args_parser.add_argument('--nodaemon',
                                     help='Do not detach process from console',
                                     action='store_true')

            args = args_parser.parse_args(args[1:])

            if not args.nodaemon:
                self._start_daemon()

            self._init_config(args.config)
            self._init_logger(not args.nodaemon)
            self._lock_acquire()

            plugin.load_plugins()

            conf_manager = conference.ConferenceManager(self)
            self.set_conference_manager(conf_manager)

            helper_manager = helper.HelpersManager(self)
            self.set_helper_manager(helper_manager)

            self.conference_manager.start()
            self.helper_manager.start()

            self._wait()
            self.log(__name__).info('Bye-bye~')
        except (KeyboardInterrupt, SystemExit):
            self.log(__name__).info('Interrupted by user')
            self.stop(2)
        except Exception as e:
            self.error(__name__, e)
            self.stop(1)
        finally:
            self._lock_release()
            sys.exit(self._exit_code)
