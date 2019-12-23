#!/usr/bin/python3
# -* coding: utf-8 *-
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

import getpass, sys, os.path, datetime
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), 'src'))

from lib.SQLiteSpeicher import SQLiteSpeicherBackend as Speicher

year = datetime.date.today().year
if len(sys.argv) > 1:
    year = sys.argv[1]
    
print ('Bearbeite %s' % (year))  
s = Speicher(year=year)
try:
    s.openDB()
except ValueError:
    password = getpass.getpass('Code: ')
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)

print ('lade alle Belege dieses Jahres...')
zahlungen = s.listAlleZahlungen()
    

    


print ('sortiere nach Datum')
zahlungen_nach_datum = {}
for z in zahlungen:
    dat = z['timestamp'][:10]
    if dat in zahlungen_nach_datum.keys():
        zahlungen_nach_datum[dat].append(z)
    else:
        zahlungen_nach_datum[dat] = [z,]


daten = sorted(list(zahlungen_nach_datum.keys()))
barsumme = 0.0
ecsumme = 0.0
ueberweisungssumme = 0.0

statistik = {}
liter = 0

for datum in daten:
    summe = 0.0
    bar = 0.0
    ec = 0.0
    ueberweisung = 0.0
    for z in zahlungen_nach_datum[datum]:
        if z['zahlart'] == 'ueberweisung':
            ueberweisung += z['betrag']
        elif z['zahlart'] == 'ec':
            ec += z['betrag']
        else:
            bar += z['betrag']
        beleg = s.ladeBeleg(z['beleg'])
        liter += beleg.getLiterzahl()
        for eintrag in beleg.getEntries():
            id = eintrag.preislistenID
            if id:
                if id not in statistik.keys():
                    statistik[id] = {'anzahl': 0, 'summe': 0}
                statistik[id]['anzahl'] += eintrag['anzahl']
                statistik[id]['summe'] += eintrag.getSumme()

    print (u'%s: %.2f € bar + %.2f € EC + %.2f € Überweisung = %.2f € gesamt' % (datum, bar, ec, ueberweisung, (bar+ec+ueberweisung)))
    barsumme += bar
    ecsumme += ec
    ueberweisungssumme += ueberweisung

print ('='*50)
print ('Gesamt: %.2f € bar + %.2f € EC + %.2f € Überw. = %.2f € Umsatz' % (barsumme, ecsumme, ueberweisungssumme, (barsumme + ecsumme + ueberweisungssumme)))

for item, number in statistik.items():
    print ('%-30s: %5i / %.2f' % (item, number['anzahl'], number['summe']))
print ('Gesamt: %i Liter' % liter)
