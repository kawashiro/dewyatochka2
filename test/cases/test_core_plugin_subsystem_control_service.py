# -*- coding=utf-8

""" Tests suite for dewyatochka.core.plugin.subsystem.control.service """

import os
import time
import threading
import socket as socket_

import unittest
from unittest.mock import call, Mock, ANY

from dewyatochka.core.plugin.subsystem.control.service import *
from dewyatochka.core.plugin.subsystem.control.network import Message
from dewyatochka.core.application import VoidApplication, Registry
from dewyatochka.core.plugin.base import PluginEntry


class TestOutput(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.service.Output """

    def test_normal_send(self):
        """ Test normal messages sending """
        socket_mock = Mock()
        logger_mock = Mock()

        output_wrapper = Output(socket_mock, logger_mock)
        output_wrapper.info('info(%s)', 'arg1')
        output_wrapper.debug('debug(%s)', 'arg2')
        output_wrapper.error('error(%s)', 'arg3')
        output_wrapper.log('log(%s)', 'arg4')
        output_wrapper.say('say(%s)', 'arg5')

        socket_mock.assert_has_calls([
            call.send(b'{"text": "info(arg1)"}\x00'),
            call.send(b'{"error": "error(arg3)"}\x00'),
            call.send(b'{"text": "log(arg4)"}\x00'),
            call.send(b'{"text": "say(arg5)"}\x00')
        ])
        logger_mock.assert_has_calls([
            call.info('info(%s)', 'arg1'),
            call.debug('debug(%s)', 'arg2'),
            call.error('error(%s)', 'arg3'),
            call.info('log(%s)', 'arg4'),
            call.info('say(%s)', 'arg5')
        ])

    def test_disconnected_client(self):
        """ Test BrokenPipeError handling on unexpected client disconnect """
        socket_mock = Mock()
        socket_mock.send.side_effect = [None, BrokenPipeError]
        logger_mock = Mock()

        output_wrapper = Output(socket_mock, logger_mock)
        output_wrapper.info('info(%d)', 1)
        output_wrapper.info('info(%d)', 2)
        output_wrapper.info('info(%d)', 3)

        socket_mock.assert_has_calls([call.send(b'{"text": "info(1)"}\x00'), call.send(b'{"text": "info(2)"}\x00')])
        logger_mock.warning.assert_has_calls([call('Control client disconnected before operation has completed')])
        logger_mock.info.assert_has_calls([call('info(%d)', 1), call('info(%d)', 2), call('info(%d)', 3)])


class TestWrapper(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.service.Wrapper """

    def test_wrap(self):
        """ Wrapper test """
        application = VoidApplication()
        application.depend(Mock(), 'extensions_config')

        environment = Wrapper(Service(application)).wrap(PluginEntry(lambda *_: None, {}))
        self.assertIsInstance(environment, Environment)


class TestEnvironment(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.service.Environment """

    def test_invoke(self):
        """ Test plugin invoking """
        assert_is_instance = self.assertIsInstance
        runtime_error = RuntimeError()

        def _plugin(**kwargs):
            assert_is_instance(kwargs['inp'], Message)
            assert_is_instance(kwargs['outp'], Output)
            assert_is_instance(kwargs['registry'], Registry)

        def _raising_plugin(**_):
            raise runtime_error

        application = VoidApplication()
        application.depend(Mock(), 'extensions_config')
        application.depend(Mock(), 'log')

        message = Message(foo='bar')
        socket = Mock()

        environment = Wrapper(Service(application)).wrap(PluginEntry(_plugin, {}))
        environment.invoke(command=message, source=socket)

        environment = Wrapper(Service(application)).wrap(PluginEntry(_raising_plugin, {}))
        self.assertRaises(RuntimeError, environment.invoke, command=message, source=socket)
        application.registry.log().error.assert_has_calls([call('%s', runtime_error)])


class TestService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.service.Service """

    def test_loading(self):
        """ Test plugins loading """
        loader_mock = Mock()
        loader_mock.load.return_value = [
            PluginEntry(lambda **_: None, dict(name='cmd1')),
            PluginEntry(lambda **_: None, dict(name='cmd2')),
            PluginEntry(lambda **_: None, dict(name='cmd1')),
        ]
        loader_service_mock = Mock()
        loader_service_mock.loaders = [loader_mock]

        application = VoidApplication()
        application.depend(loader_service_mock, 'plugins_loader')
        application.depend(Mock(), 'extensions_config')
        application.depend(Mock(), 'log')

        service = Service(application)
        self.assertRaises(RuntimeError, service.get_command, 'cmd1')

        service.load()
        application.registry.log().error.assert_has_calls([
            call('Failed to register plugin %s.%s: %s', 'test_core_plugin_subsystem_control_service', ANY, ANY)
        ])
        self.assertEqual(len(service.plugins), 2)
        self.assertIsInstance(service.get_command('cmd1'), Environment)
        self.assertIsInstance(service.get_command('cmd2'), Environment)
        self.assertRaises(RuntimeError, service.get_command, 'cmd3')

    def test_accepts(self):
        """ Test acceptable plugin types getter """
        self.assertEqual(Service(VoidApplication()).accepts, ['ctl'])

    def test_registration(self):
        """ Test service registration """
        application = VoidApplication()
        application.depend(Service)

        self.assertIsInstance(application.registry.control_plugin_provider, Service)


class TestClientService(unittest.TestCase):
    """ Tests suite for dewyatochka.core.plugin.subsystem.control.service.ClientService """

    # Test socket path
    _SOCKET_PATH = os.path.realpath(os.path.dirname(__file__) + '/../files/control/test_client_svc.sock')

    def test_communicate(self):
        """ Test communication through socket """
        def _daemon_impl(socket_path):
            nonlocal client_request
            daemon_response = b'{"text": "info message"}\0' \
                              b'{"error": "error message"}\0' \
                              b'{"foo": "unhandled message"}\0\x01\0'

            socket = socket_.socket(socket_.AF_UNIX)
            try:
                socket.bind(socket_path)
                socket.listen(0)

                connection = socket.accept()[0]
                client_request = connection.recv(1024)
                connection.send(daemon_response)

                connection.shutdown(socket_.SHUT_RDWR)
                connection.close()

            finally:
                socket.close()
                os.unlink(socket_path)

        client_request = None

        daemon = threading.Thread(target=_daemon_impl, args=(self._SOCKET_PATH,))
        client = ClientService(VoidApplication())
        client.application.depend(Mock(), 'log')
        client.socket = self._SOCKET_PATH

        daemon.start()
        time.sleep(0.05)
        client.communicate('foo', {'bar': 'baz'})
        daemon.join()

        self.assertDictEqual(Message.from_bytes(client_request[:-2]).data, {'args': {'bar': 'baz'}, 'name': 'foo'})
        client.application.registry.log().error.assert_has_calls([
            call('Server error: %s', 'error message'),
            call('Unhandled message: %s', "{'foo': 'unhandled message'}")
        ])
        client.application.registry.log().info.assert_has_calls([call('info message')])

    def test_registration(self):
        """ Test service registration """
        application = VoidApplication()
        application.depend(ClientService)

        self.assertIsInstance(application.registry.control_client, ClientService)
