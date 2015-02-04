# -*- coding: UTF-8

"""
XMPP-related errors
"""

__all__ = ['XMPPError', 'ClientDisconnectedError', 'MessageError',
           'XMPPConnectionError', 'S2SConnectionError', 'C2SConnectionError']


class XMPPError(RuntimeError):
    """
    Any error on communication witn xmpp-server
    """
    pass


class XMPPConnectionError(XMPPError):
    """
    Exception on failed connection attempt
    """
    pass


class C2SConnectionError(XMPPConnectionError):
    """
    Exception client-to-server connection error
    """
    pass


class S2SConnectionError(XMPPConnectionError):
    """
    Exception server-to-server connection error
    """
    pass


class ClientDisconnectedError(XMPPConnectionError):
    """
    Exception on client stop or connection lost
    """
    pass


class MessageError(XMPPError):
    """
    On error message recieving
    """

    # XMPP error message type
    MESSAGE_TYPE_ERROR = 'error'

    # "Feature is not implemented" error condition
    CONDITION_NOT_IMPLEMENTED = 'feature-not-implemented'

    # Exception message template
    EXCEPTION_MESSAGE_TPL = 'Error {}: {}'
