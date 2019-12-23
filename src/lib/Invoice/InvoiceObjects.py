# -* coding: utf8 *-
# (C) 2011 by Bernd Wurst <bernd@schokokeks.org>

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

import datetime

class InvoiceText(object):
    def __init__(self, content, urgent=False, headline=None):
        self.paragraphs = [content]
        self.urgent = urgent
        self.headline = headline

    def addParagraph(self, content):
        self.paragraphs.append(content)


class InvoiceTable(object):
    def __init__(self, vatType = 'gross', tender = False, summary = True):
        self.entries = []
        self.vat = {}
        self.sum = 0.0
        self.tender = tender
        self.summary = summary
        if vatType not in ['gross', 'net']:
            raise ValueError('vatType must be »gross« or »net«')
        self.vatType = vatType
    
    def validEntry(self, entry):
        '''bekommt einen Eintrag und liefert einen Eintrag wenn ok, wirft ansonsten ValueError.
        wird benutzt um z.B. die Summe auszurechnen oder ähnliches
        '''
        k = entry.keys()
        e = entry
        if not ('count' in k and 'unit' in k and 'subject' in k and 'price' in k and 'vat' in k):
            raise ValueError('Some data is missing!')
        ret = {'type': 'entry',
               'count': e['count'],
               'unit': e['unit'],
               'subject': e['subject'],
               'price': e['price'],
               'total': (e['price'] * e['count']),
               'vat': e['vat'],
               'tender': False,
               }
        if ret['vat'] > 1:
            ret['vat'] = float(ret['vat']) / 100
            
        if 'tender' in e.keys():
            ret['tender'] = e['tender']
        if 'desc' in k:
            ret['desc'] = e['desc']
        return ret
    
    def addItem(self, data):
        '''Fügt eine Zeile ein. data muss ein Dict mit passenden Keys und passenden
        Typen sein'''
        d = self.validEntry(data)
        if not d['vat'] in self.vat.keys():
            self.vat[d['vat']] = [0, chr(65+len(self.vat))]
        if 'tender' not in data or not data['tender']:
            self.vat[d['vat']][0] += d['total']
            self.sum += d['total']
        self.entries.append(d)
    
    def addTitle(self, title):
        self.entries.append({'type': 'title', 'title': title,})



class Invoice(object):
    def __init__(self, tender = False):
        self.customerno = None
        self.addresslines = ['', ]
        self.salutation = 'Sehr geehte Damen und Herren,'
        self.id = None
        self.cash = True
        self.tender = tender
        self.official = True
        self.parts = []
        self.pagecount = 0
        self.date = datetime.date.today()
    
    def setDate(self, date):
        if type(date) != datetime.date:
            raise ValueError('date must be of type »datetime.date«')
        self.date = date
