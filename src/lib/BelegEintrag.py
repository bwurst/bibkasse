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


class BelegEintrag(object):
    
    def __init__(self, invoice, anzahl, preislistenID = None, beschreibung = None, einzelpreis = None, 
                 liter_pro_einheit = None, einheit = None, preisliste_link = True, steuersatz = None, datum = None, 
                 autoupdate = False):
        self.__preisliste = invoice.getPreisliste()
        self.__invoice = invoice
        self.preislistenID = preislistenID
        self.preisliste_link = bool(preislistenID and preisliste_link and autoupdate)
        self.autoupdate = autoupdate
        self.__manuelle_rabattstufe = None

        self.__data = {'anzahl': float(anzahl),
                       'einheit': einheit,
                       'beschreibung': beschreibung,
                       'einzelpreis': einzelpreis,
                       'steuersatz': steuersatz,
                       'datum': None,
                       'liter_pro_einheit': liter_pro_einheit,
                       }
        # Die Setter-Methode macht die Typ-Konvertierung!
        self._setzeWert('datum', datum)

        if self.preisliste_link:
            invoiceChanged = self.__invoice.changed
            try:
                self.__preisliste.registerObject(self.preislistenID, self)
            except IndexError:
                self.preisliste_link = False
                self.preislistenID = None
            # Setze nochmals alle Werte, damit die interne Repräsentation in der Regel None ist
            self._setzeWert('anzahl', float(anzahl))
            self._setzeWert('einheit', einheit)
            self._setzeWert('beschreibung', beschreibung)
            self._setzeWert('einzelpreis', einzelpreis)
            self._setzeWert('steuersatz', steuersatz)
            self._setzeWert('datum', datum)
            self._setzeWert('liter_pro_einheit', liter_pro_einheit)
            self._bereinigeDaten()
            # Stelle den Zustand wieder her
            self.__invoice.changed = invoiceChanged

            
    
    def unregister(self):
        if self.__preisliste:
            self.__preisliste.unregisterObject(self)
        try:
            self.__invoice.reallyDeleteItem(self.getID())
        except IndexError:
            pass
    

    def _setzeWert(self, schluessel, wert):
        #print ('__data[%s] = "%s"' % (schluessel, wert)) 
        if schluessel not in self.__data.keys():
            raise ValueError('Schlüssel nicht bekannt: %s' % schluessel)
        elif schluessel in ['anzahl', ]:
            self.__data[schluessel] = wert
        elif schluessel == 'datum':
            if wert is None:
                return
            elif type(wert) != datetime.date:
                wert = wert.strip()
                if len(wert) == 10:
                    wert = datetime.date(int(wert[0:4]), int(wert[5:7]), int(wert[8:10]))
                else:
                    raise ValueError('Das ist kein Datum: %s' % wert)
            self.__data['datum'] = wert
        elif schluessel == 'einzelpreis':
            self.__data['einzelpreis'] = wert
            if self.autoupdate and self.istStandardpreis():
                self.__data['einzelpreis'] = None
        else:
            preislistenWert = self.preislistenWert(schluessel)
            if (wert == preislistenWert or wert is None) and self.autoupdate:
                self.__data[schluessel] = None
            else:
                self.__data[schluessel] = wert
        self.__invoice.changed = True
        #print ('__data[%s] is "%s"' % (schluessel, self.__data[schluessel]))

    def _leseWert(self, schluessel):
        if schluessel not in self.__data.keys():
            raise ValueError('Schlüssel nicht bekannt: %s' % schluessel)
        if schluessel == 'anzahl':
            return int(self.__data['anzahl'])
        if schluessel == 'datum':
            return self.__data['datum']
        preislistenWert = self.preislistenWert(schluessel)
        if self.__data[schluessel] is None and preislistenWert is not None and self.autoupdate:
            return preislistenWert
        return self.__data[schluessel]

    def preislistenWert(self, schluessel):
        if not self.preislistenID:
            return None
        if schluessel == 'einheit':
            return self.__preisliste.getEinheit(self.preislistenID)
        elif schluessel == 'beschreibung':
            return self.__preisliste.getBeschreibung(self.preislistenID)
        elif schluessel == 'einzelpreis':
            if self.__manuelle_rabattstufe:
                return self.__preisliste.getPreis(self.preislistenID, self.__manuelle_rabattstufe[1])
            else:
                return self.__preisliste.getPreis(self.preislistenID)
        elif schluessel == 'steuersatz':
            return self.__preisliste.getSteuersatz(self.preislistenID)
        elif schluessel == 'liter_pro_einheit':
            return self.__preisliste.getLiterProEinheit(self.preislistenID)
        else:
            raise IndexError('Unbekannter Schlüssel: %s' % schluessel)
        
    
    def istStandardpreis(self):
        normalpreis = self.preislistenWert('einzelpreis')
        return self.getPreis() == normalpreis
    
    def copy(self):
        new = self.__class__(self.__invoice, 
                              self.getStueckzahl(),
                              self.preislistenID,
                              liter_pro_einheit = self._leseWert('liter_pro_einheit'), 
                              preisliste_link = False,
                              datum = self.getDatum(),
                              steuersatz = self.getSteuersatz())
        new.setRabattstufe(self.getRabattstufe()) 
        new.setBeschreibung(self.getBeschreibung())
        new.setPreis(self.getPreis())
        new.setEinheit(self.getEinheit())
        new.setDatum(self.getDatum())
        return new

    
    def importValues(self, invoiceEntry):
        self._setzeWert('anzahl', invoiceEntry.getStueckzahl())
        self.setPreislistenID(invoiceEntry.preislistenID, invoiceEntry.preisliste_link)
        self.setRabattstufe(invoiceEntry.getRabattstufe())
        self._setzeWert('einheit', invoiceEntry.getEinheit())
        self._setzeWert('beschreibung', invoiceEntry.getBeschreibung())
        self._setzeWert('einzelpreis', invoiceEntry.getPreis())
        self._setzeWert('steuersatz', invoiceEntry.getSteuersatz())
        self._setzeWert('datum', invoiceEntry.getDatum())
        self._bereinigeDaten()
        self._setzeWert('liter_pro_einheit', invoiceEntry.getLiterProEinheit())
    
    def getID(self):
        return str(id(self))
        

    def __getitem__(self, key):
        if key == 'anzahl':
            return self.getStueckzahl()
        elif key == 'einheit':
            return self.getEinheit()
        elif key == 'liter':
            return self.getLiterzahl()
        elif key == 'beschreibung':
            return self.getBeschreibung()
        elif key == 'einzelpreis':
            return self.getPreis()
        elif key == 'gesamtpreis':
            return self.getSumme()
        else:
            raise IndexError("Don't know what %s should be" % key)
        
    def setPreislistenID(self, ID, preisliste_link):
        # Kopiere die Daten die ggf. von der Preisliste übernommen wurden
        for schluessel in ['einheit', 'beschreibung', 'einzelpreis', 'liter_pro_einheit']:
            self.__data[schluessel] = self._leseWert(schluessel)
        self.preislistenID = ID
        self.preisliste_link = (preisliste_link and self.autoupdate)

        if ID == None or not self.preisliste_link:
            self.__preisliste.unregisterObject(self)
        else:
            self.__preisliste.unregisterObject(self)
            self.__preisliste.registerObject(self.preislistenID, self)
        # So werden ggf. die Werte wieder auf None gesetzt wenn identisch zu den Preislisten-Daten
        self._bereinigeDaten()
        self.__invoice.changed = True
        
    def _bereinigeDaten(self):
        self._setzeWert('einheit', self.getEinheit())
        self._setzeWert('beschreibung', self.getBeschreibung())
        self._setzeWert('steuersatz', self.getSteuersatz())
        self._setzeWert('datum', self.getDatum())
        self._setzeWert('liter_pro_einheit', self.getLiterProEinheit())
        self._setzeWert('einzelpreis', self.getPreis())
        
    def getAutomatischeRabattstufe(self):
        return self.__preisliste.getRabattStufe(self.preislistenID)
        
    def setRabattstufe(self, stufe):
        if stufe == None:
            self.__manuelle_rabattstufe = None
            return
        if self.preislistenID:
            if self.getAutomatischeRabattstufe() == stufe and self.autoupdate:
                self.__manuelle_rabattstufe = None
            else:
                self.__manuelle_rabattstufe = stufe
        else:
            self.__manuelle_rabattstufe = stufe
        self.setPreis(self.preislistenWert('einzelpreis'))


    def getRabattstufe(self):
        if self.__manuelle_rabattstufe is not None:
            return self.__manuelle_rabattstufe
        else:
            return self.getAutomatischeRabattstufe()
        
    def listRabattStufen(self):
        rabatte = self.__preisliste.rabattStufen(self.preislistenID)
        return rabatte
        
    def getSteuersatz(self):
        ret = self._leseWert('steuersatz')
        if not ret:
            ret = 0.0
        return ret
    
    def setSteuersatz(self, wert):
        return self._setzeWert('steuersatz', float(wert))
    
    def getEinheit(self):
        return self._leseWert('einheit')
    
    def setEinheit(self, einheit):
        self._setzeWert('einheit', str(einheit))
        
    def getBeschreibung(self):
        return self._leseWert('beschreibung')
    
    def setBeschreibung(self, beschreibung):
        self._setzeWert('beschreibung', str(beschreibung))
        
    def getLiterzahl(self):
        try:
            return int(self.getStueckzahl()) * int(self._leseWert('liter_pro_einheit'))
        except:
            return 0
        
    def getLiterProEinheit(self):
        if self.__preisliste.getLiterProEinheit(self.preislistenID) > 0:
            return self._leseWert('liter_pro_einheit')
        else:
            return 0

    def getStueckzahl(self):
        return self._leseWert('anzahl')

    def setStueckzahl(self, anzahl):
        self._setzeWert('anzahl', float(anzahl))

    def getSumme(self):
        return self.getStueckzahl() * float(self.getPreis())

    def getNormalsumme(self):
        return self.getStueckzahl() * float(self.getNormalpreis())

    def setPreis(self, einzelpreis):
        try:
            self._setzeWert('einzelpreis', float(einzelpreis))
        except:
            print ('Fehler:', einzelpreis)
            
    def getNormalpreis(self):
        return float(self._leseWert('einzelpreis'))

    def getPreis(self):
        try:
            preis = float(self._leseWert('einzelpreis'))
            return preis
        except TypeError:
            # vermutlich None
            return 0.0
 
    def getNettosumme(self):
        return self.getSumme() / (float(self.getSteuersatz()/100) + 1)
 
    def getSteuersumme(self):
        return self.getSumme() - (self.getSumme() / (float(self.getSteuersatz()/100) + 1))

    def getInvoice(self):
        return self.__invoice
  
    def getDatum(self):
        wert = self._leseWert('datum')
        if type(wert) not in [type(None), datetime.date]:
            print (self)
            print ('»%s«' % wert)
        if not wert:
            belegzeit = self.__invoice.getZeitpunkt()
            if belegzeit:
                wert = belegzeit.date()
        return wert
    
    def setDatum(self, datum):
        self._setzeWert('datum', datum)

    def __str__(self):
        s = 'BelegEintrag #%s\n' % self.getID()
        s += '%s (=> %i Liter)\n' % (self.getBeschreibung(), self.getLiterzahl())
        s += '%.2f %s * %.2f = %.2f\n' % (self.getStueckzahl(), self.getEinheit(), self.getPreis(), self.getSumme())
        s += 'Auto-Update: %s\n' % self.autoupdate
        s += str(self.__data)
        return s
        
        
        
        
        
        
        
            
