# -*- coding: UTF-8

""" XMPP-related exception classes

Classes
=======
    XMPPError               -- Any error on communication with xmpp server / client
    XMPPConnectionError     -- Exception on failed connection attempt
    C2SConnectionError      -- Exception client-to-server connection error
    S2SConnectionError      -- Exception server-to-server connection error
    ClientDisconnectedError -- Exception on client stop or connection lost
    MessageError            -- On error message receiving
"""

from .entity import Conference

__all__ = ['XMPPError', 'ClientDisconnectedError', 'MessageError',
           'XMPPConnectionError', 'S2SConnectionError', 'C2SConnectionError']


class XMPPError(RuntimeError):
    """ Any error on communication with xmpp server / client """
    pass


class XMPPConnectionError(XMPPError):
    """ Exception on failed connection attempt """
    pass


class C2SConnectionError(XMPPConnectionError):
    """ Exception client-to-server connection error """
    pass


class S2SConnectionError(XMPPConnectionError):
    """ Exception server-to-server connection error """

    def __init__(self, *args, remote: Conference, **kwargs):
        """ Instantiate S2S connection exception and assign remote member JID to it

        :param Conference remote: Remote member JID
        :param tuple args:
        :param dict kwargs:
        """
        super().__init__(*args, **kwargs)
        self._remote = remote

    @property
    def remote(self) -> Conference:
        """ Get remote member JID

        :return Conference:
        """
        return self._remote


class ClientDisconnectedError(C2SConnectionError):
    """ Exception on client stop or connection lost """
    pass


class MessageError(XMPPError):
    """ On error message receiving """

    # XMPP error message type
    MESSAGE_TYPE_ERROR = 'error'

    # "Feature is not implemented" error condition
    CONDITION_NOT_IMPLEMENTED = 'feature-not-implemented'

    # Exception message template
    EXCEPTION_MESSAGE_TPL = 'Error {}: {}'
