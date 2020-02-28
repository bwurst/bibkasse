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
import sys, datetime

from gui.alte_abfuellungen_listentry import AbfuellungWidget
from gui.dialog_anrufen import DialogAnrufen

from lib.Speicher import Speicher
from lib.Vorgang import Vorgang
from lib.BelegHTML import BelegHTML
from lib.BelegThermo import BeleglisteThermo
from lib.SMS import receive_status
from gui.kundenauswahl import showKundenAuswahlDialog
from lib.Kassenbeleg import KassenbelegStornieren


class WidgetHistory(QtWidgets.QWidget):
    def __init__(self, mainwindow, extended = False, last10 = False):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        self.ui = None
        try:
            self.ui = uic.loadUi('ressource/ui/widget_history.ui', self.ui)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)
          
        self.year = datetime.date.today().year
        self.speicher = Speicher(self.year)

        self.__invoicelist_sorting = 'Name'

        self.__extended = extended
        self.__last10 = last10
        self.__showall = False
        self.__menu = False
        self.filter_kunde = None
        self.__aktueller_vorgang = None


        self.ui.input_suche.clicked = self.sucheClicked
        self.ui.input_suche.installEventFilter(self)
        self.ui.listWidget_2.itemClicked.connect(self.listWidgetClick)
        self.ui.listWidget_version.currentItemChanged.connect(self.versionAusgewaehlt)
        self.ui.button_bearbeiten.clicked.connect(self.vorgangOeffnen)
        self.ui.button_beleganzeigen.clicked.connect(self.belegAnzeigen)
        self.ui.button_rechnung_storno.clicked.connect(self.rechnungStornieren)
        self.ui.button_bezahlt.clicked.connect(self.toggleBezahlt)
    
        self.ui.combo_year.currentIndexChanged.connect(self.updateAlteVorgaenge)
        self.ui.combo_sortierung.currentIndexChanged.connect(self.sortingChanged)
        self.ui.input_suche.textChanged.connect(self.updateAlteVorgaenge)
        self.ui.button_sucheLeeren.clicked.connect(self.clearSuche)

        self.ui.button_reload.clicked.connect(self.reload)

        self.ui.button_listedrucken.clicked.connect(self.listedrucken)
        self.ui.button_extended.clicked.connect(self.extended)
        self.ui.button_anrufen.clicked.connect(self.anrufenClicked)
        self.ui.button_zurueckstellen.clicked.connect(self.zurueckstellen)
        self.ui.button_sammelbeleg.clicked.connect(self.vorgangKassieren)
        
        self.ui.button_sammelbeleg.hide()
        self.setupUI()
        

    def setupUI(self):
        #self.ui.listWidget_2.currentItemChanged.connect(self.vorgangAusgewaehlt)
        try:
            self.ui.listWidget_2.itemSelectionChanged.disconnect()
        except Exception:
            pass
        if self.__extended or self.__last10:
            self.ui.listWidget_2.itemSelectionChanged.connect(self.vorgangAusgewaehlt)

        if self.__extended:
            self.ui.button_listedrucken.setEnabled(False)
            self.ui.stackErweitert.setCurrentIndex(0)
        else:
            self.ui.label_dateiname.setText('---')
            self.ui.button_listedrucken.setEnabled(True)
            self.ui.stackErweitert.setCurrentIndex(1)

        if self.__last10 or self.__menu:
            self.ui.groupbox_filter.hide()
            self.ui.button_reload.hide()
            self.ui.stackErweitert.setCurrentIndex(0)
        else:
            self.ui.groupbox_filter.show()
            self.ui.button_reload.show()
            
        if self.__last10:
            self.ui.button_extended.hide()
            self.ui.button_listedrucken.hide()
        else:
            self.ui.button_extended.show()
            self.ui.button_listedrucken.show()

    def anrufenClicked(self):
        self.anrufen()
        if self.__menu:
            self.__menu = False

    def listWidgetClick(self, listWidgetItem = None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        if self.__extended or self.__last10:
            self.vorgangAusgewaehlt(listWidgetItem)
        elif not self.__menu:
            self.vorgangKassieren(listWidgetItem)

    def isShown(self):
        # beim Neu-Aufrufen ist Extended immer aus
        self.ui.button_extended.setChecked(False)
        self.__extended = False
        self.__menu = False
        self.__aktueller_vorgang = None
        # Status der SMS-Aussendungen prüfen
        receive_status(self.speicher.listVorgaengeUnbezahlt())
        self.setupUI()
        self.update()


    def update(self):
        self.setupUI()
        current_year = str(datetime.date.today().year)
        years = sorted(list(self.speicher.list_years()))

        self.ui.combo_year.currentIndexChanged[int].disconnect(self.updateAlteVorgaenge)

        self.ui.combo_year.clear()
        for y in years:
            self.ui.combo_year.addItem(y)
        self.ui.combo_year.setCurrentIndex(self.ui.combo_year.findText(current_year))
        self.ui.combo_year.currentIndexChanged[int].connect(self.updateAlteVorgaenge)
        self.updateAlteVorgaenge()
        self.ui.button_extended.setChecked(self.__extended)
        self.ui.button_anrufen.setChecked(False)
        self.ui.listWidget_version.clear()

    def clearSuche(self):
        self.filter_kunde = None
        self.ui.input_suche.clear()

    def sucheClicked(self):
        kunde = showKundenAuswahlDialog(neu=False)
        self.filter_kunde = kunde.ID()
        self.ui.input_suche.setText(kunde.getName())
        #self.ui.input_suche.setText( showTextInputDialog('Filter', [], self.ui.input_suche.text()))

    def updateAlteVorgaenge(self, foobar=None):
        button_alle = True
        self.year = str(self.ui.combo_year.currentText()).strip()
        if hasattr(self, 'speicher'):
            del self.speicher
        self.speicher = Speicher(self.year)
        self.ui.textBrowser.clear()
        self.__invoicelist = []
        if self.__last10:
            self.__invoicelist = self.mainwindow.letzte_belege
            button_alle = False
        elif self.__extended:
            if self.filter_kunde:
                self.__invoicelist = self.speicher.listVorgaengeByKunde(self.filter_kunde)
                button_alle = False
            elif self.__showall:
                button_alle = False
                self.__showall = False
                if self.__invoicelist_sorting == 'DateDesc':
                    self.__invoicelist = self.speicher.listVorgaengeByDateDesc()
                elif self.__invoicelist_sorting == 'DateAsc':
                    self.__invoicelist = self.speicher.listVorgaengeByDateAsc()
                elif self.__invoicelist_sorting == 'Name':
                    self.__invoicelist = self.speicher.listVorgaengeByName()
                elif self.__invoicelist_sorting == 'Amount':
                    self.__invoicelist = self.speicher.listVorgaengeByAmount()
                else:
                    self.__invoicelist = self.speicher.listVorgaenge()
            else:
                # Erweitert aber kein Alles anzeigen und kein Kundenfilter
                # => Unbezahlte und zurückgestellte und Show-All-Bbutton
                self.__invoicelist = self.speicher.listVorgaengeUnbezahlt(postponed=True)
                button_alle = True
        else:
            # Nicht erweitert
            # => Unbezahlte
            self.__invoicelist = self.speicher.listVorgaengeUnbezahlt()
            button_alle = False
            
        self.ui.listWidget_2.clear()
        if self.filter_kunde and not self.__invoicelist:
            label = QtWidgets.QLabel("Keine Ergebnisse")
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, label)
        else:
            for inv in self.__invoicelist:
                entry = AbfuellungWidget(inv, extended=(self.__extended or self.__last10))
                entry.anrufenClicked.connect(self.anrufSlot(inv))
                entry.menuClicked.connect(self.menuSlot(inv))
                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 68))
                self.ui.listWidget_2.addItem(item)
                self.ui.listWidget_2.setItemWidget(item, entry)

        if button_alle:
            button_showall = QtWidgets.QPushButton("Alle Vorgänge anzeigen")
            button_showall.clicked.connect(self.showall)
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, button_showall)
        
        self.vorgangAusgewaehlt()

    def menuSlot(self, invoice):
        def _menu():
            self.showMenu(invoice=invoice)
        return _menu

    def anrufSlot(self, invoice):
        def _anruf():
            self.anrufen(invoice=invoice)
        return _anruf

    def showMenu(self, invoice=None):
        self.__menu = True
        self.update()
        self.vorgangAusgewaehlt(invoice=invoice)

    def showall(self):
        self.__showall = True
        self.updateAlteVorgaenge()

    def extended(self):
        self.__menu = False
        self.__extended = self.ui.button_extended.isChecked()
        self.__aktueller_vorgang = None
        self.update()

    def listedrucken(self):
        vorgaenge = []
        for inv in self.__invoicelist:
            vorgaenge.append(inv)
        if len(vorgaenge) > 20:
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Wirklich Liste drucken?', 'Momentan sind %i Kunden auf der Liste.\nIst das korrekt?' % len(vorgaenge), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                return False
        if not BeleglisteThermo(vorgaenge, self.mainwindow.printer):
            QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)


    def updateVersionen(self, handle):
        l = self.ui.listWidget_version
        l.clear()
        versionen = self.speicher.getVorgangVersionen(handle)
        versionsnummern = list(versionen.keys())
        versionsnummern.sort(reverse=True)
        newest = max(versionsnummern)
        select = None
        for version in versionsnummern:
            v = versionen[version]
            i = QtWidgets.QListWidgetItem(parent=l)
            i.setData(1, version)
            i.setText('Version %i, %s, %s' % (version, v[0], v[1]))
            if version == newest:
                select = i
            l.addItem(i)
        l.setCurrentItem(select)
        


    def versionAusgewaehlt(self, listWidgetItem = None, nonsense = None):
        invoice = self.__aktueller_vorgang
        if not listWidgetItem:
            return None
        version = int(listWidgetItem.data(1))
        if version:
            if not invoice:
                invoice = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0]).getVorgang()
            handle = invoice.ID
            invoice = self.speicher.ladeVorgang(handle, version=version)
            text = BelegHTML(invoice, public=False)
            self.ui.textBrowser.setHtml(text)


    def vorgangAusgewaehlt(self, listWidgetItem = None, nonsense = None, invoice=None):
        if not invoice:
            if len(self.ui.listWidget_2.selectedItems()) > 0:
                if len(self.ui.listWidget_2.selectedItems()) > 1:
                    invoice = Vorgang()
                    zahlungen = False
                    for selectedItem in self.ui.listWidget_2.selectedItems():
                        tmp = self.speicher.ladeVorgang(self.ui.listWidget_2.itemWidget(selectedItem).getVorgang().ID)
                        invoice.vorgangHinzufuegen(tmp)
                        if tmp.getZahlungen():
                            zahlungen = True
                    self.ui.label_dateiname.setText(u'<em>Mehrere ausgewählt</em>')
                    if not zahlungen:
                        self.ui.button_sammelbeleg.show()
                else:
                    widget = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0])
                    if type(widget) == AbfuellungWidget:
                        invoice = self.speicher.ladeVorgang(widget.getVorgang().ID)
                        self.ui.label_dateiname.setText('%s' % invoice.ID)
                    self.ui.button_sammelbeleg.hide()
        
        if invoice:
            self.__aktueller_vorgang = invoice
            if invoice.isRechnung():
                self.ui.button_anrufen.setEnabled(False)
                self.ui.button_bearbeiten.setEnabled(False)
                self.ui.button_rechnung_storno.setEnabled(True)
                self.ui.button_beleganzeigen.setEnabled(True)
                self.ui.button_bezahlt.setEnabled(False)
            else:
                self.ui.button_bearbeiten.setEnabled(True)
                self.ui.button_rechnung_storno.setEnabled(False)
                self.ui.button_beleganzeigen.setEnabled(False)
                self.ui.button_bezahlt.setEnabled(True)
                self.ui.button_anrufen.setEnabled(True)
            

            text = BelegHTML(invoice, public=False)
            self.ui.textBrowser.setHtml(text)

            if invoice.ID:
                # Wenn mehrere Belegen ausgewählt wurden, ist das None
                self.ui.listWidget_version.show()
                self.updateVersionen(invoice.ID)
            else:
                self.ui.listWidget_version.hide()
                self.ui.button_bezahlt.setEnabled(False)
                self.ui.button_anrufen.setEnabled(False)

            label = u'Ist bezahlt'
            if invoice.getPayed() and not invoice.isRechnung():
                label = u'Ist noch nicht bezahlt'
            self.ui.button_bezahlt.setText(label)

            if invoice.getStatus() == 'postponed':
                self.ui.button_zurueckstellen.setText('Nicht mehr zurückstellen')
            else:
                self.ui.button_zurueckstellen.setText('Zurückstellen')
            self.ui.button_zurueckstellen.setEnabled(not (invoice.getPayed() or invoice.getBanktransfer()))

            if self.year != str(datetime.date.today().year):
                self.ui.button_bearbeiten.setEnabled(False)
                self.ui.button_anrufen.setEnabled(False)
            if len(self.ui.listWidget_2.selectedItems()) > 1:
                self.ui.button_bearbeiten.setEnabled(False)
                self.ui.button_anrufen.setEnabled(False)
        else:
            # Kein Vorgang ausgewählt
            self.ui.textBrowser.clear()
            self.ui.listWidget_version.clear()
            self.ui.button_anrufen.setEnabled(False)
            self.ui.button_bezahlt.setEnabled(False)
            self.ui.button_bearbeiten.setEnabled(False)
            self.ui.button_beleganzeigen.setEnabled(False)
            self.ui.button_zurueckstellen.setEnabled(False)
            self.ui.label_dateiname.setText(u'<em>Kein Vorgang ausgewählt</em>') 
            self.__aktueller_vorgang = None

    def anrufen(self, listWidgetItem = None, invoice = None):
        if self.__aktueller_vorgang:
            invoice = self.__aktueller_vorgang
        if not invoice:
            if not listWidgetItem:
                listWidgetItem = self.ui.listWidget_2.currentItem()
            invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getVorgang()
        dialog = DialogAnrufen(invoice)
        dialog.show()
        dialog.exec_()
        if self.__extended:
            self.vorgangAusgewaehlt(invoice=invoice)
        if self.__menu:
            self.__menu = False
            self.update()
      
    def zurueckstellen(self, listWidgetItem=None):  
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getVorgang()
        if invoice.getStatus() == 'postponed':
            invoice.setStatus(None)
        else:
            invoice.setStatus('postponed')
        self.speicher.speichereVorgang(invoice)
        if self.__extended:
            self.vorgangAusgewaehlt(invoice=invoice)
        if self.__menu:
            self.__menu = False
            self.update()
        
        
    def vorgangOeffnen(self, listWidgetItem=None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getVorgang()
        if invoice.isRechnung():
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Aus diesem Vorgang wurde eine Rechnung erzeugt, daher kann daran nichts mehr geändert werden.', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False
        self.mainwindow.vorgangOeffnen(invoice)
            

    def vorgangKassieren(self, listWidgetItem=None):
        invoice = self.__aktueller_vorgang
        if not invoice:
            if not listWidgetItem:
                listWidgetItem = self.ui.listWidget_2.currentItem()
            invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getVorgang()
        if invoice.originale and not invoice.ID:
            self.speicher.speichereVorgang(invoice)
            for handle in invoice.originale:
                old = self.speicher.ladeVorgang(handle)
                self.speicher.loescheVorgang(old)
        self.mainwindow.vorgangKassieren(invoice)


    def toggleBezahlt(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Vorgang ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        widget = self.ui.listWidget_2.itemWidget(item)
        invoice = widget.getVorgang()
        invoice.setPayed(not invoice.getPayed())
        if invoice.getPayed():
            invoice.setBanktransfer(False)
        widget.update()
        self.speicher.speichereVorgang(invoice)
        if self.__extended:
            self.vorgangAusgewaehlt(invoice=invoice)
        if self.__menu:
            self.__menu = False
            self.update()


    def reload(self):
        self.updateAlteVorgaenge()
        

    def sortingChanged(self, newSortingIndex):
        if newSortingIndex == 0:
            self.__invoicelist_sorting = 'DateDesc'
        elif newSortingIndex == 1:
            self.__invoicelist_sorting = 'DateAsc'
        elif newSortingIndex == 2:
            self.__invoicelist_sorting = 'Name'
        elif newSortingIndex == 3:
            self.__invoicelist_sorting = 'Amount'
        self.updateAlteVorgaenge()

    def belegAnzeigen(self):
        item = self.ui.listWidget_2.currentItem()
        if not item or len(self.ui.listWidget_2.selectedItems()) > 1:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Bitte genau einen Vorgang auswählen', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        if item:
            invoice = self.ui.listWidget_2.itemWidget(item).getVorgang()

            if not invoice.getRechnungsnummer():
                # Gibt keinen Beleg
                print('kein Beleg gefunden')
                return
            filename = 'daten/rechnungen/' + invoice.getRechnungsnummer() + '.pdf'
            self.mainwindow.belegAnzeigen(filename)

    
    def rechnungStornieren(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Keine Rechnung ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        if len(self.ui.listWidget_2.selectedItems()) > 1:
            QtWidgets.QMessageBox.warning(self, u'Mehrere Belege ausgewählt', u'Rechnungen können nur einzeln storniert werden', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        vorgang = self.ui.listWidget_2.itemWidget(item).getVorgang()
        if not vorgang.isRechnung():
            QtWidgets.QMessageBox.warning(self, u'Dies ist keine Rechnung', u'Dieser Vorgang repräsentiert keine Rechnung.', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        rechnungsnr = vorgang.getRechnungsnummer()
        kb = self.speicher.getKassenbeleg(renr=rechnungsnr)
        adresse = kb['kunde']['adresse']
        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(self, u'Rechnung Stornieren', u'Die Rechnung Nr.<br/><strong>%s</strong><br/>an<br />%s<br/>soll storniert werden. Ist das okay?' % (rechnungsnr, adresse), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
            # FIXME: Erstelle Gegenbuchung
            filename = KassenbelegStornieren(kb)
        self.updateAlteVorgaenge()

    


    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()

        return False
