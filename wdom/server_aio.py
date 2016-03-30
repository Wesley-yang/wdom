#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import asyncio
import socket
import webbrowser

from aiohttp import web, MsgType

from wdom import options
from wdom.misc import static_dir

logger = logging.getLogger(__name__)


class MainHandler(web.View):
    '''This is a main handler, which renders ``document`` object of the
    application. Must be used with an Application object which has ``document``
    attribute.'''
    async def get(self):
        logger.info('connected')
        return web.Response(body=self.request.app['document'].build().encode())


async def ws_open(request):
    handler = WSHandler()
    await handler.open(request)
    return handler.ws


class WSHandler(object):
    async def open(self, request):
        self.req = request
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)
        self.doc = self.req.app['document']
        self.doc.connections.append(self)

        while not self.ws.closed:
            msg = await self.ws.receive()
            if msg.tp == MsgType.text:
                await self.on_message(msg.data)
            elif msg.tp in (MsgType.close, MsgType.closed, MsgType.error):
                await self.ws.close()
        self.on_close()
        return self.ws

    def write_message(self, message):
        self.ws.send_str(message)

    async def on_message(self, message):
        msg = json.loads(message)
        _type = msg.get('type')
        if _type == 'log':
            await self.log_handler(msg.get('level'), msg.get('message'))
        elif _type in ('event', 'response'):
            await self.element_handler(msg)

    def on_close(self):
        logger.info('RootWS CLOSED')
        if self in self.doc.connections:
            self.doc.connections.remove(self)

    async def log_handler(self, level: str, message: str):
        message = 'JS: ' + str(message)
        if level == 'error':
            logger.error(message)
        elif level == 'warn':
            logger.warn(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'debug':
            logger.debug(message)

    async def element_handler(self, msg: dict):
        id = msg.get('id')
        elm = self.doc.getElementById(id)
        if elm is not None:
            elm.on_message(msg)
        else:
            logger.warn('No such element: id={}'.format(id))


class Application(web.Application):
    def add_static_path(self, prefix:str, path:str):
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        self.router.add_static(prefix, path)

    def add_favicon_path(self, path:str):
        self.router.add_static('/(favicon.ico)', path)


def get_app(document, debug=None, **kwargs) -> web.Application:
    '''Return Application object to serve ``document``.'''
    if debug is None:
        if 'debug' not in options.config:
            options.parse_command_line()
        debug = options.config.debug

    app = Application()
    app.router.add_route('GET', '/', MainHandler)
    app.router.add_route('*', '/rimo_ws', ws_open)
    app['document'] = document

    # Add application's static files directory
    app.add_static_path('_static', static_dir)
    return app


async def close_connections(app):
    for conn in app['document'].connections:
        await conn.ws.close(code=999, message='server shutdown')


def start_server(app: web.Application, port=None, browser=None, loop=None,
                 family=socket.AF_INET):
    '''Start server with ``app`` on ``localhost:port``.
    If port is not specified, use command line option of ``--port``.

    If ``browser`` is not specified, do not open the page. When ``browser`` is
    specified, open the page with the specified browser. The specified browser
    name is not registered in ``webbrowser`` module, or, for example it is just
    ``True``, use system's default browser to open the page.
    '''
    if port is None:
        if 'port' not in options.config:
            options.parse_command_line()
        port = options.config.port

    if loop is None:
        loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, 'localhost', port)
    server = loop.run_until_complete(f)
    server.app = app
    server.handler = handler
    app.on_shutdown.append(close_connections)
    logger.info('Start server on port {0:d}'.format(port))

    if browser is not None:
        url = 'http://localhost:{}/'.format(port)
        if browser in webbrowser._browsers:
            webbrowser.get(browser).open(url)
        else:
            webbrowser.open(url)

    return server


def stop_server(server):
    logger.info('Start server shutdown')
    server.close()
    server._loop.run_until_complete(server.wait_closed())
    server._loop.run_until_complete(server.app.shutdown())
    server._loop.run_until_complete(server.handler.finish_connections(1.0))
    server._loop.run_until_complete(server.app.cleanup())
    logger.info('Server terminated')