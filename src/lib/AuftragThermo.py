# -*- coding: utf-8 -*-
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

import re, datetime

from lib.helpers import formatPhoneNumber

def _splitToWidth(text, width):
    lines = []
    paras = text.split('\n')
    for para in paras:
        words = para.split(' ')
        while len(words) > 0:
            mywords = [words[0], ]
            del words[0]
            while len(words) > 0 and len(' '.join(mywords) + ' ' + words[0]) <= width:
                mywords.append(words[0])
                del words[0]
            lines.append(' '.join(mywords))
    return lines


def AuftragThermo(auftrag, printer):
    if not printer:
        print ('Drucker nicht initialisiert!')
        return
    name = auftrag.getKundenname()
    printer.align('left')
    printer.fontsize(4, 3)
    if len(name) > 10:
        printer.fontsize(3, 2)
    printer.bold(True)
    printer.text(name + '\n')
    printer.bold(False)
    printer.fontsize(1,1)
    telefon = auftrag.kunde.getErsteTelefon()
    if auftrag.telefon:
        telefon = auftrag.telefon
    printer.text(telefon + '\n\n')
    
    if auftrag.lieferart == 'anhaenger':
        printer.text('Obst in Anhänger\nKennzeichen: ')
        printer.bold(True)
        printer.text(auftrag.kennz + '\n')
        printer.bold(False)
    elif auftrag.lieferart == 'gitterbox':
        gbstring = '1 Gitterbox'
        if auftrag.gbcount > 1:
            gbstring = '%i Gitterboxen' % auftrag.gbcount
        printer.text('Obst ist in %s\n' % gbstring)
    else:
        printer.text('Kunde ist vor Ort\n')
    printer.text('\n')
    
    printer.text('Gebrauchte: ')
    printer.bold(True)
    printer.fontsize(3, 2)
    gebraucht = auftrag.gebrauchte
    if not gebraucht:
        gebraucht = 'Keine'
    printer.text(gebraucht)
    printer.bold(False)
    printer.fontsize(1, 1)
    printer.text('\n')
    
    printer.text('Neue: ')
    printer.bold(True)
    printer.fontsize(3, 2)
    neue = auftrag.neue
    if not neue:
        neue = 'Gemischt'
    printer.text(neue)
    printer.bold(False)
    printer.fontsize(1, 1)
    printer.text('\n')
    
    if auftrag.frischsaft:
        printer.text('Frischsaft: ')
        printer.bold(True)
        printer.fontsize(3, 2)
        printer.text(auftrag.frischsaft)
        printer.bold(False)
        printer.fontsize(1, 1)

    if auftrag.sonstiges:
        printer.text('\nBemerkung:\n' + auftrag.sonstiges + '\n')
        
    if auftrag.abholung:
        printer.text('Abholung: %s\n' % auftrag.abholung)
    printer.cut()
    return True
    


