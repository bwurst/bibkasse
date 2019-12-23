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

def _formatPrice(price, symbol=u'€'):
    '''_formatPrice(price, symbol='€'):
    Gets a floating point value and returns a formatted price, suffixed by 'symbol'. '''
    s = (u"%.2f" % price).replace('.', ',')
    pat = re.compile(r'([0-9])([0-9]{3}[.,])')
    while pat.search(s):
        s = pat.sub(r'\1.\2', s)
    return s+u' '+symbol


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


def RegalschildThermo(beleg, printer):
    if not printer:
        print ('Drucker nicht initialisiert!')
        return
    printer.reset()
    name = beleg.getKundenname()
    printer.align('left')
    printer.fontsize(4, 3)
    if len(name) > 10:
        printer.fontsize(3, 2)
    printer.bold()
    printer.text(name + '\n')
    printer.bold(False)
    printer.align('right')
    printer.fontsize(1,1)
    printer.text('Anzahl Paletten gesamt: ')
    printer.fontsize(3,2)
    printer.bold()
    printer.text('%i\n' % beleg.getPaletten())
    printer.bold(False)
    printer.fontsize(1,1)
    if beleg.getLiterzahl() > 0:
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % beleg.getLiterzahl())
    if beleg.getAbholung():
        printer.text('Abholung: %s\n' % beleg.getAbholung())
    #printer.ean13(beleg.getEAN13())
    printer.cut()
    return True
    


def BelegThermo(beleg, printer, kontodaten = False):
    if not printer:
        print ('Drucker nicht initialisiert!')
        return
    printer.reset()
    printer.align('center')
    printer.bold(True)
    printer.fontsize(2,2)
    printer.text('Mosterei Wurst\n')
    printer.fontsize(1,1)    
    printer.bold(False)
    printer.text('Köchersberg 30\n')
    printer.text('71540 Murrhardt\n')
    printer.text('07192 - 936434\n')
    printer.text('\n\n')
    printer.align('left')
    printer.fontsize(1,1)    
    ust = {}
    ust_idx = 'A'
    for entry in beleg.getEntries():
        # A: Gesamtbreite: 48 Zeichen (Bei font mit doppelter Breis: 24 Zeichen)
        # B: Gesamtbreite: 64 Zeichen (Bei font mit doppelter Breis: 32 Zeichen)
        # Aufteilung: 
        # Eine Zeile Beschreibung (fontsize(2,2))
        # Eine Zeile mit fontsize(2,2)
        #   1234 Einheit  x  1234.56 €  = 1234.56 €
        printer.bold()
        subject = entry['beschreibung']
        maxwidth = 40
        lines = _splitToWidth(subject, maxwidth)
        for line in lines:
            if not line.endswith('\n'):
                line += '\n' 
            printer.text(line)
        printer.bold(False)
        if entry.getSteuersatz() not in ust:
            ust[entry.getSteuersatz()] = {'chr': ust_idx, 'net': 0.0, 'vatsum': 0.0, 'gross': 0.0}
            ust_idx = chr(ord(ust_idx)+1)

        this_ust_char = ust[entry.getSteuersatz()]['chr']
        ust[entry.getSteuersatz()]['net'] += entry.getNettosumme()
        ust[entry.getSteuersatz()]['vatsum'] += entry.getSteuersumme()
        ust[entry.getSteuersatz()]['gross'] += entry.getSumme()
        
        printer.text(u'%6.0f' % entry['anzahl'])
        printer.fontsize(1,1)
        printer.text(u' %-8sx  %11s  =' % (entry['einheit'], _formatPrice(entry.getNormalpreis())))
        printer.text(u' %10s  %s\n' % (_formatPrice(entry.getNormalsumme()), this_ust_char))
        printer.text('\n')
    
    printer.text('\n')
    printer.align('right')

    printer.bold()
    printer.text(u'Gesamtbetrag: ')
    printer.fontsize(2,2)
    printer.text(u'%s\n\n' % _formatPrice(beleg.getNormalsumme()))

    zahlungen = beleg.getZahlungen()
    if len(zahlungen) > 0:
        printer.bold(False)
        printer.fontsize(1,1)
        for z in zahlungen:
            if (z['zahlart'] == 'return'):
                printer.text(u'zurück: %9s\n' % (z['zahlart'], _formatPrice(z['betrag'])))
            else:
                printer.text(u'Zahlung (%s): %9s\n' % (z['zahlart'], _formatPrice(z['betrag'])))

        if beleg.getZahlbetrag() > 0:
            printer.bold()
            printer.text('\n')
            printer.text(u'Restbetrag: ')
            printer.fontsize(2,2)
            printer.text(u'%s\n' % _formatPrice(beleg.getZahlbetrag()))


    printer.bold(False)
    printer.align('left')
    printer.fontsize(1, 1)
    printer.text('\n')
    
    printer.text('Satz         Netto        MwSt        Brutto\n' )
    for satz, u in ust.items():
        printer.text('%s:%02.1f%%   %9s   %9s      %9s\n' % (u['chr'], satz, _formatPrice(u['net']), _formatPrice(u['vatsum']), _formatPrice(u['gross'])))
    
    if beleg.getLiterzahl() > 0:
        printer.text('\n')
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % beleg.getLiterzahl())
    printer.text('\n')

    printer.align('center')
    printer.fontsize(1,1)    
    printer.text('%s\n' % (datetime.datetime.now().strftime('%d.%m.%Y / %H:%M:%S')))
    printer.text('USt-ID: DE239631414\n')
    printer.text('www.mosterei-wurst.de\n')
    printer.text('\n')

    if kontodaten:
        printer.text('\n')
        printer.fontsize(2,2)
        printer.bold(True)
        printer.align('center')
        printer.text('** Bankverbindung **\n')
        printer.align('left')
        printer.bold(False)
        printer.fontsize(1,1)
        printer.text('\n')
        printer.text('Name: ')
        printer.fontsize(1,2)
        printer.text('Bernd Wurst')
        printer.fontsize(1,1)
        printer.text('\n')
        printer.text('IBAN: ')
        printer.fontsize(1,2)
        printer.text('DE80 6029 1120 0041 3440 06')
        printer.fontsize(1,1)
        printer.text('\n')
        printer.text('BIC: ')
        printer.fontsize(1,2)
        printer.text('GENODES1VBK')
        printer.fontsize(1,1)
        printer.text('\n')
        printer.text('Bank: ')
        printer.fontsize(1,2)
        printer.text('Volksbank Backnang')
        printer.fontsize(1,1)
        printer.text('\n\n')
        printer.text('Bitte überweisen Sie den Gesamtbetrag\n'
                     'baldmöglichst auf unser Konto.\n'
                     'Vielen Dank!\n\n')

    printer.cut()

    return True


