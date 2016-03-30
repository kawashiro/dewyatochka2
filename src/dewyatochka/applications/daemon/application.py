# -*- coding: UTF-8

""" Main application implementation

Serves conferences and takes a talk with other people

Classes
=======
    DaemonApplication -- Application implementation
"""

import sys

from dewyatochka.core import daemon
from dewyatochka.core.application import Application, StandaloneService, EXIT_CODE_TERM

from . import __name__ as app_name

__all__ = ['DaemonApplication']


class DaemonApplication(Application):
    """ Application implementation """

    def run(self, args: list):
        """ Run application

        :param list args: Console arguments
        :return None:
        """
        try:
            no_daemon, pid_file = args

            if not no_daemon:
                daemon.detach(lambda *_: self.stop())
            if not no_daemon or pid_file:
                daemon.acquire_lock(pid_file)

            self.registry.message_plugin_provider.load()
            self.registry.helper_plugin_provider.load()
            self.registry.control_plugin_provider.load()

            self.registry.bootstrap.run()
            self.registry.daemon.start()
            self.registry.scheduler.start()
            self.registry.chat_manager.start()
            self.registry.control.start()

            self.wait()

        except (KeyboardInterrupt, SystemExit):
            self.registry.log(app_name).warning('Interrupted by user')
            self.stop(EXIT_CODE_TERM)

        except Exception as e:
            self.fatal_error(app_name, e)

        finally:
            # Stop threads if needed
            for critical_svc in self.registry.all:
                if isinstance(critical_svc, StandaloneService):
                    critical_svc.wait()
            # Release process lock if needed
            try:
                daemon.release_lock()
            except daemon.ProcessNotLockedError:
                pass
            # Say bye-bye ^-^
            try:
                self.registry.log(app_name).info('Bye-bye~')
            except:
                pass
            # Shut down
            sys.exit(self._exit_code)
