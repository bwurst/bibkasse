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

from lib.SQLiteSpeicher import SQLiteSpeicherBackend
import datetime

import traceback


class Speicher(object):
    __backend = {}
    __password = None
    
    def __init__(self, year = None, authtoken = None, dbpath = None):
        self.authtoken = authtoken
        if not self.authtoken in self.__class__.__backend.keys():
            self.__class__.__backend[self.authtoken] = {'storage': {}, 'password': None}
        if year:
            self.year = str(year)
        else:
            self.year = str(datetime.date.today().year)

        self.storage = self.__class__.__backend[self.authtoken]['storage']
        if not self.year in self.storage.keys():
            try:
                self.storage[self.year] = SQLiteSpeicherBackend(self.year, dbpath=dbpath)
                if self.storage[self.year].is_unlocked():
                    self.storage[self.year].initialize()
            except ValueError as e:
                if self.year == str(datetime.date.today().year):
                    raise e
            print ('initialized %s for %s' % (self.storage[self.year].__class__.__name__, self.year))
        self.backend = self.storage[self.year]
                
    def unmount(self): 
        return self.backend.unmount()

    def list_years(self):
        SQLiteYears = SQLiteSpeicherBackend.list_years()
        return list(set(SQLiteYears))
    
    def list_users(self):
        return self.backend.list_users()
    
    def set_user_password(self, userid, username, password):
        return self.backend.set_user_password(userid, username, password)

    def add_user(self, username, password):
        return self.backend.add_user(username, password)

    def get_current_user(self):
        return self.backend.get_current_user()

    def change_password(self, oldpassword, newpassword):
        result = self.backend.change_password(oldpassword, newpassword)
        if result:
            self.__class__.__backend[self.authtoken]['password'] = newpassword
        return result
    
    def check_password(self, password):
        result = self.backend.check_password(password)
        if result:
            self.__class__.__backend[self.authtoken]['password'] = password
        return result

    def is_unlocked(self):
        return self.backend.is_unlocked()

    def lock(self):
        return self.backend.lock()
        self.__class__.__backend[self.authtoken]['password'] = None

    def kundenname(self, handle):
        vorgang = self.backend.getVorgang(handle)
        if vorgang:
            return vorgang.getKundenname()
        
    def listVorgaenge(self):
        return self.backend.listVorgaenge()

    def listVorgaengeUnbezahlt(self, postponed=False):
        return self.backend.listVorgaengeUnbezahlt(postponed=postponed)

    def listVorgaengeLastPayed(self, num=8):
        return self.backend.listVorgaengeLastPayed(num)

    def listVorgaengeByDateAsc(self):
        return self.backend.listVorgaengeByDateAsc()

    def listVorgaengeByDateDesc(self):
        return self.backend.listVorgaengeByDateDesc()

    def listVorgaengeByName(self):
        return self.backend.listVorgaengeByName()

    def listVorgaengeByKunde(self, kunde):
        return self.backend.listVorgaengeByKunde(kunde)
    
    def listVorgaengeByNameFilter(self, searchstring):
        return self.backend.listVorgaengeByNameFilter(searchstring)

    def listVorgaengeByAmount(self):
        return self.backend.listVorgaengeByAmount()

    def getBioKunden(self):
        return self.backend.getBioKunden()

    def listeKundennamen(self):
        return self.backend.listeKundennamen()
    
    def listeRechnungsadressen(self):
        return self.backend.listeRechnungsadressen()
    
    def speichereAlteKunden(self, liste):
        return self.backend.speichereAlteKunden(liste)
    
    def speichereAlteRechnungsadressen(self, liste):
        return self.backend.speichereAlteRechnungsadressen(liste)
    
    def getVorgang(self, handle):
        return self.backend.getVorgang(handle)

    def getVorgangVersionen(self, handle):
        return self.backend.getVorgangVersionen(handle)

    def ladeVorgang(self, handle, version = None):
        return self.backend.ladeVorgang(handle=handle, version=version)
    
    def speichereVorgang(self, vorgang):
        return self.backend.speichereVorgang(vorgang)
    
    def speichereAnruf(self, rechnung, ergebnis, bemerkung):
        return self.backend.speichereAnruf(rechnung, ergebnis, bemerkung)
    
    def getAnrufe(self, rechnung):
        return self.backend.getAnrufe(rechnung)
    
    def loescheVorgang(self, rechnung):
        return self.backend.loescheVorgang(rechnung)
    
    def speichereZahlung(self, vorgang, zahlart, betrag, gegeben = None, zurueck = None, bemerkung = None):
        return self.backend.speichereZahlung(vorgang, zahlart, betrag, gegeben, zurueck, bemerkung)
    
    def updateZahlung(self, zahlung, tse_trxnum):
        return self.backend.updateZahlung(zahlung, tse_trxnum)

    def loescheZahlung(self, zahlung):
        return self.backend.loescheZahlung(zahlung)

    def getZahlungen(self, vorgang):
        return self.backend.getZahlungen(vorgang)

    def listZahlungenTagesjournal(self, datum = None):
        return self.backend.listZahlungenTagesjournal(datum)
    
    def speichereKassenbeleg(self, kassenbeleg):
        return self.backend.speichereKassenbeleg(kassenbeleg)
    
    def getKassenbeleg(self, id=None, renr=None):
        return self.backend.getKassenbeleg(id, renr)
    
    def listKassenbelege(self, erster=None, letzter=None):
        return self.backend.listKassenbelege(erster, letzter)
    
    def getAbschluss(self, from_date, to_date):
        return self.backend.getAbschluss(from_date, to_date)
    
    def getLetzterAbschluss(self):
        return self.backend.getLetzterAbschluss()
    
    def speichereAbschluss(self, abschluss):
        return self.backend.speichereAbschluss(abschluss)
    
    def speichereBioLieferschein(self, data):
        return self.backend.speichereBioLieferschein(data)

    def ladeBioLieferschein(self, id):
        return self.backend.ladeBioLieferschein(id)

    def getBioLieferscheine(self, kunde=None, fertige=False):
        return self.backend.getBioLieferscheine(kunde, fertige)
    
    def speichereKunde(self, kunde):
        return self.backend.speichereKunde(kunde)

    def ladeKunde(self, nr):
        return self.backend.ladeKunde(nr)

    def sucheKunde(self, such):
        return self.backend.sucheKunde(such)

    def sucheKundeTelefon(self, such):
        return self.backend.sucheKundeTelefon(such)

    def speichereAuftrag(self, auftrag):
        return self.backend.speichereAuftrag(auftrag)

    def ladeAuftrag(self, handle = None, version=None, sqlresult=None):
        return self.backend.ladeAuftrag(handle, version, sqlresult)
    
    def getAuftragVersionen(self, handle):
        return self.backend.getAuftragVersionen(handle)

    def listAuftraege(self):
        return self.backend.listAuftraege()

    def listAuftraegeByDateDesc(self):
        return self.backend.listAuftraegeByDateDesc()
    
    def listAuftraegeByDateAsc(self):
        return self.backend.listAuftraegeByDateAsc()
    
    def listAuftraegeByKunde(self, kunde):
        return self.backend.listAuftraegeByKunde(kunde)
    
    def listAuftraegeByName(self):
        return self.backend.listAuftraegeByName()
        
    def listOffeneAuftraege(self):
        return self.backend.listOffeneAuftraege()


if __name__ == '__main__':

#    from Beleg import Beleg
#    i = Beleg()
#
#    i.kunde.setName('Müller')
#    _5er = i.newItem(10, '5er')
#    _10er = i.newItem(10, '10er')
#    gebraucht_5er = i.newItem(10, 'frischsaft')
#    
#    print (i) 
#    
    s = Speicher()
    i = s.listVorgaenge()[0]
    print (i)
    #s.speichereVorgang(i)
