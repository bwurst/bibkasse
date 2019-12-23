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

from PyQt5 import QtCore, QtWidgets, uic
import sys, re, math
import cups

from gui.rechnungdialog import showRechnungDialog
from gui.valueinput import showValueInputDialog

from lib.Speicher import Speicher
from lib.BelegHTML import BelegHTML
from lib.BelegThermo import BelegThermo
from lib.BelegRechnung import BelegRechnung, rechnungsPDFDatei
from lib.BioBeleg import BioBeleg
from lib.BelegEintrag import BelegEintrag


PRINTER_OPTIONS = {'media': 'A4',
                   'copies': '2',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}

def _formatPrice(price, symbol=u'€'):
    '''_formatPrice(price, symbol='€'):
    Gets a floating point value and returns a formatted price, suffixed by 'symbol'. '''
    s = (u"%.2f" % price).replace('.', ',')
    pat = re.compile(r'([0-9])([0-9]{3}[.,])')
    while pat.search(s):
        s = pat.sub(r'\1.\2', s)
    return s+u' '+symbol



class WidgetKasse(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.speicher = Speicher()
        self.mainwindow = mainwindow
        self.betrag = 0.0
        self.gegeben = 0.0
        self.numbers = []
 
        try:
            self.ui = uic.loadUi('ressource/ui/widget_kasse.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        self.connectSlots()

    def update(self):
        '''wird vom Hauptprogramm aufgerufen wenn dieses Widget aktiviert wird'''
        self.mainwindow.oeffneKasse()
        self.gedruckt = False

    def reset(self):
        self.numbers = []
        self.gegeben = 0.0
        self.betrag = 0.0

    def numberPressed(self, number):
        def function():
            if number == '.' and '.' in self.numbers:
                return
            if '.' in self.numbers:
                komma = self.numbers.index('.')
                if len(self.numbers) == komma+3:
                    # Nur zwei Stellen hinter dem Komma zulassen
                    return
            self.numbers.append(str(number))
            self.updateBetraege()
        
        return function
    
    def delete(self):
        self.numbers = []
        self.updateBetraege()
    
    def beleg_hat_abfuellung(self):
        for entry in self.beleg.getEntries():
            if entry.preislistenID in ['5er', '10er',]:
                return True
        return False
    
    def ec(self):
        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.warning(self, u'Betrag per EC bezahlt?', u'Wurde die Zahlung vom EC-Gerät bestätigt?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.Yes):
            self.fertig(zahlart='ec')
           
    def bar(self):
        self.fertig(zahlart='bar')   
           
    def fertig(self, zahlart='bar'):
        betrag = self.betrag
        if zahlart == 'bar' and self.gegeben and self.gegeben < betrag:
            choice = QtWidgets.QMessageBox.warning(self, u'Anzahlung geleistet?', u'Hat der Kunde nur eine Anzahlung über %s geleistet?' % _formatPrice(self.gegeben), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel)
            if choice == QtWidgets.QMessageBox.Yes:
                self.speicher.speichereZahlung(self.beleg, 'bar', self.gegeben, 'Anzahlung')
                self.speicher.speichereBeleg(self.beleg)
                self.drucken()
                self.mainwindow.addRecentInvoice(self.beleg)
                self.gegeben = 0.0
                self.mainwindow.reset()
                return
            elif choice == QtWidgets.QMessageBox.No:
                choice = QtWidgets.QMessageBox.warning(self, u'Beleg damit bezahlt?', u'Ist der Beleg mit einer Zahlung über %s bezahlt?' % _formatPrice(self.gegeben), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.No:
                    return
                if zahlart == 'ec':
                    self.speicher.speichereZahlung(self.beleg, 'ec', self.gegeben)
                    self.beleg.setPayedEC(True)
                else:
                    self.speicher.speichereZahlung(self.beleg, 'bar', self.gegeben)
                    self.beleg.setPayed(True)
                self.speicher.speichereBeleg(self.beleg)
                self.drucken()
                self.mainwindow.addRecentInvoice(self.beleg)
                self.gegeben = 0.0
                self.mainwindow.reset()
                return
            else:
                return
              
        self.mainwindow.addRecentInvoice(self.beleg)
        if zahlart == 'ec':
            self.speicher.speichereZahlung(self.beleg, 'ec', self.beleg.getZahlbetrag())
            self.beleg.setPayedEC(True)
        elif zahlart == 'ueberweisung':
            self.beleg.setBanktransfer(True)
        else:
            self.speicher.speichereZahlung(self.beleg, 'bar', self.beleg.getZahlbetrag())
            self.beleg.setPayed(True)
        self.speicher.speichereBeleg(self.beleg)
        self.beleg = self.speicher.ladeBeleg(self.beleg.ID)
        print(self.beleg)
        self.drucken()
        self.mainwindow.addRecentInvoice(self.beleg)
        self.gegeben = 0.0
        self.mainwindow.reset()

    def belegKassieren(self, beleg):
        self.reset()
        self.beleg = beleg
        # if self.beleg_hat_abfuellung():
        #     self.drucken()
        self.betrag = beleg.getZahlbetrag()
        text = BelegHTML(self.beleg, public=False)
        self.ui.textBrowser.setHtml(text)
        self.alte_kundenbelege = self.speicher.listBelegeByKunde(self.beleg.kunde.ID())
        if self.alte_kundenbelege:
            self.liter_alte_abfuellungen = 0
            self.ui.listWidget_kundenhinweise.clear()
            for b in self.alte_kundenbelege:
                if b.ID == self.beleg.ID:
                    continue
                self.liter_alte_abfuellungen += b.getLiterzahl()
                hinweis = u'Abfüllung am %s: %s Liter' % (b.getZeitpunkt(), b.getLiterzahl())
                self.ui.listWidget_kundenhinweise.addItem(hinweis)
            self.ui.listWidget_kundenhinweise.addItem(u'Vorherige Abfüllungen dieses Jahr insgesamt: %s Liter' % (self.liter_alte_abfuellungen,))
        self.mainwindow.kundendisplay.showBeleg(self.beleg)
        self.updateBetraege()
        
    def drucken(self):
        self.gedruckt = True
        self.beleg = self.speicher.ladeBeleg(self.beleg.ID)
        BelegThermo(self.beleg, self.mainwindow.printer)

    def ueberweisung(self):
        if self.gegeben:
            if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.warning(self, u'Anzahlung geleistet?', 'Hat der Kunde eine Anzahlung über %s geleistet?' % _formatPrice(self.gegeben), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.Yes):
                self.speicher.speichereZahlung(self.beleg, 'bar', self.gegeben, 'Anzahlung')
        self.beleg = self.speicher.ladeBeleg(self.beleg.ID)
        BelegThermo(self.beleg, self.mainwindow.printer, kontodaten=True)
        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.warning(self, u'Betrag wird ueberwiesen?', 'Der Betrag wird auf unser Konto ueberwiesen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.Yes):
            self.gedruckt = True
            self.fertig(zahlart='ueberweisung')
        

    def rechnung(self):
        beleg = self.beleg
        originale = [beleg,]
        if showRechnungDialog(beleg, originale):
            self.mainwindow.addRecentInvoice(self.beleg)
            self.reset()
            self.mainwindow.reset()

    def gutschein(self):
        betrag = None
        if self.gegeben:
            betrag = self.gegeben
        else:
            betrag = showValueInputDialog(beschreibung="Gutscheinwert")
        self.speicher.speichereZahlung(self.beleg, 'gutschein', betrag, 'Gutschein-Einlösung')
        self.belegKassieren(self.speicher.ladeBeleg(self.beleg.ID))

    def updateBetraege(self):
        normalpreis = self.beleg.getZahlbetrag()
        self.ui.label_rechnungsbetrag.setText(u'%s' % _formatPrice(normalpreis))
        abgerundet = float(math.floor(normalpreis))       
        self.ui.label_rechnungsbetrag_abgerundet.setText(u'%s' % _formatPrice(abgerundet).replace(',00', ',-'))
        tmpstring = ''.join(self.numbers)
        if tmpstring:
            self.gegeben = float(tmpstring)
        else:
            self.gegeben = 0.0
        self.ui.label_gegeben.setText(_formatPrice(self.gegeben))
        rest = normalpreis - self.gegeben
        if rest < 0:
            self.ui.label_rest_text.setText(u'Rückgeld:')
            self.ui.label_rest.setText(_formatPrice(rest))
        else:
            self.ui.label_rest_text.setText(u'Restbetrag:')
            self.ui.label_rest.setText(_formatPrice(rest))
        rest_abgerundet = abgerundet - self.gegeben
        self.ui.label_rest_abgerundet.setText(u'%s' % _formatPrice(rest_abgerundet).replace(',00', ',-'))
    
    def abbrechen(self):
        self.reset()
        self.mainwindow.kundendisplay.showSlideshow()
        self.mainwindow.belegOeffnen(self.beleg)

    
    def connectSlots(self):
        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_comma.clicked.connect(self.numberPressed('.'))
        self.ui.button_delete.clicked.connect(self.delete)
        self.ui.button_drucken.clicked.connect(self.drucken)
        self.ui.button_ueberweisung.clicked.connect(self.ueberweisung)
        self.ui.button_rechnung.clicked.connect(self.rechnung)
        self.ui.button_gutschein.clicked.connect(self.gutschein)
        self.ui.button_zurueck.clicked.connect(self.abbrechen)
        self.ui.button_ec_zahlung.clicked.connect(self.ec)
        self.ui.button_barzahlung.clicked.connect(self.bar)
    

