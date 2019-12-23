# -* coding: utf-8 *-
# (C) 2012 by Bernd Wurst <bernd@schokokeks.org>

# This file is part of Bib2011.
#
# Bib2011 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bib2011 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bib2011.  If not, see <http://www.gnu.org/licenses/>.

import sys, os.path


# Search for included submodule pyusb
atoms = os.path.abspath(os.path.dirname(__file__)).split('/')
pyusb = ''
while atoms:
    candidate = os.path.join('/'.join(atoms), 'external/pyusb')
    if os.path.exists(candidate):
        pyusb = candidate
        break
    atoms = atoms[:-1]
sys.path.insert(0, pyusb)
import usb.core
import usb.util


class USBPrinter (object):
    vendor = 0x04b8
    product = 0x0e03 
    
    def __init__(self):
        self.initialized = False
        try:
            self.__device = usb.core.find(idVendor = self.vendor, idProduct = self.product)
            if not self.__device:
                return None
        
            cfg = self.__device.get_active_configuration()
            interface_number = cfg[(0,0)].bInterfaceNumber
            
            if self.__device.is_kernel_driver_active(interface_number):
                self.__device.detach_kernel_driver(interface_number)
            else:
                print ("no kernel driver attached")

            self.__device.set_configuration()
                
            intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number)
        
            endpoints = usb.util.find_descriptor(intf, find_all = True)
            ep_out = None
            for e in endpoints:
                if (usb.util.endpoint_direction(e.bEndpointAddress) == 
                    usb.util.ENDPOINT_OUT):
                    ep_out = e
                    break
            ep_in = None
            for e in endpoints:
                if (usb.util.endpoint_direction(e.bEndpointAddress) == 
                    usb.util.ENDPOINT_IN):
                    ep_in = e
                    break
        
            assert ep_out is not None and ep_in is not None, "Error getting a USB endpoint address"
            self.ep_out = ep_out
            self.ep_in = ep_in
            self.initialized = True
        except usb.core.USBError:
            pass

    def get_endpoints(self):
        if self.initialized:
            return self.ep_out, self.ep_in
        else:
            print ('initialization error')
            return None, None
            

    def __del__(self):
        self.terminate()
    
    def terminate(self):
        if self.initialized:
            usb.util.dispose_resources(self.__device)
        self.initialized = False
    
        

    
if __name__ == '__main__':
    prn = USBPrinter()
    (fd_out, fd_in) = prn.get_endpoints()
    fd_out.write('Hallo\n')
    





