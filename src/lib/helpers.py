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


import re, os, sys

# Search for included submodule python-phonenumbers
atoms = os.path.abspath(os.path.dirname(__file__)).split('/')
dir = ''
while atoms:
    candidate = os.path.join('/'.join(atoms), 'external/python-phonenumbers')
    if os.path.exists(candidate):
        dir = candidate
        break
    atoms = atoms[:-1]
sys.path.insert(0, dir+'/python')
import phonenumbers



def getMoneyValue(value, sign = u'€'):
    s = u'%.2f %s' % (float(value), sign)
    s = s.replace('.', ',')
    pat = re.compile(r'([0-9])([0-9]{3}[.,])')
    while pat.search(s):
        s = pat.sub(r'\1.\2', s)
    #s = s.replace(',00', ',-')
    return s

def renderIntOrFloat(value):
    if int(value) == value:
        return u'%.0f' % value
    else:
        for decimals in range(1,3):
            if round(value, decimals) == value:
                return u'%s' % str(round(value, decimals))
    return u'%s' % str(round(value, 2))


def formatPhoneNumber(number):
    numbers = []
    for num in number.split(' / '):
        numbers.append(formatIncompletePhonenumber(num))
    return ' / '.join(numbers)
    

def formatIncompletePhonenumber(number):
    formatter = phonenumbers.AsYouTypeFormatter("DE")
    result = ''
    for c in number:
        result = formatter.input_digit(c)
    return result
