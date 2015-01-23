# -*- coding: UTF-8

"""
Empty applications / services / etc
"""

__all__ = ['VoidApplication', 'EmptyService', 'EmptyNamedService']

from dewyatochka.core.application import Application, Service


class VoidApplication(Application):
    """
    Test application with empty run() method
    """

    def run(self, args: list):
        """
        Run application
        :param args: list Console arguments
        :return: void
        """
        pass


class EmptyService(Service):
    """
    Empty service for tests
    """
    pass


class EmptyNamedService(EmptyService):
    """
    Service with own name
    """

    @classmethod
    def name(cls) -> str:
        """
        Get service unique name
        :return: str
        """
        return 'test_service'
