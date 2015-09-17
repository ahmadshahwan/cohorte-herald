#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Herald transport implementations package

:author: Ahmad Shahwan
:copyright: Copyright 2015, isandlaTech
:license: Apache License 2.0
:version: 0.0.4
:status: Alpha

..

    Copyright 2015 isandlaTech

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Documentation strings format
__docformat__ = "restructuredtext en"

__author__ = 'Ahmad Shahwan'

import logging
from pelix.ipopo.decorators import ComponentFactory, Requires, Provides, \
    Property, Validate, Invalidate, Instantiate
import herald
from . import ACCESS_ID
from . import models

_logger = logging.getLogger(__name__)


@ComponentFactory('herald-mqtt-directory-factory')
@Requires('_directory', herald.SERVICE_DIRECTORY)
@Property('_access_id', herald.PROP_ACCESS_ID, ACCESS_ID)
@Provides(herald.SERVICE_TRANSPORT_DIRECTORY)
@Instantiate('herald-mqtt-directory')
class Directory(object):
    """
    MQTT directory for Herald.

    MQTT directory is stateless.
    """
    def __init__(self):
        self._directory = None
        self._access_id = ACCESS_ID

    @Validate
    def _validate(self, _):
        """
        Component validated
        """
        pass

    @Invalidate
    def _invalidate(self, _):
        """
        Component invalidated
        """
        pass

    def load_access(self, data):
        """
        Loads a dumped MQTT access

        :param data: Result of a call to HTTPAccess.dump()
        :return: An HTTPAccess bean
        """
        return models.Access()

    def peer_access_set(self, peer, data):
        """
        The access to the given peer matching our access ID has been set

        :param peer: The Peer bean
        :param data: The peer access data, previously loaded with load_access()
        """
        pass

    def peer_access_unset(self, peer, data):
        """
        The access to the given peer matching our access ID has been removed

        :param peer: The Peer bean
        :param data: The peer access data
        """
        pass

    def check_access(self, uid, host, port):
        """
        Checks if the peer with the given UID is known to have the given access

        :param uid: The UID of a peer
        :param host: The tested peer host
        :param port: The tested HTTP port
        :return: True if the given access matches the peer UID
        :raise ValueError: The access doesn't match the peer
        """
        pass

