# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2017 Marek Marczykowski-Górecki
#                               <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.


'''
Main Qubes() class and related classes.
'''

import socket
import subprocess

import qubesmgmt.base
import qubesmgmt.exc
import qubesmgmt.label
import qubesmgmt.storage
import qubesmgmt.utils
import qubesmgmt.vm
import qubesmgmt.config

BUF_SIZE = 4096


class VMCollection(object):
    '''Collection of VMs objects'''
    def __init__(self, app):
        self.app = app
        self._vm_list = None
        self._vm_objects = {}

    def clear_cache(self):
        '''Clear cached list of VMs'''
        self._vm_list = None

    def refresh_cache(self, force=False):
        '''Refresh cached list of VMs'''
        if not force and self._vm_list is not None:
            return
        vm_list_data = self.app.qubesd_call(
            'dom0',
            'mgmt.vm.List'
        )
        new_vm_list = {}
        # FIXME: this will probably change
        for vm_data in vm_list_data.splitlines():
            vm_name, props = vm_data.decode('ascii').split(' ', 1)
            vm_name = str(vm_name)
            props = props.split(' ')
            new_vm_list[vm_name] = dict(
                [vm_prop.split('=', 1) for vm_prop in props])

        self._vm_list = new_vm_list
        for name, vm in list(self._vm_objects.items()):
            if vm.name not in self._vm_list:
                # VM no longer exists
                del self._vm_objects[name]
            elif vm.__class__.__name__ != self._vm_list[vm.name]['class']:
                # VM class have changed
                del self._vm_objects[name]
            # TODO: some generation ID, to detect VM re-creation
            elif name != vm.name:
                # renamed
                self._vm_objects[vm.name] = vm
                del self._vm_objects[name]

    def __getitem__(self, item):
        if item not in self:
            raise KeyError(item)
        if item not in self._vm_objects:
            cls = qubesmgmt.utils.get_entry_point_one('qubesmgmt.vm',
                self._vm_list[item]['class'])
            self._vm_objects[item] = cls(self.app, item)
        return self._vm_objects[item]

    def __contains__(self, item):
        self.refresh_cache()
        return item in self._vm_list

    def __iter__(self):
        self.refresh_cache()
        for vm in self._vm_list:
            yield self[vm]

    def keys(self):
        '''Get list of VM names.'''
        self.refresh_cache()
        return self._vm_list.keys()


class QubesBase(qubesmgmt.base.PropertyHolder):
    '''Main Qubes application'''

    #: domains (VMs) collection
    domains = None
    #: labels collection
    labels = None
    #: storage pools
    pools = None
    #: type of qubesd connection: either 'socket' or 'qrexec'
    qubesd_connection_type = None

    def __init__(self):
        super(QubesBase, self).__init__(self, 'mgmt.property.', 'dom0')
        self.domains = VMCollection(self)
        self.labels = qubesmgmt.base.WrapperObjectsCollection(
            self, 'mgmt.label.List', qubesmgmt.label.Label)
        self.pools = qubesmgmt.base.WrapperObjectsCollection(
            self, 'mgmt.pool.List', qubesmgmt.storage.Pool)
        #: cache for available storage pool drivers and options to create them
        self._pool_drivers = None

    def _refresh_pool_drivers(self):
        '''
        Refresh cached storage pool drivers and their parameters.

        :return: None
        '''
        if self._pool_drivers is None:
            pool_drivers_data = self.qubesd_call(
                'dom0', 'mgmt.pool.ListDrivers', None, None)
            assert pool_drivers_data.endswith(b'\n')
            pool_drivers = {}
            for driver_line in pool_drivers_data.decode('ascii').splitlines():
                if not driver_line:
                    continue
                driver_name, driver_options = driver_line.split(' ', 1)
                pool_drivers[driver_name] = driver_options.split(' ')
            self._pool_drivers = pool_drivers

    @property
    def pool_drivers(self):
        ''' Available storage pool drivers '''
        self._refresh_pool_drivers()
        return self._pool_drivers.keys()

    def pool_driver_parameters(self, driver):
        ''' Parameters to initialize storage pool using given driver '''
        self._refresh_pool_drivers()
        return self._pool_drivers[driver]

    def add_pool(self, name, driver, **kwargs):
        ''' Add a storage pool to config

        :param name: name of storage pool to create
        :param driver: driver to use, see :py:meth:`pool_drivers` for
        available drivers
        :param kwargs: configuration parameters for storage pool,
        see :py:meth:`pool_driver_parameters` for a list
        '''
        # sort parameters only to ease testing, not required by API
        payload = 'name={}\n'.format(name) + \
                  ''.join('{}={}\n'.format(key, value)
            for key, value in sorted(kwargs.items()))
        self.qubesd_call('dom0', 'mgmt.pool.Add', driver,
            payload.encode('utf-8'))

    def remove_pool(self, name):
        ''' Remove a storage pool '''
        self.qubesd_call('dom0', 'mgmt.pool.Remove', name, None)


class QubesLocal(QubesBase):
    '''Application object communicating through local socket.

    Used when running in dom0.
    '''

    qubesd_connection_type = 'socket'

    def qubesd_call(self, dest, method, arg=None, payload=None):
        try:
            client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_socket.connect(qubesmgmt.config.QUBESD_SOCKET)
        except IOError:
            # TODO:
            raise

        # src, method, dest, arg
        for call_arg in ('dom0', method, dest, arg):
            if call_arg is not None:
                client_socket.sendall(call_arg.encode('ascii'))
            client_socket.sendall(b'\0')
        if payload is not None:
            client_socket.sendall(payload)

        client_socket.shutdown(socket.SHUT_WR)

        return_data = client_socket.makefile('rb').read()
        return self._parse_qubesd_response(return_data)


class QubesRemote(QubesBase):
    '''Application object communicating through qrexec services.

    Used when running in VM.
    '''

    qubesd_connection_type = 'qrexec'

    def qubesd_call(self, dest, method, arg=None, payload=None):
        service_name = method
        if arg is not None:
            service_name += '+' + arg
        p = subprocess.Popen(['qrexec-client-vm', dest, service_name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate(payload)
        if p.returncode != 0:
            # TODO: use dedicated exception
            raise qubesmgmt.exc.QubesException('Service call error: %s',
                stderr.decode())

        return self._parse_qubesd_response(stdout)
