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

from lib.VorgangEintrag import VorgangEintrag
from lib.Preisliste import Preisliste
from lib.Kunde import Kunde

class Vorgang(object):
    def __init__(self, kunde=None):
        self.__preisliste = Preisliste()
        self.ID = None
        self.__manuelleLiterzahl = None
        self.__entryOrder = []
        self.__entries = {}
        if not kunde:
            kunde = Kunde()
        self.kunde = kunde
        self.abholung = ''
        self.telefon = ''
        self.__zeitpunkt = None
        self.paletten = 1
        self.changed = False
        self.rechnungsDaten = {'nummer': None, 'datum': None, "adresse": None}
        self.banktransfer = False
        self.payed = False
        self.zahlart = None
        self.xmlstring = None
        self.version = 0
        self.status = None
        self.zahlungen = []
        self.bio = False
        self.bio_lieferschein = None
        self.bio_kontrollstelle = None
        self.bio_lieferant = None
        self.originale = []
        self.__minprice_deleted = False

    def setXMLString(self, xmlstring):
        self.xmlstring = xmlstring
    
    def setVersion(self, version):
        self.version = version
    
    def getVersion(self):
        return self.version
    
    def setID(self, ID):
        self.ID = ID
        
    def getEAN13(self):
        if not self.ID:
            return None
        if len(self.ID) == 9:
            return '200' + self.ID
        if len(self.ID) > 9:
            md = hashlib.md5()
            md.update(self.ID)
            return '200' + '%09i' % (int(md.hexdigest()[:8], 16) % 1000000000)
        else:
            return None
        
    def getPreisliste(self):
        return self.__preisliste
        
    def newItem(self, anzahl, preislistenID = None, beschreibung = None, einzelpreis = None, 
                liter_pro_einheit = None, einheit = '', preisliste_link = True, 
                steuersatz = None, datum = None, autoupdate = True):
        ie = VorgangEintrag(self, 
                          anzahl = anzahl,
                          preislistenID = preislistenID, 
                          beschreibung = beschreibung, 
                          einzelpreis = einzelpreis, 
                          liter_pro_einheit = liter_pro_einheit, 
                          einheit = einheit, 
                          preisliste_link = preisliste_link,
                          steuersatz = steuersatz,
                          datum = datum,
                          autoupdate = autoupdate)
        return self.addItem(ie) 

    def addItem(self, invoiceItem):
        handle = invoiceItem.getID()
        self.__entryOrder.append(handle)
        self.__entries[handle] = invoiceItem
        if self.__manuelleLiterzahl:
            if invoiceItem.getRabattstufe() and invoiceItem.getRabattstufe()[0] == 'liter':
                    invoiceItem.setRabattstufe(('liter', self.__manuelleLiterzahl))
            self.updateManuelleLiterzahl()
        self.berechneMindestpreis()
        self.changed = True
        return handle

    def berechneMindestpreis(self):
        if self.__minprice_deleted:
            return
        try:
            betrag = self.__preisliste.getPreis('minprice')
        except IndexError:
            # Kein Mindestpreis festgelegt
            return
        minprice_handle = None
        duplicates = []
        for key, e in self.__entries.items():
            if e.preislistenID == 'minprice':
                if minprice_handle:
                    duplicates.append(key)
                else:
                    minprice_handle = key
        for handle in duplicates:
            self.deleteItem(handle)
            # Das ist jetzt automatisch passiert, sonst hätte diese Funktion nichts gemacht
            self.__minprice_deleted = False
        if minprice_handle and betrag > 0:
            self.__entries[minprice_handle].setStueckzahl(1)
        elif minprice_handle and betrag <= 0:
            self.deleteItem(minprice_handle)
            # Das ist jetzt automatisch passiert, sonst hätte diese Funktion nichts gemacht
            self.__minprice_deleted = False
        elif betrag > 0 and not minprice_handle:
            self.newItem(1, 'minprice')

    def isRechnung(self):
        return (self.rechnungsDaten['nummer'] != None)
    
    def getRechnungsdatum(self):
        if not self.isRechnung():
            return None
        return self.rechnungsDaten['datum']
    
    def getRechnungsnummer(self):
        if not self.isRechnung():
            return None
        return self.rechnungsDaten['nummer']
    
    def setRechnungsdaten(self, datum, nummer = None):
        if not datum or not nummer or type(datum) != datetime.date:
            self.rechnungsDaten['nummer'] = None
            self.rechnungsDaten['datum'] = None
        else:
            self.rechnungsDaten['datum'] = datum
            self.rechnungsDaten['nummer'] = str(nummer)
        self.changed = True

    def setRechnungsadresse(self, adresse):
        self.rechnungsDaten['adresse'] = adresse

    def deleteItem(self, handle):
        if not handle in self.__entries.keys():
            raise IndexError("This VorgangEintrag is not known!")
        if self.__entries[handle].preislistenID == 'minprice':
            self.__minprice_deleted = True
        self.__entries[handle].unregister()
        self.berechneMindestpreis()
        self.changed = True
        
    def reallyDeleteItem(self, handle):
        if not handle in self.__entries.keys():
            raise IndexError("This VorgangEintrag is not known!")
        if self.__entries[handle].preislistenID == 'minprice':
            self.__minprice_deleted = True
        self.__entryOrder.remove(handle)
        del self.__entries[handle]
        self.berechneMindestpreis()
        self.changed = True

    def aendereAnzahl(self, handle, anzahl):
        self.__entries[handle].setStueckzahl(anzahl)
        self.berechneMindestpreis()
        self.changed = True


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
        self.updateManuelleLiterzahl()
        self.changed = True

    def updateManuelleLiterzahl(self):        
        for item in self.getEntries():
            if item.getRabattstufe() and item.getRabattstufe()[0] == 'liter':
                if self.__manuelleLiterzahl:
                    item.setRabattstufe(('liter', self.__manuelleLiterzahl))
                else:
                    item.setRabattstufe(None)

    def getManuelleLiterzahl(self):
        return self.__manuelleLiterzahl
    
    def getEntry(self, handle):
        return self.__entries[handle]

    def getLiterzahl(self):
        liter = 0
        for ie in self.__entries.values():
            liter += ie.getLiterzahl()
        return liter
    
    def getEinzelpreis(self, handle):
        return self.__entries[handle].getPreis()

    def getSumme(self):
        summe = 0.0
        for ie in self.__entries.values():
            summe += ie.getSumme()
        return summe

    def getNormalsumme(self):
        summe = 0.0
        for ie in self.__entries.values():
            summe += ie.getNormalsumme()
        return summe

    def getSteuersummen(self):
        summen = {}
        for ie in self.__entries.values():
            tmp = (ie.getSteuersatz(), ie.getSteuersumme())
            if tmp[0] in summen.keys():
                summen[tmp[0]] += tmp[1]
            else:
                summen[tmp[0]] = tmp[1]
        return summen
        

    def getEntries(self):
        if self.changed:
            self.berechneMindestpreis()
        return [self.__entries[handle] for handle in self.__entryOrder]

    def setKunde(self, kunde):
        if kunde != self.kunde:
            self.kunde = kunde
            self.changed = True
                
    def getKunde(self):
        return self.kunde
    
    def getKundenname(self):
        if not self.kunde:
            return ''
        return self.kunde.getName()
    
    def setBanktransfer(self, value):
        if value:
            self.banktransfer = True
            self.setPayed(False)
            self.zahlart = 'ueberweisung'
        else:
            self.banktransfer = False
        self.changed = True
    
    def getBanktransfer(self):
        return self.banktransfer

    def setPayed(self, value):
        if value:
            self.payed = True
            self.setBanktransfer(False)
            self.zahlart = 'bar'
        else:
            self.payed = False
        self.changed = True
    
    def getPayed(self):
        return self.payed

    def setPayedEC(self, value):
        if value:
            self.payed = True
            self.banktransfer = True
            self.zahlart = 'ec'
        else:
            self.payed = False
        self.changed = True

    def getZahlart(self):
        return self.zahlart

    def getPartlyPayed(self):
        pp = False
        if not self.getPayed() and not self.getBanktransfer():
            if len(self.zahlungen) > 0:
                summe = 0.0
                for z in self.zahlungen:
                    summe += z['betrag']
                if summe > 0 and summe <= self.getSumme():
                    pp = True
        return pp

    def getZahlbetrag(self):
        summe = 0.0
        for z in self.zahlungen:
            summe += z['betrag']
        return self.getSumme() - summe

    def getZahlungen(self):
        return self.zahlungen

    def setAbholung(self, abholung):
        if abholung is None:
            abholung = ''
        self.abholung = str(abholung).strip()
        self.changed = True
        
    def getAbholung(self):
        return self.abholung

    def setTelefon(self, telefon):
        print ('FIXME: vorgang.setTelefon() wurde aufgerufen!')
        import traceback
        traceback.print_stack()
        pass
        
    def getTelefon(self):
        return self.kunde.getErsteTelefon()

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
    
    def isBio(self):
        return self.bio

    def getBio(self):
        if self.bio:
            if self.bio_kontrollstelle:
                return self.bio_kontrollstelle
            else:
                return True
        return False
    
    def getBioLieferant(self):
        if self.bio and self.bio_lieferant:
            return self.bio_lieferant
        return None
    
    def getBioKontrollstelle(self):
        if self.bio and self.bio_kontrollstelle:
                return self.bio_kontrollstelle
        return None
    
    def getBioLieferschein(self):
        if self.bio and self.bio_lieferschein:
            return self.bio_lieferschein
        return None
    
    def setBio(self, bio, kontrollstelle = None, lieferant = None, lieferschein = None):
        oldbio = self.bio
        oldkontrollstelle = self.bio_kontrollstelle
        oldlieferant = self.bio_lieferant
        oldlieferschein = self.bio_lieferschein
        if bio:
            self.bio = True
        else:
            self.bio = False
        if bio and lieferschein:
            self.bio_lieferschein = lieferschein
        if bio and kontrollstelle:
            self.bio_kontrollstelle = str(kontrollstelle).strip()
        if bio and lieferant:
            self.bio_lieferant = str(lieferant).strip()
        if bio and not self.bio_kontrollstelle:
            self.bio_kontrollstelle = self.kunde.getOekoKontrollstelle()
            self.bio_lieferant = self.kunde.getAdresse()
        if oldbio != self.bio or oldkontrollstelle != self.bio_kontrollstelle or \
                oldlieferant != self.bio_lieferant or oldlieferschein != self.bio_lieferschein:
            self.changed = True
    
    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        if status != self.status:
            self.changed = True
            self.status = status
   
    def vorgangHinzufuegen(self, vorgang):
        if not self.kunde:
            self.kunde = vorgang.getKunde()
        if self.kunde.isBio() and vorgang.isBio():
            if not self.isBio():
                self.setBio(True, self.kunde.getOekoKontrollstelle())
        for neuerEintrag in vorgang.getEntries():
            found = False
            for alterEintrag in self.getEntries():
                if (alterEintrag.preislistenID == neuerEintrag.preislistenID and 
                    alterEintrag.getPreis() == neuerEintrag.getPreis() and 
                    alterEintrag.getDatum() == neuerEintrag.getDatum()):
                    found = True
                    alterEintrag.setStueckzahl(alterEintrag.getStueckzahl() + neuerEintrag.getStueckzahl())
            if not found:
                self.addItem(neuerEintrag.copy())
        self.originale.append(vorgang.ID)

    
    def __str__(self):
        ret = ''
        if self.kunde:
            ret += 'Kunde: %s\n' % self.kunde.getName()
        for item in self.getEntries():
            ret += '%3i %-5s  %-45s je %6.2f €  = %7.2f €\n' % (item['anzahl'], item['einheit'], item['beschreibung'], item['einzelpreis'], item['gesamtpreis'])
        ret += '=' * 81 + '\n'
        ret += ' ' * 54 + 'Rechnungsbetrag: %8.2f €\n' % self.getSumme()
        for satz, betrag in self.getSteuersummen().items():
            ret += ' ' * 59 + 'MwSt %4.1f%%: %8.2f €\n' % (satz, betrag)
        ret += ' ' * 54 + '      Literzahl: %8i l\n' % self.getLiterzahl()
        if self.getManuelleLiterzahl():
            ret += ' ' * 51 + 'Manuelle Literzahl: %8i l\n' % self.getManuelleLiterzahl()
        return ret




if __name__ == '__main__':
    i = Vorgang()
    _5er = i.newItem(10, '5er')
    _10er = i.newItem(20, '10er')
    gebraucht_5er = i.newItem(100, 'frischsaft')
    
    print (i) 

    i.aendereAnzahl(_10er, 30)
        
    print (i) 
    
    i.deleteItem(_10er)
    i.kunde.setName('Müller')
    
    print (i) 

    mosten = i.newItem(2, '5er_vk')
    print (i)
    i.aendereAnzahl(mosten, 6)
    print (i)

    i = Vorgang()
    i.newItem(12, 'frischsaft')
    i.newItem(18, '5er')
    print (i)
    