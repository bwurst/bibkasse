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

from datetime import date

PFAD = 'daten/rechnungen'


def findeNaechsteRechnungsnummer():
    files = sorted(list(os.listdir(PFAD)))
    try:
        max = int(files[-1].replace('.pdf', '').rsplit('-')[-1])
    except:
        max = 0
    return '%04i-%03i' % (date.today().year, max + 1)


def BelegRechnung(beleg, cash = False, originale = [], rechnungsadresse = None):
    if not beleg:
        return False
      
    adresse = beleg.kunde.getAdresse()
    if rechnungsadresse:
        adresse = rechnungsadresse
    
    from io import BytesIO
    file = BytesIO()
    invoice = Invoice()
    invoice.customerno = None
    invoice.salutation = None
    if adresse:
        invoice.addresslines = [x for x in adresse.split('\n') if x != '']
    else:
        invoice.addresslines = []
    invoice.setDate(date.today())
      
    data = beleg.getEntries()
    
    vatType = 'gross'
    tab = InvoiceTable(vatType=vatType)
    
    datumswerte = set()
    for item in data:
        datumswerte.add(item.getDatum())

    nur_heute = False        
    if len(datumswerte) == 1 and date.today() in datumswerte:
        nur_heute = True
        for item in data:
            tab.addItem(
                        {'count': float(item['anzahl']),
                         'unit': str(item['einheit']),
                         'subject': item['beschreibung'],
                         'price': float(item['einzelpreis']),
                         'vat': float(item.getSteuersatz()),
                         } 
                        )
    else:
        posten = {}
        for item in data:
            if item.getDatum() not in posten.keys():
                posten[item.getDatum()] = []
            posten[item.getDatum()].append(item)
        
        for datum in sorted(posten.keys()):
            entries = posten[datum]
            tab.addTitle("Leistung am %s:" % datum.strftime('%d. %m. %Y'))
            for item in entries:
                tab.addItem(
                    {'count': float(item['anzahl']),
                     'unit': str(item['einheit']),
                     'subject': item['beschreibung'],
                     'price': float(item['einzelpreis']),
                     'vat': float(item.getSteuersatz()),
                     } 
                    )
    invoice.parts.append(tab)
    
    invoice.cash = cash
    
    if invoice.cash:
        text = InvoiceText('Betrag dankend erhalten.')
        invoice.parts.append(text)
    else:
        text = InvoiceText('Bitte begleichen Sie diese Rechnung innerhalb von 2 Wochen nach Erhalt auf das unten angegebene Konto.')
        invoice.parts.append(text)
    
    if nur_heute:
        text = InvoiceText('Das Leistungsdatum entspricht dem Rechnungsdatum. Wir danken Ihnen, dass Sie unser Angebot in Anspruch genommen haben.')
        invoice.parts.append(text)
    else:
        text = InvoiceText('Wir danken Ihnen, dass Sie unser Angebot in Anspruch genommen haben.')
        invoice.parts.append(text)
    
    if invoice.official:
        invoice.id = findeNaechsteRechnungsnummer()
    else:
        invoice.id = '000'
    
    if invoice.id and len(originale) > 0:
        s = Speicher()
        for b in originale:
            b.setRechnungsdaten(date.today(), invoice.id)
            if invoice.cash:
                if not b.getPayed():
                    b.setBanktransfer(False)
                    b.setPayed(True)
                    s.speichereZahlung(b, 'bar', b.getZahlbetrag())
            else:
                b.setBanktransfer(True)
            s.speichereBeleg(b)
        
    pdfdata = InvoiceToPDF(invoice)
    filename = "%s/%s.pdf" % (PFAD, invoice.id) 
    f = open(filename, "wb")
    f.write(pdfdata)
    f.close()
    return filename


def rechnungsPDFDatei(beleg):
    if not beleg.isRechnung():
        return None
    filename = "%s/%s.pdf" % (PFAD, beleg.getRechnungsnummer()) 
    return filename


def storniereRechnung(beleg):
    datei = rechnungsPDFDatei(beleg)
    if not datei:
        return False
    if os.path.exists(datei):
        os.unlink(datei)
    s = Speicher()
    rechnungsnr = beleg.getRechnungsnummer()
    for b in s.listBelege():
        if b.isRechnung() and b.getRechnungsnummer() == rechnungsnr:
            b.setRechnungsdaten(None)
            b.setBanktransfer(False)
            b.setPayed(False)
            s.speichereBeleg(b)
    
