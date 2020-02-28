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

import os

from lib.Invoice.InvoiceObjects import Invoice, InvoiceTable, InvoiceText
#from invoice.InvoiceToText import *
from lib.Invoice.InvoiceToPDF import InvoiceToPDF
from lib.Speicher import Speicher
from lib.helpers import getMoneyValue
from datetime import date

PFAD = 'daten/rechnungen'


def BelegRechnung(kb):
    invoice = Invoice()
    if kb['type'] == 'storno':
        s = Speicher()
        storno = s.getKassenbeleg(kb['referenz'])
        invoice.title = 'Rechnungskorrektur zu %s' % storno['renr'] 
    invoice.customerno = kb['kunde']['kundennummer']
    invoice.salutation = None
    if kb['kunde']['adresse']:
        invoice.addresslines = [x for x in kb['kunde']['adresse'].split('\n') if x != '']
    else:
        invoice.addresslines = []
    invoice.setDate(kb['redatum'])
      
    data = kb['posten']
    
    vatType = 'gross'
    tab = InvoiceTable(vatType=vatType)
    
    datumswerte = set()
    for item in data:
        datumswerte.add(item['datum'])

    nur_heute = False        
    if len(datumswerte) == 1 and date.today() in datumswerte:
        nur_heute = True
        for item in data:
            tab.addItem(
                        {'count': float(item['anzahl']),
                         'unit': str(item['einheit']),
                         'subject': item['beschreibung'],
                         'price': float(item['einzelpreis_brutto']),
                         'vat': float(item['mwst_satz']),
                         } 
                        )
    else:
        posten = {}
        for item in data:
            if item['datum'] not in posten.keys():
                posten[item['datum']] = []
            posten[item['datum']].append(item)
        
        for datum in sorted(posten.keys()):
            entries = posten[datum]
            tab.addTitle("Leistung am %s:" % datum.strftime('%d. %m. %Y'))
            for item in entries:
                tab.addItem(
                    {'count': float(item['anzahl']),
                     'unit': str(item['einheit']),
                     'subject': item['beschreibung'],
                     'price': float(item['einzelpreis_brutto']),
                     'vat': float(item['mwst_satz']),
                     } 
                    )

    for z in kb['zahlungen']:
        if z['type'] == 'bar':
            if z['gegeben'] and type(z['zurueck']) != type(None):
                tab.addPayment(type='cash', amount=z['gegeben'], date=z['zeitpunkt'].date())
                tab.addPayment(type='return', amount=z['zurueck'], date=z['zeitpunkt'].date())
            else:
                tab.addPayment(type='cash', amount=z['betrag'], date=z['zeitpunkt'].date())
        else:
            tab.addPayment(type=z['type'], amount=z['betrag'], date=z['zeitpunkt'].date())

    invoice.parts.append(tab)
    
        
    if not kb['zahlart']:
        text = InvoiceText('Betrag dankend erhalten.')
        invoice.parts.append(text)

    if kb['tse_processtype'] == 'Kassenbeleg-V1':
        text = InvoiceText('Zum Zeitpunkt der Belegerstellung war keine technische Sicherungseinrichtung verfügbar!')
        if kb['tse_time_start']:
            text = InvoiceText('Daten der technischen Sicherungseinrichtung:\n' 
                               'Beginn des Vorgangs: %s, Ende des Vorgangs: %s\n'
                               'Seriennummer: %s\n' 
                               'Transaktionsnummer: %s, Signaturzähler: %s\n' 
                               'Signatur:\n'
                               '%s'
                               % (kb['tse_time_start'], kb['tse_time_end'], kb['tse_serial'], kb['tse_trxnum'], kb['tse_sigcounter'], kb['tse_signature']))
        invoice.parts.append(text)
        
    if kb['zahlart'] == 'ueberweisung':
        text = InvoiceText('Bitte begleichen Sie diese Rechnung innerhalb von 2 Wochen nach Erhalt auf das unten angegebene Konto.')
        invoice.parts.append(text)
    
    if nur_heute:
        text = InvoiceText('Das Leistungsdatum entspricht dem Rechnungsdatum. Wir danken Ihnen, dass Sie unser Angebot in Anspruch genommen haben.')
        invoice.parts.append(text)
    else:
        text = InvoiceText('Wir danken Ihnen, dass Sie unser Angebot in Anspruch genommen haben.')
        invoice.parts.append(text)
    
    invoice.id = kb['renr']
    
    pdfdata = InvoiceToPDF(invoice)
    filename = "%s/%s.pdf" % (PFAD, invoice.id) 
    f = open(filename, "wb")
    f.write(pdfdata)
    f.close()
    return filename


def rechnungsPDFDatei(vorgang):
    if not vorgang.isRechnung() or vorgang.isPayed():
        return None
    
    filename = "%s/%s.pdf" % (PFAD, vorgang.getRechnungsnummer()) 
    return filename

