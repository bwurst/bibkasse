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

from lib.Speicher import Speicher
import datetime
import codecs
from lib.TSE import TSE, TSEException
from lib.Vorgang import Vorgang
from lib.BelegRechnung import BelegRechnung

def Kassenbeleg(vorgang, typ = "bon", zahlart = None, rechnungsadresse = None, tse_trxnum = None, tse_time_start = None, abbruch = False, storno = None):
    kassenbeleg = {
        "id": None,
        "vorgang": vorgang.ID,
        "vorgang_version": vorgang.version,
        "timestamp": datetime.datetime.now().timestamp(),
        "redatum": datetime.date.today(),
        "renr": None,
        "type": typ, # "bon", "a4", "rechnung"
        "tse_processtype": None,
        "tse_processdata": None,
        "tse_time_start": tse_time_start,
        "tse_time_end": None,
        "tse_trxnum": tse_trxnum,
        "tse_serial": None,
        "tse_sigcounter": None,
        "tse_signature": None,
        "kunde": {
            "kundennummer": None,
            "adresse": None
            },
        "posten": [
                #{"anzahl": 1, "einheit": "Stk", "beschreibung": "Test-Eintrag", "einzelpreis_netto": 0.0, "einzelpreis_brutto": 0.0, "mwst_satz": 19.0, "datum": None},
            ],
        "zahlart": None, # Wie wird der Rest bezahlt?
        "summen": {
            "summe": {
                "netto": 0.0,
                "brutto": 0.0,
                "mwst": 0.0,
                },
            "mwst": {
                #19.0: {"netto": 0.0, "brutto": 0.0, "mwst": 0.0}, 
                }
            },
        "zahlungen": [
                #{"id": 0, "type": "bar", "betrag": 0.0, "waehrung": "EUR", "datum": "...", "gegeben": 0.0, "zurueck": 0.0},
                #{"id": 0, "type": "ec", "betrag": 0.0, "waehrung": "EUR"},
            ],
        "referenz": storno,
        "brutto": 1, # ob die Rechnung mit Bruttobeträgen geschrieben wird
        "kassenbewegung": 0.0,
        "bemerkung": None,
        }
    
    adresse = vorgang.kunde.getAdresse()
    if rechnungsadresse:
        adresse = rechnungsadresse

    kassenbeleg['kunde']['kundennummer'] = vorgang.kunde.ID()
    kassenbeleg['kunde']['adresse'] = adresse

    data = vorgang.getEntries()
    
    posten = {}
    for item in data:
        if item.getDatum() not in posten.keys():
            posten[item.getDatum()] = []
        posten[item.getDatum()].append(item)
    
    for datum in sorted(posten.keys()):
        entries = posten[datum]
        for item in entries:
            netto = round(float(item['einzelpreis']) / (1+(float(item.getSteuersatz())/100)),3)
            p = {'anzahl': float(item['anzahl']),
                 'einheit': str(item['einheit']),
                 'beschreibung': item['beschreibung'],
                 'einzelpreis_netto': netto,
                 'einzelpreis_brutto': float(item['einzelpreis']),
                 'mwst_satz': float(item.getSteuersatz()),
                 'datum': item.getDatum(),
                 } 
            if storno:
                p['anzahl'] = -p['anzahl']
            kassenbeleg['posten'].append(p)
            sum = kassenbeleg['summen']["summe"]
            sum['netto'] += round(p['einzelpreis_netto'] * p['anzahl'], 3)
            sum['brutto'] += p['einzelpreis_brutto'] * p['anzahl']
            sum['mwst'] += round(p['einzelpreis_netto'] * float(item.getSteuersatz())/100 * p['anzahl'], 3)
            if not p['mwst_satz'] in kassenbeleg['summen']['mwst']:
                kassenbeleg['summen']['mwst'][p['mwst_satz']] = {"netto": 0.0, "brutto": 0.0, "mwst": 0.0}
            m = kassenbeleg['summen']['mwst'][p['mwst_satz']]
            m['netto'] += round(p['einzelpreis_netto'] * p['anzahl'], 3)
            m['brutto'] += p['einzelpreis_brutto'] * p['anzahl']
            m['mwst'] += round(p['einzelpreis_netto'] * float(item.getSteuersatz())/100 * p['anzahl'], 3)

    for zahl in vorgang.getZahlungen():
        z = {
            "id": zahl['id'],
            "type": zahl['zahlart'],
            "betrag": zahl['betrag'],
            "gegeben": zahl['gegeben'],
            "zurueck": zahl['zurueck'],
            "waehrung": "EUR",
            "zeitpunkt": zahl['timestamp'],
            "tse_trxnum": zahl['tse_trxnum'],
            }
        if storno:
            z['betrag'] = -z['betrag']
            z['gegeben'] = None
            z['zurueck'] = None
            z['tse_trxnum'] = None
        kassenbeleg['zahlungen'].append(z)
    
    if not vorgang.getPayed():
        kassenbeleg['zahlart'] = zahlart
    elif storno:
        kassenbeleg['zahlart'] = 'storno'

    bar = 0.0
    unbar = 0.0
    for z in kassenbeleg['zahlungen']: 
        if z['tse_trxnum']:
            # Diese Zahlung wurde bereits von der TSE signiert!
            continue
        z['tse_trxnum'] = kassenbeleg['tse_trxnum']
        if z['type'] in ['bar', 'transit']:
            bar += z['betrag']
        else:
            unbar += z['betrag']
    
    zahlungen = []
    if bar != 0.0:
        zahlungen.append('%.2f:Bar' % bar)
    if unbar != 0.0:
        zahlungen.append('%.2f:Unbar' % unbar)

    s = Speicher()
    # speichere vorhandene Daten um eine ID zu erzeugen
    kassenbeleg['id'] = s.speichereKassenbeleg(kassenbeleg)
    kassenbeleg['renr'] = 'R%04i-%04i' % (datetime.date.today().year, kassenbeleg['id'])
    
    vorgang.setRechnungsdaten(nummer=kassenbeleg['renr'], datum=kassenbeleg['redatum'])
    if storno:
        vorgang.setRechnungsdaten(None)
        vorgang.setPayed(False)
    s.speichereVorgang(vorgang)

    ums_19 = 0.0
    if 19.0 in kassenbeleg['summen']['mwst']:
        ums_19 = kassenbeleg['summen']['mwst'][19.0]['brutto']
    ums_7 = 0.0
    if 7.0 in kassenbeleg['summen']['mwst']:
        ums_7 = kassenbeleg['summen']['mwst'][7.0]['brutto']
    ums_107 = 0.0
    if 10.7 in kassenbeleg['summen']['mwst']:
        ums_107 = kassenbeleg['summen']['mwst'][10.7]['brutto']
    ums_55 = 0.0
    if 5.5 in kassenbeleg['summen']['mwst']:
        ums_55 = kassenbeleg['summen']['mwst'][5.5]['brutto']
    ums_0 = 0.0
    if 0.0 in kassenbeleg['summen']['mwst']:
        ums_0 = kassenbeleg['summen']['mwst'][0.0]['brutto']
    umsaetze = '%.2f_%.2f_%.2f_%.2f_%.2f' % (ums_19, ums_7, ums_107, ums_55, ums_0)
    
    kassenbeleg['tse_processtype'] = 'Kassenbeleg-V1'
    typ = 'Beleg'
    if kassenbeleg['zahlart'] == 'uebeweisung':
        typ = 'AVRechnung'
    if abbruch and not zahlungen:
        typ = 'AVBelegabbruch'
    kassenbeleg['tse_processdata'] = '%s^%s^%s' % (typ, umsaetze, '_'.join(zahlungen))

    kassenbeleg['kassenbewegung'] = bar

    # TSE Transaktion abschließen
    try:
        tse = TSE()
        assert kassenbeleg['tse_trxnum'] != None
        response = tse.transaction_finish(kassenbeleg['tse_trxnum'], kassenbeleg['tse_processdata'], kassenbeleg['tse_processtype'])
        del(tse)
        kassenbeleg['tse_time_end'] = response.logTime
        kassenbeleg['tse_serial'] = bytes(response.serialNumber).hex()
        kassenbeleg['tse_sigcounter'] = response.signatureCounter
        kassenbeleg['tse_signature'] = codecs.encode(response.signature, 'base64').decode()
    except TSEException:
        kassenbeleg['tse_signature'] = 'TSE ausgefallen!'
    except AssertionError:
        kassenbeleg['tse_signature'] = 'TSE ausgefallen!'

    # TSE-Ergebnisse speichern
    if zahlungen and not storno:
        for z in vorgang.getZahlungen():
            if not z['tse_trxnum']:
                s.updateZahlung(z['id'], kassenbeleg['tse_trxnum'])
    s.speichereKassenbeleg(kassenbeleg)

    return kassenbeleg



