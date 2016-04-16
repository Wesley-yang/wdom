#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module defines options for wdom and wraps ``tornado.options``.
Do not use ``tornado.options`` directly.
"""

from argparse import ArgumentParser

__all__ = [
    'parser',
    'config',
    'parse_command_line',
]


def parse_command_line():
    '''Parse command line options and set options in ``tornado.options``.'''
    import tornado.options
    global config
    parser.parse_known_args(namespace=config)
    for k, v in vars(config).items():
        if k.startswith('log'):
            tornado.options.options.__setattr__(k, v)
    return config


parser = ArgumentParser(prog='WDOM', argument_default=None)
config = parser.parse_args([])

parser.add_argument(
    '--logging', choices=['debug', 'info', 'wran', 'error'],
    help='Set the log level (dafualt: `info`).',
)
parser.add_argument(
    '--debug', default=False, action='store_const', const=True,
    help='Enable debug mode (dafualt: False).'
    ' Debug mode enables `--autoreload`.'
)
parser.add_argument(
    '--address', default='localhost',
    help='Address to run server (default: `localhost`).'
)
parser.add_argument(
    '--port', default=8888, type=int,
    help='Port to run server (defualt: 8888). If 0, use arbitrary free port.',
)
parser.add_argument(
    '--autoreload', default=False, action='store_const', const=True,
    help='Watch files and restart when any files changed (default: False).',
)
parser.add_argument(
    '--theme', default=None, type=str,
    help='Choose theme name to use with wdom.themes module.'
    ' By default (None) or unavailable name, use `wdom.tag`.'
)
parser.add_argument(
    '--auto-shutdown', default=False, action='store_const', const=True,
    help='Terminate server process when all connections (browser tabs) closed'
    ' (default: False).',
)
parser.add_argument(
    '--shutdown-wait', default=1.0, type=float,
    help='Seconds to wait until shutdown after all connections closed'
    ' when --auto-shutdown is enabled (default: 1.0 [sec]).',
)
parser.add_argument(
    '--open-browser', default=False, action='store_const', const=True,
    help='Open browser automatically (default: False).',
)
parser.add_argument(
    '--browser', default=None, help='Browser name to open.'
    ' Only affects when used with --open-browser option.'
    ' Available values are keys of `webbrowser._browsers`.'
    ' When not specified or specified invalid value, open system\'s'
    ' default browser (default: None).',
)
parse_command_line()
