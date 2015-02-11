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
    pass


class ClientDisconnectedError(XMPPConnectionError):
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