if __name__ == '__main__':
    from Beleg import Beleg 
    invoice = Beleg()
    my5er = invoice.newItem(20, '5er')
    invoice.newItem(20, '10er')
    invoice.newItem(10, '5er_gebraucht')
    invoice.newItem(10, 'holzstaender')

    print ('Liter insgesamt: %4i' % invoice.getLiterzahl())
    gesamtpreis = 0.0
    for i in invoice.getEntries():
        print ('%3i x %-50s je %6.2f €    = %7.2f €' % (i['anzahl'], i['beschreibung'], i['einzelpreis'], i['gesamtpreis']))
        gesamtpreis += i.getSumme()
    print ('=' * 81)
    print (' ' * 53, 'Rechnungsbetrag: %8.2f € (%8.2f)' % (gesamtpreis, invoice.getSumme()))

    print ('Liter insgesamt: %4i' % invoice.getLiterzahl())
    gesamtpreis = 0.0
    for i in invoice.getEntries():
        print ('%3i x %-50s je %6.2f €    = %7.2f €' % (i['anzahl'], i['beschreibung'], i['einzelpreis'], i['gesamtpreis']))
        gesamtpreis += i.getSumme()
    print ('=' * 81)
    print (' ' * 53, 'Rechnungsbetrag: %8.2f € (%8.2f)' % (gesamtpreis, invoice.getSumme()))



