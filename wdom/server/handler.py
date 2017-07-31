#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Event/Message handlers for web server."""

import json
import logging
from typing import Any, Dict

from wdom.event import Event, create_event

logger = logging.getLogger(__name__)


def log_handler(level: str, message: str) -> None:
    """Handle logs from client (browser)."""
    message = 'JS: ' + str(message)
    if level == 'error':
        logger.error(message)
    elif level == 'warn':
        logger.warning(message)
    elif level == 'info':
        logger.info(message)
    elif level == 'debug':
        logger.debug(message)


def create_event_from_msg(msg: dict) -> Event:
    """Create Event from dictionally (JSON message).

    Message format:
        {
            'type': 'event type',
            'currentTarget': {
                'id': 'rimo_id of target node',
                ... (additional information),
                },
            'target': {
                'id': 'rimo_id of target node',
                ... (additional information),
                },
            ...,
            }
    """
    from wdom.document import getElementByRimoId
    _id = msg.get('currentTarget', {'id': None}).get('id')
    ctarget = getElementByRimoId(_id)
    _id = msg.get('target', {'id': None}).get('id')
    target = getElementByRimoId(_id) or ctarget
    return create_event(msg['type'], currentTarget=ctarget,
                        target=target, init=msg)


def event_handler(msg: Dict[str, Any]) -> None:
    """Handle events emitted on browser."""
    e = create_event_from_msg(msg)
    if e.currentTarget is None:
        if e.type not in ['mount', 'unmount']:
            id = msg['currentTarget']['id']
            logger.warning('No such element: rimo_id={}'.format(id))
        return
    e.currentTarget.on_event_pre(e)
    e.currentTarget.dispatchEvent(e)


def response_handler(msg: Dict[str, str]) -> None:
    """Handle response sent by browser."""
    from wdom.document import getElementByRimoId
    id = msg['id']
    elm = getElementByRimoId(id)
    if elm:
        elm.on_response(msg)
    else:
        logger.warning('No such element: rimo_id={}'.format(id))


def on_websocket_message(message: str) -> None:
    """Handle messages from browser."""
    msgs = json.loads(message)
    for msg in msgs:
        _type = msg.get('type')
        if _type == 'log':
            log_handler(msg.get('level'), msg.get('message'))
        elif _type == 'event':
            event_handler(msg['event'])
        elif _type == 'response':
            response_handler(msg)
        else:
            raise ValueError('unkown message type: {}'.format(message))