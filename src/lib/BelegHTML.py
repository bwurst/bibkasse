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

from lib.helpers import getMoneyValue 
from lib.Speicher import Speicher


def BelegHTML(vorgang, public=True):
    fussnoten = {}
    def fussnote(msg):
        candidate = 1
        while candidate in fussnoten:
            if fussnoten[candidate] == msg:
                return u'<sup style="color: red;">%i</sup>' % candidate
            candidate += 1
        fussnoten[candidate] = msg
        return u'<sup style="color: red;">%i</sup>' % candidate
    
    html = ''
    if not public:
        name = vorgang.getKundenname()
        html += '<h3>' + name + '</h3>\n'
        
        html += '<p>&nbsp;</p>\n'
    
    datumswerte = set()
    for item in vorgang.getEntries():
        datumswerte.add(item.getDatum())
        
    posten = {}
    for item in vorgang.getEntries():
        if item.getDatum() not in posten.keys():
            posten[item.getDatum()] = []
        posten[item.getDatum()].append(item)
    for datum in sorted(posten.keys()):
        entries = posten[datum]
        if len(datumswerte) > 1:
            html += "<strong>Leistung vom %s</strong>\n" % datum.strftime('%d. %m. %Y')
        for entry in entries:
            subject = entry['beschreibung']
            if not entry.autoupdate:
                subject = subject+fussnote('Kein Update aus der Preisliste')
            if not entry.preisliste_link:
                subject = subject+fussnote('Manuell eingegebener Artikel')
            html += '<p><strong>%s</strong></p>\n' % subject
                
            
            html += '<pre>'
            if entry['anzahl'] != 1 or entry['einheit'] not in ['', 'Psch.']:
                html += u'%6.0f' % entry['anzahl']
                ep = getMoneyValue(entry.getNormalpreis())
                fn = ''
                if not entry.istStandardpreis():
                    fn += fussnote('Manuell gesetzter Preis')
                elif entry.getRabattstufe() != entry.getAutomatischeRabattstufe():
                    fn += fussnote('Manuell gesetzte Rabattstufe')
                html += u' %-8sx %10s%s  =' % (entry['einheit'], ep, fn)
            else:
                html += ' '*32
            html += u'   %11s (%4.1f%%)</pre>\n' % (getMoneyValue(entry.getNormalsumme()), entry.getSteuersatz())
    
    html += u'<p style="font-size: 25pt; margin-top: 2em; font-weight: bold;">Gesamtbetrag: &nbsp; &nbsp; %11s </p>\n' % getMoneyValue(vorgang.getNormalsumme())

    zahlungen = vorgang.getZahlungen()
    if len(zahlungen) > 0:
        for z in zahlungen:
            bemerkung = ''
            if z['bemerkung']:
                bemerkung = ' (%s)' % z['bemerkung']
            html += u'<p>Zahlung (%s) am %s%s: %11s</p>' % (z['zahlart'], z['timestamp'], bemerkung, getMoneyValue(z['betrag']))
        html += u'<p style="font-size: 25pt; font-weight: bold;">Restbetrag: &nbsp; &nbsp; %11s </p>\n' % getMoneyValue(vorgang.getZahlbetrag())
        

    html += '<p>Gesamtmenge Bag-in-Box: %i Liter</p>\n' % vorgang.getLiterzahl()
    if not public:
        html += '<hr />'
        html += '<p>Anzahl Paletten: <strong>%i</strong></p>\n' % vorgang.getPaletten()
        if vorgang.getAbholung():
            html += '<p>Abholung: %s</p>\n' % vorgang.getAbholung()
        if vorgang.getTelefon():
            html += '<p>Telefon: %s</p>\n' % vorgang.getTelefon()

        if vorgang.getPayed():
            html += u'<p><strong>*** BEZAHLT ***</strong></p>'

        s = Speicher()
        anrufe = s.getAnrufe(vorgang)
        for anruf in anrufe:
            if anruf['ergebnis'] == 'erreicht':
                html += '<p>Anruf %s - Erreicht - %s</p>\n' % (anruf['timestamp'],anruf['bemerkung'])
            elif anruf['ergebnis'] == 'ab':
                html += '<p>Anruf %s - AB</p>\n' % (anruf['timestamp'],)
            elif anruf['ergebnis'] == 'nichterreicht':
                html += '<p>Anruf %s - NICHT erreicht</p>\n' % (anruf['timestamp'],)
            else:
                html += '<p>Anruf %s - %s</p>\n' % (anruf['ergebnis'], anruf['timestamp'])


    for key, msg in fussnoten.items():
        html += '<p>%i: %s</p>' % (key, msg)
        

    return html

