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

from .Kunde import Kunde
from lib.helpers import formatPhoneNumber
from itertools import count


StatusUnvollstaendig = -1
StatusOffen = 0
StatusInBearbeitung = 1
StatusErledigt = 2
StatusBezahlt = 3


PFAD_JSON = 'daten/auftraege'


class Auftrag(object):
    def __init__(self, kunde=None):
        self.ID = None
        self.version = 0
        if not kunde:
            kunde = Kunde()
        self.kunde = kunde
        self.erledigt = False
        self.abholung = None
        self.quelle = 'online' # 'online', 'papier', 'termin'
        self.obst = 'kunde' # 'kunde', 'verkauf'
        self.obstmenge = None # Freitext-Feld ("300 kg")
        self.obstart = None # 'birne', 'apfel', 'quitte', ...
        self.angeliefert = False
        self.lieferart = 'termin' # 'anhaenger', 'gitterbox', 'termin'
        self.gbcount = None # Anzahl Gitterboxen
        self.kennz = None # Kennzeichen des Anhängers
        self.gebrauchte = None # '5er', '10er', None
        self.neue = None # '3er', '5er', '10er', None
        self.neue3er = None # Bei Aufteilung, wie viele von welcher Sorte. 
        self.neue5er = None # self.neue definiert was mit dem Rest passiert
        self.neue10er = None # Bei "halbe halbe" soll self.neue auf None stehen und das Mischungsverhältnis an den Einzelgrößen festgelegt werden.
        self.sonstiges = None # Freitext-Feld
        self.frischsaft = None
        self.telefon = ''
        self.zeitpunkt = None
        self.changed = False
        self.status = None # "
        self.anmerkungen = None # Bemerkungen allgemein
        self.bio = False
        self.bio_lieferschein = None


    def set(self, key, value):
        setattr(self, key, value)

    def getKundenname(self):
        if not self.kunde:
            return ''
        return self.kunde.getName()
    

def import_auftraege():
    import json
    import os, os.path
    from lib.Speicher import Speicher
    speicher = Speicher()
    assert speicher.is_unlocked(), 'Speicher ist gesperrt!'
    for filename in os.listdir(PFAD_JSON):
        with open(os.path.join(PFAD_JSON, filename), 'r') as f:
            data = json.load(f)
        
        kunde = None 
        if data['kundennr']:
            kunde = speicher.ladeKunde(data['kundennr'])
        else:
            kunde = Kunde()
            telefon = formatPhoneNumber(data['phone'])
            typ = 'telefon'
            if telefon.startswith('01'):
                typ = 'mobile'
            kunde.addKontakt(typ, telefon)
        kunde['vorname'] = data['fname']
        kunde['nachname'] = data['lname']
        kunde['strasse'] = data['address']
        kunde['plz'] = data['zip']
        kunde['ort'] = data['city']

        # Finde heraus, ob es diesen Auftrag schon gibt.
        versionen = speicher.getAuftragVersionen(data['handle'])
        if versionen:
            auftrag = speicher.ladeAuftrag(data['handle'])
        else:
            auftrag = Auftrag(kunde)
            
        mappings = {
            'source': 'quelle',
            'angeliefert': 'angeliefert',
            'handle': 'ID',
            'lieferart': 'lieferart',
            'gbcount': 'gbcount',
            'kennz': 'kennz',
            'kartons': 'gebrauchte',
            'neue': 'neue',
            'sonstiges': 'sonstiges',
            'frischsaft': 'frischsaft',
            'anmerkungen': 'anmerkungen',
            }
        for key1, key2 in mappings.items():
            if key1 in data:
                auftrag.set(key2, data[key1])
        if 'date' in data:
            auftrag.zeitpunkt = data['date'] 
        if not data['complete']:
            auftrag.status = -1
        else:
            auftrag.status = 0
    
        speicher.speichereAuftrag(auftrag)
        os.unlink(os.path.join(PFAD_JSON, filename))
    
    