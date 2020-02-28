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

import datetime, hashlib

class VorgangDummy(object):
    def __init__(self):
        self.ID = None
        self.__manuelleLiterzahl = None
        self.__kunde = {'name': '',
                        'adresse': None
                        }
        self.abholung = ''
        self.telefon = ''
        self.__zeitpunkt = None
        self.paletten = 1
        self.rechnungsDaten = None
        self.banktransfer = False
        self.payed = False
        self.status = None
        self.__literzahl = 0
        self.__summe = 0.0

    def setID(self, ID):
        self.ID = ID
        
    def isRechnung(self):
        return (self.rechnungsDaten != None)
    
    def getRechnungsdatum(self):
        if not self.isRechnung():
            return None
        return self.rechnungsDaten[0]
    
    def getRechnungsnummer(self):
        if not self.isRechnung():
            return None
        return self.rechnungsDaten[1]
    
    def setRechnungsdaten(self, datum, nummer = None):
        if not datum or not nummer or type(datum) != datetime.date:
            self.rechnungsDaten = None
        else:
            self.rechnungsDaten = (datum, str(nummer))

    def setManuelleLiterzahl(self, liter):
        try:
            if self.__manuelleLiterzahl is None and liter is None:
                # Es hat sich nichts geändert!
                return
            if self.__manuelleLiterzahl == int(liter):
                # Es hat sich nichts geändert!
                return
        except TypeError:
            pass
        try:
            self.__manuelleLiterzahl = int(liter)
        except:
            self.__manuelleLiterzahl = None
        

    def getManuelleLiterzahl(self):
        return self.__manuelleLiterzahl
    
    def getLiterzahl(self):
        return self.__literzahl
    
    def getSumme(self):
        return self.__summe

    def setKundenname(self, kundenname):
        if kundenname is None:
            kundenname = ''
        self.__kunde['name'] = str(kundenname).strip() 
        self.changed = True
    
    def setAdresse(self, adresse):
        if adresse is None:
            self.__kunde['adresse'] = None
        elif str(adresse).strip() == '':
            self.__kunde['adresse'] = None
        else:
            self.__kunde['adresse'] = str(adresse).strip()
        self.changed = True
    
    def getAdresse(self):
        return self.__kunde['adresse']
    
    def getKunde(self):
        return self.__kunde
    
    def getKundenname(self):
        if 'name' in self.__kunde:
            return self.__kunde['name']
        else:
            return ''
    
    def setBanktransfer(self, value):
        if value:
            self.banktransfer = True
            self.setPayed(False)
        else:
            self.banktransfer = False
    
    def getBanktransfer(self):
        return self.banktransfer

    def setPayed(self, value):
        if value:
            self.payed = True
            self.setBanktransfer(False)
        else:
            self.payed = False
    
    def getPayed(self):
        return self.payed

    def setAbholung(self, abholung):
        if abholung is None:
            abholung = ''
        self.abholung = str(abholung).strip()
        self.changed = True
        
    def getAbholung(self):
        return self.abholung

    def setTelefon(self, telefon):
        if telefon is None:
            telefon = ''
        self.telefon = str(telefon).strip()
        self.changed = True
        
    def getTelefon(self):
        return self.telefon

    def setPaletten(self, pal):
        if int(pal) > 0:
            self.paletten = int(pal)
        self.changed = True
        
    def getPaletten(self):
        return self.paletten
    
    def setZeitpunkt(self, zeitpunkt):
        self.__zeitpunkt = zeitpunkt
        self.changed = True
        
    def getZeitpunkt(self):
        return self.__zeitpunkt
    
    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        if status != self.status:
            self.changed = True
            self.status = status

    def setLiterzahl(self, liter):
        self.__literzahl = liter
        
    def setSumme(self, summe):
        self.__summe = summe
   
    
    def __str__(self):
        ret = u''
        if self.__kunde['name']:
            ret += u'Kunde: %s\n' % self.__kunde['name']
        ret += u' ' * 54 + u'Rechnungsbetrag: %8.2f €\n' % self.getSumme()
        ret += u' ' * 54 + u'      Literzahl: %8i l\n' % self.getLiterzahl()
        if self.getManuelleLiterzahl():
            ret += u' ' * 51 + u'Manuelle Literzahl: %8i l\n' % self.getManuelleLiterzahl()
        return ret



    