def KassenbelegStornieren(kb):
    tse_trxnum = None
    tse_time_start = None
    try:
        tse = TSE()
        response = tse.transaction_start('', '')
        tse_trxnum = response.transactionNumber
        tse_time_start = response.logTime
    except TSEException:
        pass
    
    s = Speicher()
    vorgang = s.ladeVorgang(kb['vorgang'])
    storno = Kassenbeleg(vorgang, 'storno', 'storno', tse_trxnum=tse_trxnum, tse_time_start=tse_time_start, storno=kb['id'])
    
    for z in s.getZahlungen(vorgang):
        s.loescheZahlung(z['id'])
    
    filename = BelegRechnung(storno)
    print("Storno: %s" % filename)
    return filename




if __name__ == '__main__':
    from lib.Vorgang import Vorgang
    import sys, getpass
    s = Speicher()
    password = getpass.getpass('Code: ')
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)

    tse_trxnum = None
    tse_time_start = None
    try:
        tse = TSE()
        response = tse.transaction_start('', '')
        tse_trxnum = response.transactionNumber
        tse_time_start = response.logTime
    except TSEException:
        pass


    b = Vorgang()
    b.newItem(10, '5er')
    b.newItem(10, '10er')
    b.newItem(10, 'frischsaft')
    
    b.setKunde(s.sucheKundeTelefon('7192936436')[0])
    s.speichereZahlung(b, 'ec', betrag=10)
    #s.speichereZahlung(b, 'bar', betrag=100.0, gegeben=101, zurueck=1)
    
    #b.setPayed(True)
    b = s.ladeVorgang(b.ID)

    kb = Kassenbeleg(b, 'bon', zahlart = 'ueberweisung', tse_trxnum = tse_trxnum, tse_time_start = tse_time_start)
    from pprint import pprint
    pprint(kb)
    
    try:
        del(tse)
    except:
        pass
    
    
    
    print(BelegRechnung(kb))
    