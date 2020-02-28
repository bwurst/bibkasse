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
import sys


from lib.helpers import getMoneyValue
from lib.Speicher import Speicher
from gui.textinput import showTextInputDialog
from gui.valueinput import showValueInputDialog
from lib.Vorgang import Vorgang
from lib.Kassenbeleg import Kassenbeleg
from lib.TSE import TSE, TSEException

class WidgetZaehlprotokoll(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_zaehlprotokoll.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        
        self.connectSlots()
        self.abschluss = {
            "ersterbeleg": None,
            "letzterbeleg": None,
            "summe_brutto": None,
            "summe_netto": None,
            "summe_mwst": None,
            "summe_bar": None,
            "summe_transit": None,
            "kassenstand": None,
            "bemerkung": None
            }
        self.kassenbestand = 0.0
        self.__kassenstand_berechnet = 0.0

    def isShown(self):
        pass
    
    def update(self):
        self.get_kassenstand()
        self.ui.count_500.setValue(0)
        self.ui.count_200.setValue(0)
        self.ui.count_100.setValue(0)
        self.ui.count_50.setValue(0)
        self.ui.count_20.setValue(0)
        self.ui.count_10.setValue(0)
        self.ui.count_5.setValue(0)
        self.ui.count_2.setValue(0)
        self.ui.count_1.setValue(0)
        self.ui.count_050.setValue(0)
        self.ui.count_020.setValue(0)
        self.ui.count_010.setValue(0)
        self.ui.count_005.setValue(0)
        self.ui.count_002.setValue(0)
        self.ui.count_001.setValue(0)
        self.calculate()

        
    def get_kassenstand(self):
        self.abschluss['summe_brutto'] = 0.0
        self.abschluss['summe_netto'] = 0.0
        self.abschluss['summe_mwst'] = 0.0
        self.abschluss['summe_bar'] = 0.0
        self.abschluss['summe_transit'] = 0.0
        self.abschluss['ersterbeleg'] = None
        s = Speicher()
        letzter_abschluss = s.getLetzterAbschluss()
        kassenstand = 0.0
        infotext = ''
        if letzter_abschluss:
            infotext += 'Letzter Abschluss vom %s:\nKassenstand: %s\n\n' % (letzter_abschluss['timestamp'].isoformat(), getMoneyValue(letzter_abschluss['kassenstand']))
            kassenstand = letzter_abschluss['kassenstand']
            self.abschluss['ersterbeleg'] = letzter_abschluss['letzterbeleg'] + 1
        else:
            infotext += 'Keinen vorherigen Abschluss gefunden!\n\n'
        belege = s.listKassenbelege(self.abschluss['ersterbeleg'])
        for b in belege:
            if not self.abschluss['ersterbeleg']:
                self.abschluss['ersterbeleg'] = b['id']
            kassenstand += b['kassenbewegung']
            if b['type'] == 'transit' and b['summen']['summe']['mwst'] == 0:
                self.abschluss['summe_transit'] += b['kassenbewegung']
            else:
                self.abschluss['summe_brutto'] += b['summen']['summe']['brutto']
                self.abschluss['summe_netto'] += b['summen']['summe']['netto']
                self.abschluss['summe_mwst'] += b['summen']['summe']['mwst']
                self.abschluss['summe_bar'] += b['kassenbewegung']
            self.abschluss['letzterbeleg'] = b['id']
        infotext += 'Umsatz brutto: %s\nUmsatz netto: %s\nMwSt: %s\n\nSumme der Barzahlungen: %s\n\nSumme der Transitbuchungen: %s\n' % (
            getMoneyValue(self.abschluss['summe_brutto']), getMoneyValue(self.abschluss['summe_netto']), 
            getMoneyValue(self.abschluss['summe_mwst']), getMoneyValue(self.abschluss['summe_bar']),
            getMoneyValue(self.abschluss['summe_transit']))
        self.__kassenstand_berechnet = kassenstand
        self.ui.infotext.setText(infotext)
        

    def connectSlots(self):
        self.ui.count_500.valueChanged.connect(self.calculate)
        self.ui.count_200.valueChanged.connect(self.calculate)
        self.ui.count_100.valueChanged.connect(self.calculate)
        self.ui.count_50.valueChanged.connect(self.calculate)
        self.ui.count_20.valueChanged.connect(self.calculate)
        self.ui.count_10.valueChanged.connect(self.calculate)
        self.ui.count_5.valueChanged.connect(self.calculate)
        self.ui.count_2.valueChanged.connect(self.calculate)
        self.ui.count_1.valueChanged.connect(self.calculate)
        self.ui.count_050.valueChanged.connect(self.calculate)
        self.ui.count_020.valueChanged.connect(self.calculate)
        self.ui.count_010.valueChanged.connect(self.calculate)
        self.ui.count_005.valueChanged.connect(self.calculate)
        self.ui.count_002.valueChanged.connect(self.calculate)
        self.ui.count_001.valueChanged.connect(self.calculate)
        self.ui.button_abschluss.clicked.connect(self.erstelle_abschluss)
        self.ui.button_entnahme.clicked.connect(self.entnahme)
        self.ui.button_einlage.clicked.connect(self.einlage)

    def entnahme(self):
        beschreibung = showTextInputDialog('Grund der Entnahme', ['Bargeldentnahme', 'Zahlung Mitarbeiter', 'Spesen', 'Trinkgeld'], '')
        if not beschreibung:
            return
        betrag = showValueInputDialog(beschreibung='Entnahme-Betrag')
        if not betrag:
            return
        self.transitbuchung(-betrag, beschreibung)

    def einlage(self):
        beschreibung = showTextInputDialog('Grund der Einlage', ['Bargeldeinlage', 'Privateinlage', 'Trinkgeld'], '')
        if not beschreibung:
            return
        betrag = showValueInputDialog(beschreibung='Einlage-Betrag')
        if not betrag:
            return
        self.transitbuchung(betrag, beschreibung)
        
        
    def transitbuchung(self, betrag, beschreibung):
        tse_trxnum = None
        tse_time_start = None
        try:
            tse = TSE()
            response = tse.transaction_start('', '')
            tse_trxnum = response.transactionNumber
            tse_time_start = response.logTime
        except TSEException:
            pass
        v = Vorgang()
        s = Speicher()
        v.newItem(1, beschreibung=beschreibung, einzelpreis=betrag, steuersatz=0.0)
        v.setPayed(True)
        v.setStatus('transit')
        s.speichereZahlung(v, 'transit', betrag)
        v = s.ladeVorgang(v.ID)
        kb = Kassenbeleg(v, 'transit', tse_trxnum=tse_trxnum, tse_time_start=tse_time_start)
        self.get_kassenstand()
        self.calculate()
        
    
    def erstelle_abschluss(self):
        differenz = self.kassenbestand - self.__kassenstand_berechnet
        self.abschluss['kassenstand'] = self.kassenbestand
        if differenz:
            self.abschluss['bemerkung'] = 'Abweichung der Kasse: %s' % getMoneyValue(differenz)
            if QtWidgets.QMessageBox.No == QtWidgets.QMessageBox.warning(self, 'Abweichung in der Kasse', 'Der Kassenstand entspricht nicht dem errechneten Kassenstand lauf Aufzeichnungen.\nAbweichungsbetrag: %s\nSoll der Abschluss mit Abweichung vorgenommen werden?' % getMoneyValue(differenz), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
                return
        else:
            self.abschluss['bemerkung'] = None
        s = Speicher()
        s.speichereAbschluss(self.abschluss)
        # Drucke Zählprotokoll
        self.mainwindow.reset()
        
        
    def calculate(self, foo=None):
        _summe = 0.0
        _scheine = 0.0
        summe_500 = self.ui.count_500.value() * 500
        self.ui.summe_500.setText(getMoneyValue(summe_500))
        _summe += summe_500
        _scheine += summe_500
        summe_200 = self.ui.count_200.value() * 200
        self.ui.summe_200.setText(getMoneyValue(summe_200))
        _summe += summe_200
        _scheine += summe_200
        summe_100 = self.ui.count_100.value() * 100
        self.ui.summe_100.setText(getMoneyValue(summe_100))
        _summe += summe_100
        _scheine += summe_100
        summe_50 = self.ui.count_50.value() * 50
        self.ui.summe_50.setText(getMoneyValue(summe_50))
        _summe += summe_50
        _scheine += summe_50
        summe_20 = self.ui.count_20.value() * 20
        self.ui.summe_20.setText(getMoneyValue(summe_20))
        _summe += summe_20
        _scheine += summe_20
        summe_10 = self.ui.count_10.value() * 10
        self.ui.summe_10.setText(getMoneyValue(summe_10))
        _summe += summe_10
        _scheine += summe_10
        summe_5 = self.ui.count_5.value() * 5
        self.ui.summe_5.setText(getMoneyValue(summe_5))
        _summe += summe_5
        _scheine += summe_5
        
        self.ui.summe_scheine.setText(getMoneyValue(_scheine))

        _muenzen = 0.0        
        summe_2 = self.ui.count_2.value() * 2
        self.ui.summe_2.setText(getMoneyValue(summe_2))
        _summe += summe_2
        _muenzen += summe_2
        summe_1 = self.ui.count_1.value()
        self.ui.summe_1.setText(getMoneyValue(summe_1))
        _summe += summe_1
        _muenzen += summe_1
        summe_050 = 0.50 * self.ui.count_050.value()
        self.ui.summe_050.setText(getMoneyValue(summe_050))
        _summe += summe_050
        _muenzen += summe_050
        summe_020 = 0.20 * self.ui.count_020.value()
        self.ui.summe_020.setText(getMoneyValue(summe_020))
        _summe += summe_020
        _muenzen += summe_020
        summe_010 = 0.10 * self.ui.count_010.value()
        self.ui.summe_010.setText(getMoneyValue(summe_010))
        _summe += summe_010
        _muenzen += summe_010
        summe_005 = 0.05 * self.ui.count_005.value()
        self.ui.summe_005.setText(getMoneyValue(summe_005))
        _summe += summe_005
        _muenzen += summe_005
        summe_002 = 0.02 * self.ui.count_002.value()
        self.ui.summe_002.setText(getMoneyValue(summe_002))
        _summe += summe_002
        _muenzen += summe_002
        summe_001 = 0.01 * self.ui.count_001.value()
        self.ui.summe_001.setText(getMoneyValue(summe_001))
        _summe += summe_001
        _muenzen += summe_001
        
        self.kassenbestand = _summe
        
        self.ui.summe_muenzen.setText(getMoneyValue(_muenzen))
        self.ui.summe_alles.setText(getMoneyValue(self.kassenbestand))
        self.ui.kassenstand_berechnet.setText(getMoneyValue(self.__kassenstand_berechnet))
        self.ui.differenz.setText(getMoneyValue(self.kassenbestand - self.__kassenstand_berechnet))