def BeleglisteThermo(belege, printer):
    if not printer:
        print ('Drucker nicht initialisiert!')
        return
    printer.reset()
    printer.fontsize(2,2)
    printer.text('Offene Posten\n')
    printer.text(datetime.date.today().strftime('%d.%m.%Y')+'\n\n')
    
    
    for beleg in belege:
        name = beleg.getKundenname()
        printer.align('left')
        printer.fontsize(3, 2)
        printer.bold()
        printer.text(name + '\n')
        printer.bold(False)
        printer.align('right')
        printer.fontsize(1,1)
        printer.text('Anzahl Paletten gesamt: ')
        printer.fontsize(1,1)
        printer.bold()
        printer.text('%i\n' % beleg.getPaletten())
        printer.bold(False)
        printer.fontsize(1,1)
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % beleg.getLiterzahl())
        if beleg.getAbholung():
            printer.text('Abholung: %s\n' % beleg.getAbholung())
        if beleg.getTelefon():
            telefon = set()
            for t in beleg.kunde.listKontakte():
                if t['typ'] in ['mobil', 'telefon']:
                    telefon.add(formatPhoneNumber(t['wert']))
            printer.text('Telefon: %s\n' % ' / '.join(telefon))
        printer.bold()
        printer.text(u'Gesamtbetrag: ')
        printer.fontsize(2,2)
        printer.text(u'%s\n\n' % _formatPrice(beleg.getSumme()))
    printer.text('\n\n')
    printer.cut()
    return True




if __name__ == '__main__':
    import sys
    sys.path.insert(0,'./src')
    from lib.Speicher import Speicher
    speicher = Speicher()
    beleg = speicher.getBeleg('a4931774-085c-4602-92f2-3f1f1cdce9be')
    RegalschildThermo(beleg)
    #BelegThermo(beleg)
