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

from PyQt5 import QtWidgets, uic
import sys, re, math
import cups
import datetime

from gui.rechnungdialog import showRechnungDialog
from gui.valueinput import showValueInputDialog

from lib.Speicher import Speicher
from lib.BelegHTML import BelegHTML
from lib.BelegThermo import VorgangThermo, KassenbelegThermo
from lib.TSE import TSE, TSEException
from lib.Kassenbeleg import Kassenbeleg
from lib.BelegRechnung import BelegRechnung
from lib.Config import config
from lib.BioBeleg import BioBeleg
from lib.helpers import getMoneyValue
from gui.numberinput import showNumberInputDialog
from gui.textinput import showTextInputDialog
from lib.printer.esccapture import ESCCapture
import logging
from lib.printer.eschtml import ESCHTML


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
        self.zahlung_erfolgt = False
        self.rechnungdrucken = False
        self.rechnungsadresse = None
        self.betrag = 0.0
        self.gegeben = 0.0
        self.numbers = []
        try:
            self.tse = TSE()
        except TSEException:
            pass
        self.tse_trxnum = None
        self.tse_time_start = None
         
        try:
            self.ui = uic.loadUi('ressource/ui/widget_kasse.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        self.connectSlots()

    def shutdown(self):
        logging.info('shutting down widget_kasse')
        self.tse.stop()

    def update(self):
        '''wird vom Hauptprogramm aufgerufen wenn dieses Widget aktiviert wird'''
        self.gedruckt = False

    def reset(self):
        self.numbers = []
        self.gegeben = 0.0
        self.betrag = 0.0
        self.rechnungdrucken = False
        self.zahlung_erfolgt = False

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
    
    def ec(self):
        if self.gegeben == 0:
            self.gegeben = self.betrag
        if self.gegeben > self.betrag:
            trinkgeld = self.gegeben - self.betrag
            if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.warning(self, 'Zahlbetrag zu hoch', 'Zahlbetrag liegt über dem Rechnungsbetrag. Soll der Betrag von %s als Trinkgeld verbucht werden?' % getMoneyValue(trinkgeld), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.Yes):
                # FIXME: Wie verbuchen wir das?!
                self.gegeben = self.betrag
            else:
                # Was machen wir dann?
                pass
        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.warning(self, u'Per EC bezahlt?', u'Wurde die Zahlung über %s vom EC-Gerät bestätigt?' % getMoneyValue(self.gegeben), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.Yes):
            self.zahlung(betrag=self.gegeben, zahlart='ec')

    def bar(self):
        bemerkung = None
        if self.gegeben == 0 and self.betrag != 0:
            QtWidgets.QMessageBox.warning(self, 'Zahlungsbetrag eingeben!', 'Bitte zuerst den Zahlungsbetrag eingeben!', buttons=QtWidgets.QMessageBox.Ok)
            return
        if self.gegeben < self.betrag:
            choice = QtWidgets.QMessageBox.warning(self, u'Anzahlung geleistet?', u'Hat der Kunde nur eine Anzahlung über %s geleistet?' % _formatPrice(self.gegeben), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel)
            if choice == QtWidgets.QMessageBox.Cancel:
                return
            elif choice == QtWidgets.QMessageBox.Yes:
                bemerkung = 'Anzahlung'
            elif choice == QtWidgets.QMessageBox.No:
                rabatt = self.betrag - self.gegeben
                choice = QtWidgets.QMessageBox.warning(self, u'Beleg damit bezahlt?', u'Ist der Beleg mit einer Zahlung über %s bezahlt?\nDas entspricht einem Rabatt von %s' % (getMoneyValue(self.gegeben), getMoneyValue(rabatt)), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    self.vorgang.newItem(anzahl=1, beschreibung='Zahlungsrabatt', einzelpreis=-rabatt, steuersatz=19.0, datum=datetime.date.today())
                    self.vorgang.setPayed(True)
                    self.speicher.speichereVorgang(self.vorgang)
        self.zahlung(self.gegeben, 'bar', bemerkung)

    def gutschein(self):
        betrag = self.gegeben
        if not betrag:
            QtWidgets.QMessageBox.warning(self, 'Gutscheinbetrag eingeben!', 'Bitte zuerst den eingelösten Gutscheinbetrag eingeben!', buttons=QtWidgets.QMessageBox.Ok)
            return
        nummer = showTextInputDialog(titel="Gutschein-Nummer", vorschlaege=[], vorgabewert='')
        # Einzweck-Gutschein ist keine Zahlung im steuerlichen Sinne. Auf den Gutschein-Anteil darf keine 
        # USt berechnet werden, da diese schon bei Ausstellung des Gutscheins abgeführt wurde.
        # Daher wird der Gutschein als Rabatt auf der Rechnung vermerkt. 
        self.vorgang.newItem(anzahl=1, beschreibung='Gutschein-Einlösung (Nr. %s)' % nummer, einzelpreis=-betrag, steuersatz=19.0)
        self.speicher.speichereVorgang(self.vorgang)
        self.delete()
        text = BelegHTML(self.vorgang, public=False)
        self.ui.textBrowser.setHtml(text)
        self.mainwindow.kundendisplay.showVorgang(self.vorgang)
        #self.zahlung(betrag, 'gutschein', 'Gutschein-Einlösung Nr. %s' % nummer)
    
    def zahlung(self, betrag, zahlart, bemerkung=None):
        self.zahlung_erfolgt = True
        if zahlart == 'bar' and self.gegeben > self.betrag:
            self.speicher.speichereZahlung(self.vorgang, zahlart=zahlart, betrag=self.betrag, gegeben=self.gegeben, zurueck=self.betrag-self.gegeben, bemerkung=bemerkung)
        else:
            self.speicher.speichereZahlung(self.vorgang, zahlart=zahlart, betrag=betrag, bemerkung=bemerkung)
        self.vorgang = self.speicher.ladeVorgang(self.vorgang.ID)
        self.betrag = self.vorgang.getZahlbetrag()
        self.numbers = []
        if self.vorgang.getZahlbetrag() <= 0.0:
            # Kassiervorgang bendet!
            self.vorgang.setPayed(True)
            self.speicher.speichereVorgang(self.vorgang)
            self.fertig()
        else:
            # Nur verbuchen und im Kassiermodus bleiben.
            self.updateBetraege()
            text = BelegHTML(self.vorgang, public=False)
            self.ui.textBrowser.setHtml(text)
            self.mainwindow.kundendisplay.showVorgang(self.vorgang)
            


    def belegErzeugen(self):
        adresse = None
        if self.rechnungsadresse:
            adresse = self.rechnungsadresse
        print(adresse)
        kb = Kassenbeleg(self.vorgang, typ='rechnung', zahlart='ueberweisung', rechnungsadresse=adresse, tse_trxnum=self.tse_trxnum, tse_time_start=self.tse_time_start)
        self.tse_trxnum = None
        self.tse_time_start = None
        filename = BelegRechnung(kb)
        with open(filename.replace('.pdf', '.esc'), mode='wb') as escfile:
            capture = ESCCapture(escfile)
            KassenbelegThermo(kb, capture)
        with open(filename.replace('.pdf', '.html'), mode='w', encoding='utf-8') as escfile:
            capture = ESCHTML(escfile)
            KassenbelegThermo(kb, capture)
        return (filename, kb)

    def fertig(self):
        (filename, kb) = self.belegErzeugen()
        printed = False

        if not self.vorgang.getPayed() or self.vorgang.isBio() or self.rechnungdrucken:
            c = cups.Connection()
            c.printFile(c.getDefault(), filename, 'Rechnung %s' % kb['renr'], config('printer_plain'))
            printed = True

        if self.vorgang.isBio():
            # BIO-Beleg
            originale = [self.vorgang.ID,]
            if self.vorgang.originale:
                originale = self.vorgang.originale
                
            for idx in range(len(originale)):
                handle = originale[idx]
                vorgang = self.speicher.ladeVorgang(handle)
                filename = BioBeleg(vorgang, filename='BIO_%s_%02i.pdf' % (kb['renr'], idx))
                c = cups.Connection()
                c.printFile(c.getDefault(), filename, 'Bio-Beleg %s' % kb['renr'], config('printer_plain'))
                
                if vorgang.getBioLieferschein():
                    l = self.speicher.ladeBioLieferschein(vorgang.getBioLieferschein())
                    if not l['abholdatum']:
                        l['abholdatum'] = datetime.date.today()
                        self.speicher.speichereBioLieferschein(l)

        self.mainwindow.addRecentInvoice(self.vorgang)
        self.gegeben = 0.0
        if not printed:
            self.mainwindow.belegAnzeigen(filename)
            self.mainwindow.WIDGETS['abfuellung'].neuerVorgang()
        else:
            self.mainwindow.reset()

    def bondrucken(self, filename):
        if not self.mainwindow.printer:
            # Kein Bondrucker
            QtWidgets.QMessageBox.warning(self, 'Kein Bondrucker', 'Der Bondrucker wurde nicht erkannt!', buttons=QtWidgets.QMessageBox.Ok)
            return
        if filename.endswith('.pdf'):
            filename = filename.replace('.pdf', '.esc')
        with open(filename, 'rb') as escfile:
            self.mainwindow.printer.raw(escfile.read())


    def vorgangKassieren(self, vorgang):
        self.vorgang = vorgang
        if self.tse_trxnum:
            # Wir sind noch am Kasieren!
            pass
        else:
            self.reset()
            self.tse_trxnum = None
            self.tse_time_start = None
            try:
                response = self.tse.transaction_start('', '')
                self.tse_trxnum = response.transactionNumber
                self.tse_time_start = response.logTime
            except TSEException:
                pass
        
        # if self.beleg_hat_abfuellung():
        #     self.drucken()
        self.betrag = vorgang.getZahlbetrag()
        text = BelegHTML(self.vorgang, public=False)
        self.ui.textBrowser.setHtml(text)
        self.alte_kundenvorgaenge = self.speicher.listVorgaengeByKunde(self.vorgang.kunde.ID())
        if self.alte_kundenvorgaenge:
            self.liter_alte_abfuellungen = 0
            self.ui.listWidget_kundenhinweise.clear()
            for b in self.alte_kundenvorgaenge:
                if b.ID == self.vorgang.ID:
                    continue
                self.liter_alte_abfuellungen += b.getLiterzahl()
                hinweis = u'Abfüllung am %s: %s Liter' % (b.getZeitpunkt(), b.getLiterzahl())
                self.ui.listWidget_kundenhinweise.addItem(hinweis)
            self.ui.listWidget_kundenhinweise.addItem(u'Vorherige Abfüllungen dieses Jahr insgesamt: %s Liter' % (self.liter_alte_abfuellungen,))
        self.mainwindow.kundendisplay.showVorgang(self.vorgang)
        self.updateBetraege()
        
    def rechnung(self):
        if not self.vorgang.getPayed():
            self.vorgang.setBanktransfer(True)
        self.fertig()

    def rechnungsdaten(self):
        if showRechnungDialog(self.vorgang):
            self.rechnungsadresse = self.vorgang.rechnungsDaten['adresse']
            self.rechnungdrucken = True

    def updateBetraege(self):
        normalpreis = self.vorgang.getZahlbetrag()
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

    def beenden(self):
        if self.zahlung_erfolgt and self.tse_trxnum:
            # Es sind Zahlungen erfolgt aber noch nicht auf der TSE abgesichert. Es ist noch ein Restbetrag offen.
            (filename, kb) = self.belegErzeugen()
            # FIXME: Belegausgabe?
        else:
            if self.tse_trxnum:
                # TSE-Transaktion mit Abbruch beenden!
                Kassenbeleg(self.vorgang, 'abbruch', zahlart=None, tse_trxnum=self.tse_trxnum, tse_time_start=self.tse_time_start, abbruch=True)
            self.tse_trxnum = None
            self.tse_time_start = None
        self.reset()
        self.mainwindow.kundendisplay.showSlideshow()
        self.mainwindow.reset()
    
    def zurueck(self):
        self.mainwindow.kundendisplay.showSlideshow()
        self.mainwindow.vorgangOeffnen(self.vorgang, kassiervorgang=True)

    
    def connectSlots(self):
        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_comma.clicked.connect(self.numberPressed('.'))
        self.ui.button_delete.clicked.connect(self.delete)
        self.ui.button_abbrechen.clicked.connect(self.beenden)
        self.ui.button_rechnung.clicked.connect(self.rechnung)
        self.ui.button_rechnungsdaten.clicked.connect(self.rechnungsdaten)
        self.ui.button_gutschein.clicked.connect(self.gutschein)
        self.ui.button_zurueck.clicked.connect(self.zurueck)
        self.ui.button_ec_zahlung.clicked.connect(self.ec)
        self.ui.button_barzahlung.clicked.connect(self.bar)
    

