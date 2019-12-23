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


def AuftragHTML(auftrag, public=True):
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
    name = auftrag.getKundenname()
    html += '<h3>' + name + '</h3>'
    telefon = auftrag.kunde.getErsteTelefon()
    if auftrag.telefon:
        telefon = auftrag.telefon
    html += '<p>Telefon: ' + telefon + '</p>\n'
    
    if auftrag.lieferart == 'anhaenger':
        html += '<p><strong>Obst in Anhänger</strong><br>\nKennzeichen: <strong>' + \
                auftrag.kennz + '</strong></p>'
    elif auftrag.lieferart == 'gitterbox':
        gbstring = '1 Gitterbox'
        if auftrag.gbcount > 1:
            gbstring = '%i Gitterboxen' % auftrag.gbcount
        html += '<p>Obst ist in <strong>%s</strong></p>\n' % gbstring
    else:
        html += '<p>Kunde ist vor Ort</p>\n'
    
    gebraucht = auftrag.gebrauchte
    if not gebraucht:
        gebraucht = 'Keine'
    html += '<p>Gebrauchte: <strong>%s</strong></p>' % gebraucht

    neue = auftrag.neue
    if not neue:
        neue = 'Gemischt'
    html += '<p>Neue: <strong>%s</strong></p>' % neue

    if auftrag.frischsaft:
        html += '<p>Frischsaft: <strong>%s</strong></p>' % auftrag.frischsaft

    if auftrag.sonstiges:
        html += '<p><strong>Bemerkung:</strong><br>\n' + auftrag.sonstiges + '</p>\n'
        
    if auftrag.abholung:
        html += '<p>Abholung: %s</p>\n' % auftrag.abholung
     
    return html

