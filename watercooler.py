# coding=utf-8

import hashlib
import json
import logging
import os
import signal
import time
import uuid

from typing import Union, Optional, Awaitable
from urllib.parse import urlparse

from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils.crypto import constant_time_compare
from redis import Redis
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, parse_command_line, options
from tornado.web import Application, RequestHandler, HTTPError
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornadoredis import Client
from tornadoredis.pubsub import BaseSubscriber

define('debug', default=False, type=bool, help='Run in debug mode')
define('port', default=8080, type=int, help='Server port')
define('allowed_hosts', default="localhost:8080", multiple=True,
       help='Allowed hosts for cross domain connections')


class RedisSubscriber(BaseSubscriber):

    def on_message(self, msg):
        """Handle new message on the Redis channel"""
        if msg and msg.kind == 'message':
            try:
                message = json.loads(msg.body)
                sender = message['sender']
                message = message['message']
            except (ValueError, KeyError):
                message = msg.body
                sender = None

            subscribers = list(self.subscribers[msg.channel].keys())
            for subscriber in subscribers:
                if sender is None or sender != subscriber.uid:
                    try:
                        subscriber.write_message(message)
                    except WebSocketClosedError:
                        # Remove dead peer
                        self.unsubscribe(msg.channel, subscriber)
        super().on_message(msg)


class SprintHandler(WebSocketHandler):
    """Handlers real-time updates to the board."""

    def check_origin(self, origin: str):
        allowed = super().check_origin(origin)
        parsed = urlparse(origin.lower())
        matched = any(parsed.netloc == host for host in options.allowed_hosts)
        return options.debug or allowed or matched

    def open(self, *args: str, **kwargs: str) -> Optional[Awaitable[None]]:
        """Subscribe to sprint updates on a new connection."""
        # breakpoint()
        # TODO: Validate sprint
        setattr(self, 'sprint', None)
        channel = self.get_argument('channel', None)
        if not channel:
            self.close()
        else:
            try:  # signature to guarantee the client is not the fake.
                sprint = self.application.signer.unsign(channel, max_age=60 * 30)
                setattr(self, 'sprint', sprint)
            except (BadSignature, SignatureExpired):
                self.close()
            else:
                uid = uuid.uuid4().hex  # unique uid, Using to send message to others not itself.
                setattr(self, 'uid', uid)
                self.application.add_subscriber(getattr(self, 'sprint'), self)

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        """Broadcast updates to other interested clients."""
        if getattr(self, 'sprint') is not None:
            self.application.broadcast(message, channel=getattr(self, 'sprint'), sender=self)

    def on_close(self) -> None:
        """Remove subscription."""
        if getattr(self, 'sprint') is not None:
            self.application.remove_subscriber(getattr(self, 'sprint'), self)


class UpdateHandler(RequestHandler):
    """Handler updates from the Django application."""

    def post(self, model, pk):
        self._broadcast(model, pk, 'add')

    def put(self, model, pk):
        self._broadcast(model, pk, 'update')

    def delete(self, model, pk):
        self._broadcast(model, pk, 'remove')

    def _broadcast(self, model, pk, action):
        signature = self.request.headers.get('X-Signature', None)
        if not signature:
            raise HTTPError(400)
        try:
            result = self.application.signer.unsign(signature, max_age=60 * 1)
        except (BadSignature, SignatureExpired):
            raise HTTPError(400)
        else:
            method = self.request.method.lower()
            url = self.request.full_url()
            body = hashlib.sha256(self.request.body).hexdigest()
            expected = f"{method}:{url}:{body}"
            if not constant_time_compare(result, expected):
                raise HTTPError(400)
        try:
            body = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            body = None
        message = json.dumps({
            'model': model,
            'id': pk,
            'action': action,
            'body': body,
        })
        self.application.broadcast(message)
        self.write("OK")


class ScrumApplication(Application):

    def __init__(self, **kwargs):
        routes = [
            (r'/socket', SprintHandler),
            (r'/(?P<model>task|sprint|user)/(?P<pk>[0-9]+)', UpdateHandler),
        ]
        super().__init__(routes, **kwargs)
        self.subscriber = RedisSubscriber(Client())
        self.publisher = Redis()
        self._key = os.environ.get('WATERCOOLER_SECRET', ')zu-07tfvq5&@f^k26f&c58w+w$q=r#ttx!j6pku(-lj6d3jtv')
        self.signer = TimestampSigner(self._key)

    def add_subscriber(self, channel, subscriber):
        self.subscriber.subscribe(['all', channel], subscriber)

    def remove_subscriber(self, channel, subscriber):
        self.subscriber.unsubscribe(channel, subscriber)
        self.subscriber.unsubscribe('all', subscriber)

    def broadcast(self, message, channel=None, sender=None):
        """
        If channel is None, it means that broadcasting to all clients in every channels.
        otherwise, it broadcasts to these clients who interest in at this channel.
        """
        channel = 'all' if channel is None else channel
        message = json.dumps({
            'sender': sender and sender.uid,
            'message': message,
        })
        self.publisher.publish(channel, message)


def shutdown(server):
    ioloop = IOLoop.instance()
    logging.info('Stopping server.')
    server.stop()

    def finalize():
        ioloop.stop()
        logging.info('Stopped.')

    ioloop.add_timeout(time.time() + 1.5, finalize)


if __name__ == "__main__":
    parse_command_line()
    application = ScrumApplication(debug=options.debug)
    server = HTTPServer(application)
    server.listen(options.port)
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown(server))
    logging.info(f'Starting server on localhost: {options.port}')
    IOLoop.instance().start()
