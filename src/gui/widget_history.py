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
import tempfile, subprocess, os, sys, datetime
import cups

from gui.alte_abfuellungen_listentry import AbfuellungWidget
from gui.textinput import showTextInputDialog
from gui.dialog_anrufen import DialogAnrufen
from gui.rechnungdialog import showRechnungDialog

from lib.Speicher import Speicher
from lib.Beleg import Beleg
from lib.BelegHTML import BelegHTML
from lib.BelegThermo import BelegThermo, BeleglisteThermo
from lib.BelegRechnung import BelegRechnung, rechnungsPDFDatei, storniereRechnung
from lib.BioBeleg import BioBeleg
from lib.SMS import receive_status
from gui.kundenauswahl import showKundenAuswahlDialog


PRINTER_OPTIONS = {'media': 'A4',
                   'copies': '1',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}


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
        self.filter_kunde = None


        self.ui.input_suche.clicked = self.sucheClicked
        self.ui.input_suche.installEventFilter(self)
        self.ui.listWidget_2.itemClicked.connect(self.listWidgetClick)
        #self.ui.listWidget_2.currentItemChanged.connect(self.belegAusgewaehlt)
        if self.__extended or self.__last10:
            self.ui.listWidget_2.itemSelectionChanged.connect(self.belegAusgewaehlt)
        self.ui.listWidget_version.currentItemChanged.connect(self.versionAusgewaehlt)
        self.ui.button_bearbeiten.clicked.connect(self.belegOeffnen)
        self.ui.button_belegdrucken.clicked.connect(self.belegDruckenThermo)
        self.ui.button_rechnung.clicked.connect(self.rechnungAusBeleg)
        self.ui.button_rechnung_storno.clicked.connect(self.rechnungStornieren)
        self.ui.button_ueberweisung.clicked.connect(self.toggleUeberweisung)
        self.ui.button_bezahlt.clicked.connect(self.toggleBezahlt)
        self.ui.button_bio.clicked.connect(self.toggleBio)
    
        self.ui.combo_year.currentIndexChanged.connect(self.updateAlteBelege)
        self.ui.combo_sortierung.currentIndexChanged.connect(self.sortingChanged)
        self.ui.input_suche.textChanged.connect(self.updateAlteBelege)
        self.ui.button_sucheLeeren.clicked.connect(self.clearSuche)

        self.ui.button_reload.clicked.connect(self.reload)

        self.ui.button_listedrucken.clicked.connect(self.listedrucken)
        self.ui.button_extended.clicked.connect(self.extended)
        self.ui.button_anrufen.clicked.connect(self.anrufenClicked)


    def anrufenClicked(self):
        if self.ui.button_anrufen.isChecked():
            belege = self.speicher.listBelegeUnbezahlt()
            # Status der SMS-Aussendungen prüfen
            receive_status(belege)
        self.updateAlteBelege()

    def listWidgetClick(self, listWidgetItem = None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        if self.__extended or self.__last10:
            self.belegAusgewaehlt(listWidgetItem)
        elif self.ui.button_anrufen.isChecked():
            self.anrufen(listWidgetItem)
        else:
            self.belegKassieren(listWidgetItem)

          

    def update(self):
        current_year = str(datetime.date.today().year)
        years = sorted(list(self.speicher.list_years()))

        self.ui.combo_year.currentIndexChanged[int].disconnect(self.updateAlteBelege)

        self.ui.combo_year.clear()
        for y in years:
            self.ui.combo_year.addItem(y)
        self.ui.combo_year.setCurrentIndex(self.ui.combo_year.findText(current_year))
        self.ui.combo_year.currentIndexChanged[int].connect(self.updateAlteBelege)
        self.updateAlteBelege()
        self.ui.button_extended.setChecked(self.__extended)
        self.ui.button_anrufen.setChecked(False)
        if self.__extended:
            self.ui.button_listedrucken.setEnabled(False)
            self.ui.stackErweitert.setCurrentIndex(0)
        else:
            self.ui.button_listedrucken.setEnabled(True)
            self.ui.stackErweitert.setCurrentIndex(1)
        if self.__last10:
            self.ui.button_extended.hide()
            self.ui.button_listedrucken.hide()
            self.ui.stackErweitert.setCurrentIndex(0)

    def clearSuche(self):
        self.filter_kunde = None
        self.ui.input_suche.clear()

    def sucheClicked(self):
        kunde = showKundenAuswahlDialog(neu=False)
        self.filter_kunde = kunde.ID()
        self.ui.input_suche.setText(kunde.getName())
        #self.ui.input_suche.setText( showTextInputDialog('Filter', [], self.ui.input_suche.text()))

    def updateAlteBelege(self, foobar=None):
        self.year = str(self.ui.combo_year.currentText()).strip()
        if self.__last10:
            self.__invoicelist = self.mainwindow.letzte_belege
        else:
            if hasattr(self, 'speicher'):
                del self.speicher
            self.speicher = Speicher(self.year)
            self.ui.textBrowser.clear()
            self.__invoicelist = []
            if self.filter_kunde:
                self.__invoicelist = self.speicher.listBelegeByKunde(self.filter_kunde)
            elif not self.__extended:
                self.__invoicelist = self.speicher.listBelegeUnbezahlt()
            if self.__showall and self.__extended and not self.filter_kunde:
                self.__showall = False
                if self.__invoicelist_sorting == 'DateDesc':
                    self.__invoicelist = self.speicher.listBelegeByDateDesc()
                elif self.__invoicelist_sorting == 'DateAsc':
                    self.__invoicelist = self.speicher.listBelegeByDateAsc()
                elif self.__invoicelist_sorting == 'Name':
                    self.__invoicelist = self.speicher.listBelegeByName()
                elif self.__invoicelist_sorting == 'Amount':
                    self.__invoicelist = self.speicher.listBelegeByAmount()
                else:
                    self.__invoicelist = self.speicher.listBelege()

        if self.filter_kunde and not self.__invoicelist:
            label = QtWidgets.QLabel("Keine Ergebnisse")
            self.ui.listWidget_2.clear()
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, label)
        elif not self.__invoicelist and self.__extended and not self.__last10:
            button_showall = QtWidgets.QPushButton("Alle Belege anzeigen")
            button_showall.clicked.connect(self.showall)
            self.ui.listWidget_2.clear()
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, button_showall)
        else:
            self.ui.listWidget_2.clear()
            for inv in self.__invoicelist:
                entry = AbfuellungWidget(inv)
                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 68))
                self.ui.listWidget_2.addItem(item)
                self.ui.listWidget_2.setItemWidget(item, entry)
        self.belegAusgewaehlt()

    def showall(self):
        self.__showall = True
        self.updateAlteBelege()

    def extended(self):
        if self.__extended:
            self.mainwindow.showWidget('history')
        else:
            self.mainwindow.showWidget('history_complete')

    def listedrucken(self):
        belege = []
        for inv in self.__invoicelist:
            belege.append(inv)
        if len(belege) > 20:
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Wirklich Liste drucken?', 'Momentan sind %i Kunden auf der Liste.\nIst das korrekt?' % len(belege), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                return False
        if not BeleglisteThermo(belege, self.mainwindow.printer):
            QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)


    def updateVersionen(self, handle):
        l = self.ui.listWidget_version
        l.clear()
        versionen = self.speicher.getBelegVersionen(handle)
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
        if not listWidgetItem:
            return None
        version = int(listWidgetItem.data(1))
        if version:
            invoice = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0]).getBeleg()
            handle = invoice.ID
            invoice = self.speicher.ladeBeleg(handle, version=version)
            text = BelegHTML(invoice, public=False)
            self.ui.textBrowser.setHtml(text)
        


    def belegAusgewaehlt(self, listWidgetItem = None, nonsense = None):
        invoice = None
        if len(self.ui.listWidget_2.selectedItems()) > 0:
            if len(self.ui.listWidget_2.selectedItems()) > 1:
                invoice = Beleg()
                for selectedItem in self.ui.listWidget_2.selectedItems():
                    tmp = self.speicher.ladeBeleg(self.ui.listWidget_2.itemWidget(selectedItem).getBeleg().ID)
                    invoice.belegHinzufuegen(tmp)
                self.ui.label_dateiname.setText(u'<em>Mehrere ausgewählt</em>')
            else:
                widget = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0])
                if type(widget) == AbfuellungWidget:
                    invoice = self.speicher.ladeBeleg(widget.getBeleg().ID)
                    self.ui.label_dateiname.setText('%s' % invoice.ID)

        if invoice:
            self.ui.button_belegdrucken.setEnabled(True)

            self.ui.button_rechnung.setEnabled(True)
            if invoice.isRechnung():
                self.ui.button_bearbeiten.setEnabled(False)
                self.ui.button_rechnung.setText("Rechnung anzeigen")
                self.ui.button_rechnung_storno.setEnabled(True)
                self.ui.button_bio.setEnabled(True)
                self.ui.button_bio.setChecked(invoice.isBio())
            else:
                self.ui.button_bearbeiten.setEnabled(True)
                self.ui.button_rechnung.setText("Rechnung ausstellen")
                self.ui.button_rechnung_storno.setEnabled(False)
                self.ui.button_bio.setEnabled(False)
                self.ui.button_bio.setChecked(False)
            

            text = BelegHTML(invoice, public=False)
            self.ui.textBrowser.setHtml(text)

            if invoice.ID:
                # Wenn mehrere Belegen ausgewählt wurden, ist das False
                self.ui.listWidget_version.show()
                self.updateVersionen(invoice.ID)
            else:
                self.ui.listWidget_version.hide()


            self.ui.button_ueberweisung.setEnabled(not invoice.getPayed())
            label = u'wird überwiesen'
            if invoice.getBanktransfer():
                label = u'wird bar bezahlt'
            self.ui.button_ueberweisung.setText(label)
            

            self.ui.button_bezahlt.setEnabled(not invoice.getBanktransfer())
            label = u'Ist bezahlt'
            if invoice.getPayed():
                label = u'Ist noch nicht bezahlt'
            self.ui.button_bezahlt.setText(label)

            if self.year != str(datetime.date.today().year):
                self.ui.button_bearbeiten.setEnabled(False)
            if len(self.ui.listWidget_2.selectedItems()) > 1:
                self.ui.button_bearbeiten.setEnabled(False)
        else:
            # Kein Beleg ausgewählt
            self.ui.textBrowser.clear()
            self.ui.listWidget_version.clear()
            self.ui.button_ueberweisung.setEnabled(False)
            self.ui.button_bio.setEnabled(False)
            self.ui.button_bezahlt.setEnabled(False);
            self.ui.button_bearbeiten.setEnabled(False)
            self.ui.button_rechnung.setEnabled(False)
            self.ui.button_belegdrucken.setEnabled(False)
            self.ui.label_dateiname.setText(u'<em>Kein Beleg ausgewählt</em>') 

    def anrufen(self, listWidgetItem = None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getBeleg()
        dialog = DialogAnrufen(invoice)
        dialog.show()
        dialog.exec_()
        self.updateAlteBelege()
        
    def belegOeffnen(self, listWidgetItem=None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getBeleg()
        if invoice.isRechnung():
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Aus diesem Beleg wurde eine Rechnung erzeugt, daher kann daran nichts mehr geändert werden.', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False
        self.mainwindow.belegOeffnen(invoice)
            

    def belegKassieren(self, listWidgetItem=None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        invoice = self.ui.listWidget_2.itemWidget(listWidgetItem).getBeleg()
        self.mainwindow.belegKassieren(invoice)


    def toggleUeberweisung(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Beleg ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        widget = self.ui.listWidget_2.itemWidget(item)
        invoice = widget.getBeleg()
        invoice.setBanktransfer(not invoice.getBanktransfer())
        if invoice.getBanktransfer():
            invoice.setPayed(False)
        widget.update()
        self.speicher.speichereBeleg(invoice)
        self.belegAusgewaehlt(item)

    def toggleBio(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Beleg ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        widget = self.ui.listWidget_2.itemWidget(item)
        invoice = widget.getBeleg()
        if invoice.isBio():
            if QtWidgets.QMessageBox.warning(self, u'Kein BIO?', u'Diese Verarbeitung war doch kein BIO-Obst?.', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel) == QtWidgets.QMessageBox.Yes:
                invoice.setBio(False)
                self.speicher.speichereBeleg(invoice)
        else:
            reply = QtWidgets.QMessageBox.warning(self, u'BIO-Belege?', u'Bio-Beleg erstellen und drucken?\n\nJa = BIO-Beleg für diesen Vorgang drucken\nNein = Bio-Markierung setzen aber keinen Beleg drucken\nAbbrechen = War doch kein Bio', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return
            elif reply == QtWidgets.QMessageBox.No:
                invoice.setBio(True)
                self.speicher.speichereBeleg(invoice)
            elif reply == QtWidgets.QMessageBox.Yes:
                invoice.setBio(True)
                self.speicher.speichereBeleg(invoice)
                filename = BioBeleg(invoice, filename='BIO_%s.pdf' % invoice.getRechnungsnummer())
                print('Filename: %s' % filename)
                c = cups.Connection()
                c.printFile(c.getDefault(), filename, 'Bio-Beleg %s' % invoice.getRechnungsnummer(), PRINTER_OPTIONS)
        self.updateAlteBelege()

            


    def toggleBezahlt(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Beleg ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        widget = self.ui.listWidget_2.itemWidget(item)
        invoice = widget.getBeleg()
        if invoice.getPayed():
            # Stornobuchung
            zahlbetrag = 0.0
            for z in self.speicher.getZahlungen(invoice):
                zahlbetrag += z['betrag']
            if zahlbetrag > 0.0:
                self.speicher.speichereZahlung(invoice, 'bar', -zahlbetrag, 'Beleg auf "unbezahlt" gesetzt')
        invoice.setPayed(not invoice.getPayed())
        if invoice.getPayed():
            invoice.setBanktransfer(False)
        widget.update()
        self.speicher.speichereBeleg(invoice)
        self.belegAusgewaehlt(item)


    def reload(self):
        self.updateAlteBelege()
        

    def sortingChanged(self, newSortingIndex):
        if newSortingIndex == 0:
            self.__invoicelist_sorting = 'DateDesc'
        elif newSortingIndex == 1:
            self.__invoicelist_sorting = 'DateAsc'
        elif newSortingIndex == 2:
            self.__invoicelist_sorting = 'Name'
        elif newSortingIndex == 3:
            self.__invoicelist_sorting = 'Amount'
        self.updateAlteBelege()

    def belegDruckenThermo(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Beleg ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        if item:
            invoice = None
            if len(self.ui.listWidget_2.selectedItems()) > 1:
                invoice = Beleg()
                for selectedItem in self.ui.listWidget_2.selectedItems():
                    tmp = self.ui.listWidget_2.itemWidget(selectedItem).getBeleg()
                    invoice.belegHinzufuegen(tmp)
            else:
                invoice = self.ui.listWidget_2.itemWidget(item).getBeleg()

            if not BelegThermo(invoice, self.mainwindow.printer):
                QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)


    def rechnungStornieren(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Keine Rechnung ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        if len(self.ui.listWidget_2.selectedItems()) > 1:
            QtWidgets.QMessageBox.warning(self, u'Mehrere Belege ausgewählt', u'Rechnungen können nur einzeln storniert werden', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        beleg = self.ui.listWidget_2.itemWidget(item).getBeleg()
        if not beleg.isRechnung():
            QtWidgets.QMessageBox.warning(self, u'Dies ist keine Rechnung', u'Dieser Beleg repräsentiert keine Rechnung.', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        rechnungsnr = beleg.getRechnungsnummer()
        adresse = beleg.kunde.getAdresse()
        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(self, u'Rechnung Stornieren', u'Die Rechnung Nr.<br/><strong>%s</strong><br/>an<br />%s<br/>soll storniert werden. Ist das okay?' % (rechnungsnr, adresse), buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
            storniereRechnung(beleg)
        self.updateAlteBelege()

    
    def rechnungAusBeleg(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Keine Rechnung ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        originale = []
        beleg = None
        if len(self.ui.listWidget_2.selectedItems()) > 1:
            QtWidgets.QMessageBox.warning(self, u'Mehrere Belege ausgewählt', u'Die Posten der einzelnen Belege werden zusammengefasst', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            beleg = Beleg()
            for selectedItem in self.ui.listWidget_2.selectedItems():
                tmp = self.ui.listWidget_2.itemWidget(selectedItem).getBeleg()
                if tmp.isRechnung():
                    QtWidgets.QMessageBox.warning(self, u'Wiederholte Rechnung', u'Mindestens einer der beteiligten Belege wurde schon in eine Rechnung übernommen.', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                    return False
                originale.append(tmp)
                beleg.belegHinzufuegen(tmp)
        else: 
            beleg = self.ui.listWidget_2.itemWidget(item).getBeleg()
            originale.append(beleg)

        
        if beleg.isRechnung():
            filename = rechnungsPDFDatei(beleg)
            if filename is None:
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Rechnungsdatei ist kaputt!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                return False            
            if not os.path.exists(filename):
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Rechnungsdatei nicht gefunden!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                return False
            if 0 != subprocess.call(['/usr/bin/xdg-open', filename], shell=False, stderr=open('/dev/null', 'a')):
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Fehler beim Öffnen der PDF-Datei!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                return False
            return False

        if showRechnungDialog(beleg, originale):
            self.belegAusgewaehlt(item)
            self.updateAlteBelege()



    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()

        return False
