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

import datetime


from lib.Speicher import Speicher
from lib.Preisliste import Preisliste


def tagesstatistik(year = None):
    ret = {}
    speicher = Speicher(year)
    speicher.backend.db.execute('SELECT handle, liter, zeitpunkt, summe, preislisten_id, anzahl, einzelpreis, datum FROM posten CROSS JOIN beleg ON (posten.beleg=beleg.id) WHERE beleg.currentversion=1')
    data = speicher.backend.db.fetchall()
    currenthandle = None
    for line in data:
        datum = datetime.datetime.strptime(line['zeitpunkt'], "%Y-%m-%d %H:%M:%S.%f").date().isoformat()
        if datum not in ret.keys():
            ret[datum] = {'liter': 0,}
        id = line['preislisten_id']
        if id:
            if id in ret[datum].keys():
                ret[datum][id][0] += line['anzahl']
                ret[datum][id][1] += line['anzahl'] * line['einzelpreis']
            else:
                ret[datum][id] = [line['anzahl'], line['anzahl'] * line['einzelpreis']]
        if line['handle'] != currenthandle:
            ret[datum]['liter'] += line['liter']
            currenthandle = line['handle']
    return ret


def jahresstatistik(year = None):
    tage = tagesstatistik(year)
    ret = {}
    for tag in tage.values():
        for key, value in tag.items():
            if key not in ret.keys():
                ret[key] = value
            else:
                if key == 'liter':
                    ret[key] += value
                else:
                    ret[key][0] += value[0]
                    ret[key][1] += value[1]
    return ret


def ueberschuss_nach_preiskategorien(year = None):
    p = Preisliste()
    basis_5er = p.getPreis('5er', amount=10000)
    basis_10er = p.getPreis('10er', amount=10000)
    rabattstufen = p.rabattStufen('5er')
    ret = {}
    speicher = Speicher(year)
    speicher.backend.db.execute('SELECT liter, manuelle_liter, preislisten_id, anzahl, einzelpreis FROM posten INNER JOIN beleg ON (posten.beleg=beleg.id) WHERE beleg.currentversion=1')
    data = speicher.backend.db.fetchall()
    for line in data:
        kategorie = 0
        if line['manuelle_liter']:
            kategorie = line['manuelle_liter']
        else:
            for stufe in rabattstufen:
                if stufe[1] < line['liter']:
                    kategorie = stufe[1]
        if kategorie not in ret.keys():
            ret[kategorie] = 0.0 
        if line['preislisten_id'] == '5er':
            ret[kategorie] += line['anzahl'] * (line['einzelpreis'] - basis_5er)
        if line['preislisten_id'] == '10er':
            ret[kategorie] += line['anzahl'] * (line['einzelpreis'] - basis_10er)
    return ret
  


def umsatzstatistik(year = None):
    gesamtsumme = 0.0
    anzahl = 0
    speicher = Speicher(year)
    anonym_umsatz = 0.0
    rechnungen_summe = 0.0
    speicher.backend.db.execute('SELECT summe, rechnungsnummer, name FROM beleg WHERE beleg.currentversion=1')
    data = speicher.backend.db.fetchall()
    for line in data:
        if line['name']:
            anzahl += 1
            gesamtsumme += line['summe']
        else:
            anonym_umsatz += line['summe']
        if line['rechnungsnummer']:
            rechnungen_summe += line['summe']
    return (anzahl, gesamtsumme, anonym_umsatz, rechnungen_summe)


def html_tagesstatistik(year = None):
    stat = tagesstatistik(year)
    html = ''
    tage = sorted(list(stat.keys()))
    tage.reverse()
    pl = Preisliste()
    for datum in tage:
        html += '<h3>%s</h3>\n<table>' % datum
        html += '<tr><td>Liter</td><td>%s</td></tr>\n' % (stat[datum]['liter'])
        
        keys = sorted(list(stat[datum].keys()))
        keys.remove('liter')
        for key in keys:
            value = stat[datum][key]
            desc = pl.getBeschreibung(key)
            if desc:
                key = desc + ' (' + key + ')'   
            html += u'<tr><td>%s</td><td>%s</td><td>%.2f €</td></tr>\n' % (key, value[0], value[1])
        html += '</table>\n\n'
    return html


