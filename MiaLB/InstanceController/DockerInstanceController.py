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
import docker

from ipaddress import ip_address, ip_network
from logging import getLogger
from threading import Thread
from re import sub
from requests import get

from SingleInstanceController import SingleInstanceController
from MiaLB.mialb_configs import *

logger = getLogger(__name__)


def _guess_MiaLB_url():
    print("my pid is {}".format(str(os.getpid())))
    try:
        protocol, inq, outq, local_addr, foreign_addr, state, process = \
            os.popen("netstat -4 -tlnp | grep -e '\s{}/'".format(str(os.getpid()))).readlines()[0].split()
    except IndexError:
        protocol, inq, outq, local_addr, foreign_addr, state, process = \
            os.popen("netstat -4 -tlnp | grep -e ':{}\s'".format(port)).readlines()[0].split()
    # guess my public ip
    temp = os.popen("ip route show | grep default").read().split()
    public_device = temp[temp.index('dev') + 1]
    temp = os.popen("ip -4 addr show {} | grep inet".format(public_device)).read().split()
    public_address = temp[temp.index('inet') + 1].split('/')[0]
    local_addr = sub('(0.0.0.0|127.0.0.1)', public_address, local_addr)
    print("http://{}".format(local_addr))
    return "http://{}".format(local_addr)


class DockerInstanceController(SingleInstanceController):
    def __init__(self, mialb_url=None):
        SingleInstanceController.__init__(self)
        self.client = docker.DockerClient(base_url='http://localhost:2376')
        self.mialb_url = mialb_url if mialb_url else None

    def set_instance(self, **kwargs):
        Thread(target=super(DockerInstanceController, self).set_instance, kwargs=kwargs).start()

    def rem_instance(self, farm_id=None, instance_id=None):
        Thread(target=super(DockerInstanceController, self).rem_instance,
               kwargs={'farm_id': farm_id, 'instance_id': instance_id}).start()

    def _remove_instance(self, farm_id):
        instance_id = super(DockerInstanceController, self)._remove_instance(farm_id=farm_id)
        if isinstance(instance_id, list):
            instance_id = instance_id[0]
        return self.client.services.get(instance_id).remove()

    def _create_instance(self, farm_id):
        if self.mialb_url is None:
            self.mialb_url = _guess_MiaLB_url()
        service_id = self.client.services.create(image='nginx_for_mia:latest',
                                                 env=['FARMID={}'.format(str(farm_id)),
                                                      'MIALBURI={}'.format(str(self.mialb_url))],
                                                 name=str(farm_id))
        if isinstance(service_id, list):
            return service_id[0]
        else:
            return service_id

    def _update_instance(self, farm_id, **kwargs):
        if self.mialb_url is None:
            self.mialb_url = _guess_MiaLB_url()

        # we'll get here when an instance reports it's up and waiting for eth1
        external_ip = get(
            url="{mialb_uri}/MiaLB/farms/{farm_id}".format(mialb_uri=self.mialb_url, farm_id=farm_id)
        ).json()['ip']
        node_name = ""
        container_id = ""
        for container in self.client.services.get(farm_id).tasks():
            logger.debug(str(container))
            if container['Status']['State'] in ['running', 'starting']:
                container_id = container['Status']['ContainerStatus']['ContainerID']
                node_name = self.client.nodes.get(container['NodeID']).attrs['Description']['Hostname']
                logger.info("container id: {}".format(container_id))
                logger.info("node name: {}".format(node_name))
        host_address = node_name
        logger.debug("ssh root@{host} 'python2.7 ....'".format(host=host_address))
        os.system("ssh root@{host} 'python2.7 /usr/bin/docker_networking.py connect"
                  " --container {contiainer_id} --ip {ip}'".format(host=host_address,
                                                                   contiainer_id=container_id,
                                                                   ip=external_ip))

        return self.client.services.get(farm_id).short_id
