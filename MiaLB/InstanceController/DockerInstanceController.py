#!/usr/bin/python2.7

# Copyright (C) 2016 Eitan Geiger
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os

from threading import Thread
from requests import get

from .SingleInstanceController import SingleInstanceController


class DockerInstanceController(SingleInstanceController):
    def __init__(self):
        SingleInstanceController.__init__(self)
        self.swarm_uri = "connection string to swarm cluster?"
        # TODO: initial something of docker??

    def set_instance(self, farm_id, instance_id=None):
        Thread(target=super(DockerInstanceController, self).set_instance,
               kwargs={'farm_id': farm_id, 'instance_id': instance_id}).start()

    def rem_instance(self, farm_id=None, instance_id=None):
        Thread(target=super(DockerInstanceController, self).rem_instance,
               kwargs={'farm_id': farm_id, 'instance_id': instance_id}).start()

    def _remove_instance(self, farm_id):
        instance_id = super(DockerInstanceController, self)._remove_instance(farm_id=farm_id)
        return os.system("docker kill {}".format(instance_id))

    def _create_instance(self, farm_id):
        instance_id = os.popen("docker run -e FARMID={} server:port/user/mia-farm".format(farm_id)).read().strip()
        # now we want to add an interface
        os.system("docker ")
        return instance_id

    def _update_instance(self, instance_id):
        return os.system("docker exec {} /update_nginx.sh".format(instance_id))