def html_jahresstatistik(year = None):
    stat = jahresstatistik(year)
    if len(stat) < 1:
        return ''
    
    # legacy
    values = {}
    numbers = {}
    for key, value in stat.items():
        if key == 'liter':
            values['liter'] = 0
            continue
        values[key] = value[1]
    for key, value in stat.items():
        if key == 'liter':
            numbers['liter'] = value
            continue
        numbers[key] = value[0]
    stat = numbers
    
    for key in ['liter', '5er', '10er', '5er_vk', '10er_vk', 
                '5er_gebraucht', '10er_gebraucht', '5er_abfuellung_vk', '10er_abfuellung_vk']:
        if key not in stat.keys():
            stat[key] = 0
    
    
    html = u''
    # Schöne Anzeige
    html += u'<p><strong>Liter gesamt:</strong> %i</p>\n' % stat['liter']
    
    anteil_5er = (float(stat['5er']*5) / (stat['5er']*5 + stat['10er']*10)) * 100
    anteil_10er = (float(stat['10er']*10) / (stat['5er']*5 + stat['10er']*10)) * 100
    
    html += u'<h4>Materialverbrauch</h4>'
    html += u'<table border="1">'
    html += u'<tr><td>Beutel 5l:</td><td>%i</td><td>(%.1f Kartons, %i%%)</td></tr>\n' % (stat['5er'], float(stat['5er'])/ 400, int(anteil_5er))
    html += u'<tr><td>Beutel 10l:</td><td>%i</td><td>(%.1f Kartons, %i%%)</td></tr>\n' % (stat['10er'], float(stat['10er'])/400, int(anteil_10er))
    karton_5er = stat['5er'] + stat['5er_abfuellung_vk'] - stat['5er_gebraucht']
    html += u'<tr><td>Kartons 5l:</td><td>%i</td><td>(%.1f Paletten)</td></tr>\n' % (karton_5er, float(karton_5er)/800)
    karton_10er = stat['10er'] + stat['10er_abfuellung_vk'] - stat['10er_gebraucht']
    html += u'<tr><td>Kartons 10l:</td><td>%i</td><td>(%.1f Paletten)</td></tr>\n' % (karton_10er, float(karton_10er)/400)
    try:
        html += u'<tr><td>Karton Rückläufer 5l:</td><td>%i</td><td>(%i%%)</td></tr>\n' % (stat['5er_gebraucht'], int((float(stat['5er_gebraucht'])/(stat['5er'] + stat['5er_vk']))*100))
        html += u'<tr><td>Karton Rückläufer 10l:</td><td>%i</td><td>(%i%%)</td></tr>\n' % (stat['10er_gebraucht'], int((float(stat['10er_gebraucht'])/(stat['10er'] + stat['10er_vk']))*100))
    except ZeroDivisionError:
        html += u'<tr><td colspan="3"><em>Zu wenig Daten...</em></td></tr>\n'
    
    html += u'</table>'
    
    zw_summe = 0
    tagesstat = tagesstatistik(year)
    tage = sorted(list(tagesstat.keys()))
    html += '<h4>Kumulierte Liter nach Tagen</h4>\n<table>'
    for tag in tage:
        zw_summe += tagesstat[tag]['liter']
        html += '<tr><td>%s</td><td>%i</td></tr>' % (tag, zw_summe)
    html += '</table>'
    
    tage_anzahl = 0
    for t in tage:
        if 'liter' in tagesstat[t] and tagesstat[t]['liter'] > 0:
            tage_anzahl += 1
    
    if tage_anzahl == 0:
        # Wenn keine Umsätze da sind, macht diese Statistik keinen Sinn.
        # (Führt sonst zu einem DIV0) 
        return html
    
    html += u'<h4>Umsatzstatistik</h4>\n'
    (anzahl, gesamtsumme, anonym_umsatz, rechnungen_summe) = umsatzstatistik(year)
    html += u'<dl><dt>Anzahl Kunden</dt><dd>%i</dd>\n' \
            u'<dt>Anzahl Arbeitstage</dt><dd>%i</dd>\n' \
            u'<dt>Umsatz auf Rechnung</dt><dd>%.2f €</dd>\n' \
            u'<dt>Gesamtumsatz</dt><dd>%.2f €</dd>\n' \
            u'<dt>davon Laufkundschaft</dt><dd>%.2f €</dd>\n' \
            u'<dt>Durchschn. Umsatz pro Kunde</dt><dd>%.2f €</dd>' \
            u'<dt>Durchschn. Umsatz pro Tag</dt><dd>%.2f €</dd>' \
            u'<dt>Durchschn. Liter pro Tag</dt><dd>%i</dd></dl>' \
            % (anzahl, tage_anzahl, rechnungen_summe, gesamtsumme + anonym_umsatz, anonym_umsatz, gesamtsumme / anzahl, gesamtsumme / tage_anzahl, stat['liter'] / tage_anzahl) 

    html += u'<h4>Gewinn gegenüber 500-Liter-Preis nach Preiskategorien</h4>\n<dl>\n'
    kategorien = ueberschuss_nach_preiskategorien(year)
    stufen = sorted(list(kategorien.keys()))
    for key in stufen:
        value = kategorien[key ]
        html += u'<dt>%s</dt><dd>%s</dd>\n' % (key, value)
    html += u'</dl>\n\n'

    html += u'<h4>Überweisungen</h4>\n<table>\n'
    ueberweisungen_summe = 0.0
    speicher = Speicher(year)
    speicher.backend.db.execute('SELECT zeitpunkt, bezahlt, zahlung, name, summe FROM beleg WHERE currentversion=1')
    data = speicher.backend.db.fetchall()
    for line in data:
        if not line['bezahlt'] and line['zahlung'] == 'ueberweisung':
            html += u'<tr><td>%s</td><td>%s</td><td>%.2f €</td></tr>\n' % (str(datetime.datetime.strptime(line['zeitpunkt'], "%Y-%m-%d %H:%M:%S.%f").date()), line['name'], line['summe']) 
            ueberweisungen_summe += line['summe']
    html += u'</table>'
    html += u'<p>Summe aller Überweisungen: %.2f €' % ueberweisungen_summe

    html += u'<h4>EC-Zahlungen</h4>\n<table>\n'
    ec_summe = 0.0
    zahlungen = Speicher(year).backend.listAlleZahlungen()
    for z in zahlungen:
        if z['zahlart'] == 'ec':
            b = Speicher(year).ladeBeleg(z['beleg'])
            html += u'<tr><td>%s</td><td>%s</td><td>%.2f €</td></tr>\n' % (str(datetime.datetime.strptime(z['timestamp'], "%Y-%m-%d %H:%M:%S.%f").date()), b.getKundenname(), z['betrag']) 
            ec_summe += z['betrag']
    html += u'</table>'
    html += u'<p>Summe aller EC-Zahlungen: %.2f €' % ec_summe

    # Alle Rohdaten
    html += u'<h4>Rohdaten</h4>\n<table>\n'
    pl = Preisliste()
    keys = sorted(list(stat.keys()))
    for key in keys:
        value = stat[key]
        desc = pl.getBeschreibung(key)
        if desc:
            desc = desc + ' (' + key + ')'   
        try:
            html += u'<tr><td>%s</td><td>%s</td><td>%.2f €</td></tr>\n' % (desc, value, values[key])
        except KeyError:
            pass
    html += u'</table>\n\n'
    
    return html


if __name__ == '__main__':
    import getpass, sys
    password = getpass.getpass('Code: ')


    s = Speicher()
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)
    from pprint import pprint
    pprint(tagesstatistik())
    pprint(ueberschuss_nach_preiskategorien())
    #pprint(jahresstatistik())
    
    #print (html_jahresstatistik())

