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

import re
import datetime

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



def KassenbelegThermo(kb, printer):
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
    for entry in kb['posten']:
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
        if entry['mwst_satz'] not in ust:
            ust[entry['mwst_satz']] = ust_idx
            ust_idx = chr(ord(ust_idx)+1)

        this_ust_char = ust[entry['mwst_satz']]
        
        printer.text(u'%6.0f' % entry['anzahl'])
        printer.fontsize(1,1)
        printer.text(u' %-8sx  %11s  =' % (entry['einheit'], _formatPrice(entry['einzelpreis_brutto'])))
        printer.text(u' %10s  %s\n' % (_formatPrice(entry['einzelpreis_brutto']* entry['anzahl']), this_ust_char))
        printer.text('\n')
    
    printer.align('right')
    printer.bold()
    printer.text(u'Gesamtbetrag: ')
    printer.fontsize(2,2)
    printer.text(u'%s\n' % _formatPrice(kb['summen']['summe']['brutto']))

    zahlungen = kb['zahlungen']
    if len(zahlungen) > 0:
        zsumme = 0.0
        printer.bold(False)
        printer.fontsize(1,1)
        for z in zahlungen:
            if z['type'] == 'bar':
                if z['gegeben'] and type(z['zurueck']) != type(None):
                    printer.text('gegeben: %9s\n' % (_formatPrice(z['gegeben']),))
                    printer.text('zurück: %9s\n' % (_formatPrice(z['zurueck']),))
                else:
                    printer.text('Barzahlung: %9s\n' % (_formatPrice(z['betrag']),))
            else:
                printer.text(u'Zahlung (%s): %9s\n' % (z['type'], _formatPrice(z['betrag'])))
            zsumme += z['betrag']

        rest = kb['summen']['summe']['brutto'] - zsumme
        if kb['zahlart'] and rest > 0:
            printer.bold()
            printer.text('\n')
            printer.text(u'Restbetrag: ')
            printer.fontsize(2,2)
            printer.text(u'%s\n' % _formatPrice(rest))


    printer.bold(False)
    printer.align('left')
    printer.fontsize(1, 1)
    printer.text('\n')
    
    printer.text('Satz         Netto        MwSt        Brutto\n' )
    for satz, c in ust.items():
        printer.text('%s:%02.1f%%   %9s   %9s      %9s\n' % (c, satz, _formatPrice(kb['summen']['mwst'][satz]['netto']), _formatPrice(kb['summen']['mwst'][satz]['mwst']), _formatPrice(kb['summen']['mwst'][satz]['brutto'])))
    
    printer.text('\n')
    printer.align('center')
    printer.fontsize(1,1)
    printer.text('Bon-Nr. %s\n' % kb['renr'])    
    printer.text('%s\n' % (datetime.datetime.now().strftime('%d.%m.%Y / %H:%M')))
    printer.text('USt-ID: DE239631414\n')
    printer.text('www.mosterei-wurst.de\n')
    
    printer.align('left')
    printer.text('\n')
    if kb['tse_processtype'] == 'Kassenbeleg-V1':
        width = 48
        signature = kb['tse_signature'].replace('\n', '')
        signature = '\n'.join([signature[0+i:width+i] for i in range(0, len(signature), width)])
        serial = kb['tse_serial']
        if serial:
            # Wenn die TSE nicht verfügbar ist, kommt hier nichts
            serial = '\n'.join([serial[0+i:width+i] for i in range(0, len(serial), width)])
        if kb['tse_time_start']:
            printer.text('Daten der TSE:\n'
                         'Beginn: %s\n'
                         'Ende: %s\n'
                         'TRX-Nr.: %s, Sig-Zähler: %s\n' 
                         'Serial:\n'
                         '%s\n' 
                         'Signatur:\n'
                         '%s\n'
                         % (kb['tse_time_start'], kb['tse_time_end'], kb['tse_trxnum'], kb['tse_sigcounter'], serial, signature))
        else:
            printer.text('Zum Zeitpunkt der Bon-Erstellung\nwar keine TSE verfügbar!\n')
    
    printer.cut()
    return True




def RegalschildThermo(vorgang, printer):
    if not printer:
        print ('Drucker nicht initialisiert!')
        return
    printer.reset()
    name = vorgang.getKundenname()
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
    printer.text('%i\n' % vorgang.getPaletten())
    printer.bold(False)
    printer.fontsize(1,1)
    if vorgang.getLiterzahl() > 0:
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % vorgang.getLiterzahl())
    if vorgang.getAbholung():
        printer.text('Abholung: %s\n' % vorgang.getAbholung())
    #printer.ean13(vorgang.getEAN13())
    printer.cut()
    return True
    


def VorgangThermo(vorgang, printer):
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
    for entry in vorgang.getEntries():
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
    printer.text(u'%s\n\n' % _formatPrice(vorgang.getNormalsumme()))

    printer.bold(False)
    printer.align('left')
    printer.fontsize(1, 1)
    printer.text('\n')
    
    printer.text('Satz         Netto        MwSt        Brutto\n' )
    for satz, u in ust.items():
        printer.text('%s:%02.1f%%   %9s   %9s      %9s\n' % (u['chr'], satz, _formatPrice(u['net']), _formatPrice(u['vatsum']), _formatPrice(u['gross'])))
    
    if vorgang.getLiterzahl() > 0:
        printer.text('\n')
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % vorgang.getLiterzahl())
    printer.text('\n')

    printer.align('center')
    printer.fontsize(1,1)    
    printer.text('%s\n' % (datetime.datetime.now().strftime('%d.%m.%Y / %H:%M:%S')))
    printer.text('USt-ID: DE239631414\n')
    printer.text('www.mosterei-wurst.de\n')

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
    
    
    for vorgang in belege:
        name = vorgang.getKundenname()
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
        printer.text('%i\n' % vorgang.getPaletten())
        printer.bold(False)
        printer.fontsize(1,1)
        printer.text('Gesamtmenge Bag-in-Box: %i Liter\n' % vorgang.getLiterzahl())
        if vorgang.getAbholung():
            printer.text('Abholung: %s\n' % vorgang.getAbholung())
        if vorgang.getTelefon():
            telefon = set()
            for t in vorgang.kunde.listKontakte():
                if t['typ'] in ['mobil', 'telefon']:
                    telefon.add(formatPhoneNumber(t['wert']))
            printer.text('Telefon: %s\n' % ' / '.join(telefon))
        printer.bold()
        printer.text(u'Gesamtbetrag: ')
        printer.fontsize(2,2)
        printer.text(u'%s\n\n' % _formatPrice(vorgang.getSumme()))
    printer.text('\n\n')
    printer.cut()
    return True




if __name__ == '__main__':
    import sys
    sys.path.insert(0,'./src')
    from lib.Speicher import Speicher
    speicher = Speicher()
    vorgang = speicher.getVorgang('a4931774-085c-4602-92f2-3f1f1cdce9be')
    RegalschildThermo(vorgang)
    #VorgangThermo(vorgang)
