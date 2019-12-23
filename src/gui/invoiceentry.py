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

from lib.Preisliste import Preisliste

from PyQt5 import QtCore, QtWidgets, uic
import sys, datetime

from gui.numberinput import showNumberInputDialog
from gui.valueinput import showValueInputDialog
from gui.textinput import showTextInputDialog

from lib.helpers import getMoneyValue, renderIntOrFloat

def showInvoiceEntryDialog(invoiceEntry):
        invoiceentry = InvoiceEntryDialog(invoiceEntry)
        if invoiceentry:
            invoiceentry.show()
            invoiceentry.exec_()


class InvoiceEntryDialog(QtWidgets.QDialog):
    def __init__(self, invoiceEntry):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/invoiceentry.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        
        self.showFullScreen()

        self.__preisliste = Preisliste()
        
        # Kopie für "Abbrechen"
        self.__backup = invoiceEntry.copy()
        self.__backup_preislistenbezug = (invoiceEntry.preislistenID, invoiceEntry.preisliste_link)
        self.__default = None
        if invoiceEntry.preislistenID:
            self.__default = invoiceEntry.copy()
        
        self.invoiceEntry = invoiceEntry
        
        self.updateComboProdukt()
        self.updateOldValues()
        self.updateDefaultValues()        
        self.update()
        if not self.invoiceEntry.preislistenID:
            self.ui.combo_produkt.setCurrentIndex(0)
        self.ui.input_anzahl.clicked = self.showNumberDialog
        self.ui.input_einheit.clicked = self.showEinheitDialog
        self.ui.input_beschreibung.clicked = self.showBeschreibungDialog
        self.ui.input_einzelpreis.clicked = self.showValueDialog
        self.ui.input_anzahl.installEventFilter(self)
        self.ui.input_einheit.installEventFilter(self)
        self.ui.input_beschreibung.installEventFilter(self)
        self.ui.input_einzelpreis.installEventFilter(self)
        self.ui.button_ok.clicked.connect(self.okPressed)
        self.ui.button_abbrechen.clicked.connect(self.cancelPressed)

        self.ui.input_anzahl.editingFinished.connect(self.anzahlEditingFinished)
        self.ui.input_einheit.editingFinished.connect(self.einheitEditingFinished)
        self.ui.input_beschreibung.editingFinished.connect(self.beschreibungEditingFinished)
        self.ui.input_einzelpreis.editingFinished.connect(self.einzelpreisEditingFinished)
        self.ui.combo_steuersatz.currentIndexChanged.connect(self.comboSteuersatzChanged)

        self.ui.combo_produkt.currentIndexChanged.connect(self.comboProduktChanged)
        self.ui.combo_rabattstufe.currentIndexChanged.connect(self.comboRabattstufeChanged)

        self.ui.button_einheit_default.clicked.connect(self.buttonEinheitDefaultClicked)
        self.ui.button_beschreibung_default.clicked.connect(self.buttonBeschreibungDefaultClicked)
        self.ui.button_einzelpreis_default.clicked.connect(self.buttonEinzelpreisDefaultClicked)
        self.ui.button_steuersatz_default.clicked.connect(self.buttonSteuersatzDefaultClicked)

        self.ui.dateedit_leistungsdatum.dateChanged.connect(self.dateChanged)


    def okPressed(self):
        alterPreis = self.__backup.getPreis()
        neuerPreis = self.invoiceEntry.getPreis()
        if alterPreis * neuerPreis < 0:
            # Minus mal Minus gibt Plus, wenn es also < 0 ist, hat sich das vorzeichen geändert.
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Möglicher Fehler', u'Das Vorzeichen des Einzelpreises hat sich geändert!\nIst das korrekt?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                self.invoiceEntry.setPreis(-1 * neuerPreis)
                self.update()
                return None
        if self.__backup.getDatum() != self.invoiceEntry.getDatum():
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Möglicher Fehler', u'Das Leistungsdatum dieses Eintrags wurde verändert!\nIst das korrekt?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                self.invoiceEntry.setDatum(self.__backup.getDatum())
                d = self.__backup.getDatum()
                if not d:
                    d = datetime.date.today()
                self.ui.dateedit_leistungsdatum.setDate(QtCore.QDate(d.year, d.month, d.day))
                return None
                
        self.__backup.unregister()
        if self.__default:
            self.__default.unregister()
        self.close()
        
    def cancelPressed(self):
        self.invoiceEntry.importValues(self.__backup)
        self.invoiceEntry.setPreislistenID(self.__backup_preislistenbezug[0], self.__backup_preislistenbezug[1])
        self.__backup.unregister()
        if self.__default:
            self.__default.unregister()
        self.close()

    def buttonEinheitDefaultClicked(self):
        if not self.__default:
            return
        self.invoiceEntry.setEinheit(self.ui.label_einheit_default.text())
        self.update()

    def buttonBeschreibungDefaultClicked(self):
        if not self.__default:
            return
        self.invoiceEntry.setPreislistenID(self.__default.preislistenID, self.invoiceEntry.preisliste_link)
        self.invoiceEntry.setBeschreibung(self.ui.label_beschreibung_default.text())
        self.update()

    def buttonEinzelpreisDefaultClicked(self):
        if not self.__default:
            return
        self.invoiceEntry.setRabattstufe(self.__default.getRabattstufe())
        self.invoiceEntry.setPreis(self.__default.getPreis())
        self.update()


    def buttonSteuersatzDefaultClicked(self):
        if not self.__default:
            return
        self.ui.combo_steuersatz.setCurrentIndex(self.ui.combo_steuersatz.findText(self.ui.label_steuersatz_default.text()))

    def anzahlEditingFinished(self):
        self.invoiceEntry.setStueckzahl( int(self.ui.input_anzahl.text()) )
        self.comboRabattstufeChanged()
        self.update()

    def einheitEditingFinished(self):
        self.invoiceEntry.setEinheit( str(self.ui.input_einheit.text()) ) 
        self.update()

    def beschreibungEditingFinished(self):
        self.invoiceEntry.setBeschreibung( str(self.ui.input_beschreibung.text()) )
        self.update()

    def einzelpreisEditingFinished(self):
        betrag = self.ui.input_einzelpreis.text()
        betrag = betrag.replace(u' €', '')
        betrag = betrag.replace(',', '.')
        self.invoiceEntry.setPreis( float(betrag) )
        self.update()

    def comboSteuersatzChanged(self):
        text = self.ui.combo_steuersatz.currentText()
        (value, percent) = text.split(' ', 1)
        try:
            value = float(value)
        except:
            value = 0.0
            self.ui.combo_steuersatz.setCurrentIndex(0)
        self.invoiceEntry.setSteuersatz(value)
        self.update()
        

    def showNumberDialog(self):
        showNumberInputDialog(self.invoiceEntry)
        self.comboRabattstufeChanged()
        self.update()

    def showEinheitDialog(self):
        self.invoiceEntry.setEinheit( showTextInputDialog('Einheit', ['Stk', 'Liter', 'Ztr', 'Psch'], self.invoiceEntry.getEinheit()))
        self.update()

    def showBeschreibungDialog(self):
        self.invoiceEntry.setBeschreibung( showTextInputDialog('Beschreibung', [], self.invoiceEntry.getBeschreibung()))
        self.update()

    def showValueDialog(self):
        showValueInputDialog(self.invoiceEntry)
        self.update()

    def setzePreiskategorie(self, nonsense=None):
        self.invoiceEntry.setPreislistenID(self.preislisteIDfuerBeschreibung(self.ui.combo_produkt.currentText()), True) 
        self.update()


    def preislisteIDfuerBeschreibung(self, beschr):
        for (key, val) in self.preislistenEintraege.items():
            if str(val) == str(beschr):
                return key
        return None

    def preislisteBeschreibungfuerID(self, ID):
        for (key, val) in self.preislistenEintraege.items():
            if key == ID:
                return val
        return None

    def comboProduktChanged(self, newIndex):
        self.updateDefaultValues()
        self.update()

    def comboRabattstufeChanged(self, newIndex = None):
        if self.__default:
            rabatte = self.__default.listRabattStufen()
            self.__default.setStueckzahl(self.invoiceEntry.getStueckzahl())
            if newIndex is not None:
                self.__default.setRabattstufe(rabatte.keys()[newIndex])
            if self.__default.getAutomatischeRabattstufe() == self.__default.getRabattstufe():
                self.__default.setRabattstufe(None)
            try:
                cur = list(rabatte.keys()).index(self.__default.getRabattstufe())
                self.ui.combo_rabattstufe.blockSignals(True)
                self.ui.combo_rabattstufe.setCurrentIndex(cur)
            except ValueError:
                # Wenn es keine Rabatt-Stufen gibt, dann halt nicht
                pass
            finally:
                self.ui.combo_rabattstufe.blockSignals(False)
        self.update()

    def dateChanged(self, qdate):
        self.invoiceEntry.setDatum(datetime.date(qdate.year(), qdate.month(), qdate.day()))
        

    def updateDefaultValues(self):
        if self.ui.combo_produkt.currentIndex() < 2:
            if self.__default:
                self.__default.unregister()
            self.__default = None
        else:
            if not self.__default:
                self.__default = self.invoiceEntry.copy() 
            self.__default.setPreislistenID(self.preislisteIDfuerBeschreibung(self.ui.combo_produkt.currentText()), False) 
            self.__default.setStueckzahl(self.invoiceEntry.getStueckzahl())
            self.__default.setEinheit(self.__default.preislistenWert('einheit'))
            self.__default.setBeschreibung(self.__default.preislistenWert('beschreibung'))
            self.__default.setPreis(self.__default.preislistenWert('einzelpreis'))
            self.__default.setSteuersatz(self.__default.preislistenWert('steuersatz'))

    def updateOldValues(self):
        self.ui.label_anzahl_alt.setText(renderIntOrFloat(self.__backup.getStueckzahl()))
        self.ui.label_einheit_alt.setText(str(self.__backup.getEinheit()))
        self.ui.label_beschreibung_alt.setText(str(self.__backup.getBeschreibung()))
        self.ui.label_einzelpreis_alt.setText(getMoneyValue(self.__backup.getPreis()))
        self.ui.label_steuersatz_alt.setText(u'%.1f %%' % self.__backup.getSteuersatz())
        self.ui.label_gesamtpreis_alt.setText(getMoneyValue(self.__backup.getSumme()))
        d = self.__backup.getDatum()
        if not d:
            d = datetime.date.today()
        self.ui.dateedit_leistungsdatum.setDate(QtCore.QDate(d.year, d.month, d.day))

    def updateComboProdukt(self):
        self.ui.combo_produkt.blockSignals(True)
        self.ui.combo_rabattstufe.blockSignals(True)
        self.preislistenEintraege = self.__preisliste.getBeschreibungen()
        self.ui.combo_produkt.clear()
        beschreibungen = sorted(list(self.preislistenEintraege.values()))
        beschreibungen = ['Kein Produkt aus der Preisliste', '---------------------------------',] + beschreibungen
        self.ui.combo_produkt.addItems(beschreibungen)
        if self.__default:
            self.ui.combo_produkt.setCurrentIndex( self.ui.combo_produkt.findText(self.preislisteBeschreibungfuerID(self.__default.preislistenID)) )
            rabatte = self.__preisliste.rabattStufen(self.__default.preislistenID)
            rabattArt = list(rabatte.keys())[0][0]
            stufenString = u'Ab %i Stück: je %.2f €'
            if rabattArt == 'liter':
                stufenString = u'Ab %i Liter: je %.2f €'
                
            if len(rabatte) > 1:
                self.ui.combo_rabattstufe.clear()
                self.ui.combo_rabattstufe.addItems( [stufenString % (key[1], value) for key, value in rabatte.items()] )
                self.ui.combo_rabattstufe.setEnabled(True)
                index = 0
                try:
                    index = list(rabatte.keys()).index(self.__default.getRabattstufe())
                except ValueError:
                    index = 0
                finally:
                    self.ui.combo_rabattstufe.setCurrentIndex(index)
            else:
                self.ui.combo_rabattstufe.clear()
                self.ui.combo_rabattstufe.setEnabled(False)
        else:
            self.ui.combo_rabattstufe.clear()
            self.ui.combo_rabattstufe.setEnabled(False)
        self.ui.combo_produkt.blockSignals(False)
        self.ui.combo_rabattstufe.blockSignals(False)

    def update(self):
        self.ui.label_anzahl_alt.setText(u'%i' % self.__backup.getStueckzahl())
        self.ui.label_einheit_alt.setText(str(self.__backup.getEinheit()))
        self.ui.label_beschreibung_alt.setText(str(self.__backup.getBeschreibung()))
        self.ui.input_anzahl.setText(u'%i' % int(self.invoiceEntry.getStueckzahl()))
        self.ui.input_einheit.setText(u'%s' % self.invoiceEntry.getEinheit())
        self.ui.input_beschreibung.setText(u'%s' % self.invoiceEntry.getBeschreibung())
        self.ui.input_einzelpreis.setText(u'%s' % getMoneyValue(self.invoiceEntry.getPreis()))
        self.ui.label_gesamtpreis.setText(u'%s' % getMoneyValue(self.invoiceEntry.getSumme()))
        index = self.ui.combo_steuersatz.findText(u'%.1f' % self.invoiceEntry.getSteuersatz(), flags=QtCore.Qt.MatchStartsWith)
        if index == -1:
            self.ui.combo_steuersatz.addItem(u'%.1f %%' % self.invoiceEntry.getSteuersatz())
            index = self.ui.combo_steuersatz.findText(u'%.1f' % self.invoiceEntry.getSteuersatz(), flags=QtCore.Qt.MatchStartsWith)
        self.ui.combo_steuersatz.setCurrentIndex(index)

        if self.__default:
            self.ui.label_einheit_default.setText(self.__default.getEinheit())
            self.ui.label_beschreibung_default.setText(self.__default.getBeschreibung())
            self.ui.label_einzelpreis_default.setText(getMoneyValue(self.__default.getPreis()))
            self.ui.label_steuersatz_default.setText(u'%.1f %%' % self.__default.getSteuersatz())
        else:
            self.ui.label_einheit_default.setText(u'----')
            self.ui.label_beschreibung_default.setText(u'----')
            self.ui.label_einzelpreis_default.setText(u'----')
            self.ui.label_steuersatz_default.setText(u'----')

        self.updateComboProdukt()            
        
    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()

        return False
        
        
