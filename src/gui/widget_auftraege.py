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
import subprocess, os, sys, datetime
import cups

from gui.auftraege_listentry import AuftragWidget

from lib.Speicher import Speicher
from gui.kundenauswahl import showKundenAuswahlDialog
from gui.bioanlieferung import showBioAnlieferungDialog

from lib.AuftragHTML import AuftragHTML
from lib.AuftragThermo import AuftragThermo


PRINTER_OPTIONS = {'media': 'A4',
                   'copies': '1',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}


class WidgetAuftraege(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        self.ui = None
        try:
            self.ui = uic.loadUi('ressource/ui/widget_auftraege.ui', self.ui)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)
          
        self.year = datetime.date.today().year
        self.speicher = Speicher(self.year)

        self.__list_sorting = 'Name'

        self.__erledigte = False
        self.__showall = False
        self.filter_kunde = None


        self.ui.input_suche.clicked = self.sucheClicked
        self.ui.input_suche.installEventFilter(self)
        self.ui.listWidget_2.itemClicked.connect(self.listWidgetClick)
        self.ui.listWidget_2.currentItemChanged.connect(self.auftragAusgewaehlt)
        self.ui.listWidget_version.currentItemChanged.connect(self.versionAusgewaehlt)
        #self.ui.button_bearbeiten.clicked.connect(self.belegOeffnen)
        #self.ui.button_belegdrucken.clicked.connect(self.belegDruckenThermo)
        self.ui.button_bio.clicked.connect(self.toggleBio)
    
        self.ui.combo_year.currentIndexChanged.connect(self.updateAuftraege)
        self.ui.combo_sortierung.currentIndexChanged.connect(self.sortingChanged)
        self.ui.input_suche.textChanged.connect(self.updateAuftraege)
        self.ui.button_sucheLeeren.clicked.connect(self.clearSuche)

        self.ui.button_reload.clicked.connect(self.reload)

        self.ui.button_listedrucken.clicked.connect(self.listedrucken)
        self.ui.button_erledigte.clicked.connect(self.extended)
        

    def listWidgetClick(self, listWidgetItem = None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        self.auftragAusgewaehlt(listWidgetItem)

          

    def update(self):
        print('update()')
        current_year = str(datetime.date.today().year)
        years = sorted(list(self.speicher.list_years()))

        self.ui.combo_year.currentIndexChanged[int].disconnect(self.updateAuftraege)

        self.ui.combo_year.clear()
        for y in years:
            self.ui.combo_year.addItem(y)
        self.ui.combo_year.setCurrentIndex(self.ui.combo_year.findText(current_year))
        self.ui.combo_year.currentIndexChanged[int].connect(self.updateAuftraege)
        self.updateAuftraege()
        self.ui.button_erledigte.setChecked(self.__erledigte)
        if self.__erledigte:
            self.ui.button_listedrucken.setEnabled(False)
        else:
            self.ui.button_listedrucken.setEnabled(True)

    def clearSuche(self):
        self.filter_kunde = None
        self.ui.input_suche.clear()

    def sucheClicked(self):
        kunde = showKundenAuswahlDialog(neu=False)
        self.filter_kunde = kunde.ID()
        self.ui.input_suche.setText(kunde.getName())
        #self.ui.input_suche.setText( showTextInputDialog('Filter', [], self.ui.input_suche.text()))

    def updateAuftraege(self, foobar=None):
        self.year = str(self.ui.combo_year.currentText()).strip()
        if hasattr(self, 'speicher'):
            del self.speicher
        self.speicher = Speicher(self.year)
        self.ui.textBrowser.clear()
        self.__auftragsliste = []
        if self.filter_kunde:
            self.__auftragsliste = self.speicher.listAuftraegeByKunde(self.filter_kunde)
        elif not self.__erledigte:
            self.__auftragsliste = self.speicher.listOffeneAuftraege()
        if self.__showall and self.__erledigte and not self.filter_kunde:
            self.__showall = False
            if self.__list_sorting == 'DateDesc':
                self.__auftragsliste = self.speicher.listAuftraegeByDateDesc()
            elif self.__list_sorting == 'DateAsc':
                self.__auftragsliste = self.speicher.listAuftraegeByDateAsc()
            elif self.__list_sorting == 'Name':
                self.__auftragsliste = self.speicher.listAuftraegeByName()
            else:
                self.__auftragsliste = self.speicher.listAuftraege()

        if self.filter_kunde and not self.__auftragsliste:
            label = QtWidgets.QLabel("Keine Ergebnisse")
            self.ui.listWidget_2.clear()
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, label)
        elif not self.__auftragsliste and self.__erledigte:
            button_showall = QtWidgets.QPushButton("Alle Aufträge anzeigen")
            button_showall.clicked.connect(self.showall)
            self.ui.listWidget_2.clear()
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 100))
            self.ui.listWidget_2.addItem(item)
            self.ui.listWidget_2.setItemWidget(item, button_showall)
        else:
            self.ui.listWidget_2.clear()
            for auftrag in self.__auftragsliste:
                entry = AuftragWidget(auftrag)
                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(QtCore.QSize(self.ui.listWidget_2.size().width() - 40, 68))
                self.ui.listWidget_2.addItem(item)
                self.ui.listWidget_2.setItemWidget(item, entry)
        self.auftragAusgewaehlt()

    def showall(self):
        self.__showall = True
        self.updateAuftraege()

    def extended(self):
        self.__erledigte = not self.__erledigte


    def updateVersionen(self, handle):
        l = self.ui.listWidget_version
        l.clear()
        versionen = self.speicher.getAuftragVersionen(handle)
        versionsnummern = list(versionen.keys())
        versionsnummern.sort(reverse=True)
        newest = max(versionsnummern)
        select = None
        for version in versionsnummern:
            v = versionen[version]
            i = QtWidgets.QListWidgetItem(parent=l)
            i.setData(1, version)
            i.setText('Version %i, %s, %s, %s' % (version, v['quelle'], v['zeitpunkt'], v['status']))
            if version == newest:
                select = i
            l.addItem(i)
        l.setCurrentItem(select)
        


    def versionAusgewaehlt(self, listWidgetItem = None, nonsense = None):
        if not listWidgetItem:
            return None
        version = int(listWidgetItem.data(1))
        if version:
            auftrag = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0]).getAuftrag()
            handle = auftrag.ID
            auftrag = self.speicher.ladeAuftrag(handle, version=version)
            text = AuftragHTML(auftrag, public=False)
            self.ui.textBrowser.setHtml(text)
        


    def auftragAusgewaehlt(self, listWidgetItem = None, nonsense = None):
        print('AuftragAusgewaehlt')
        auftrag = None
        if len(self.ui.listWidget_2.selectedItems()) > 0:
            widget = self.ui.listWidget_2.itemWidget(self.ui.listWidget_2.selectedItems()[0])
            if type(widget) == AuftragWidget:
                auftrag = self.speicher.ladeAuftrag(widget.getAuftrag().ID)
                self.ui.label_dateiname.setText('%s' % auftrag.ID)

        if auftrag:
            self.ui.button_drucken.setEnabled(True)

            self.ui.button_loeschen.setEnabled(True)
            #self.ui.button_bearbeiten.setEnabled(True)
            self.ui.button_bio.setEnabled(False)
            self.ui.button_bio.setChecked(False)
            

            text = AuftragHTML(auftrag, public=False)
            self.ui.textBrowser.setHtml(text)
            self.updateVersionen(auftrag.ID)


            if self.year != str(datetime.date.today().year):
                self.ui.button_loeschen.setEnabled(False)
                #self.ui.button_bearbeiten.setEnabled(False)
        else:
            # Kein Auftrag ausgewählt
            self.ui.textBrowser.clear()
            self.ui.listWidget_version.clear()
            self.ui.button_bio.setEnabled(False)
            self.ui.button_loeschen.setEnabled(False)
            #self.ui.button_bearbeiten.setEnabled(False)
            self.ui.button_drucken.setEnabled(False)
            self.ui.label_dateiname.setText(u'<em>Kein Auftrag ausgewählt</em>') 


    def auftragAusfuehren(self, listWidgetItem=None):
        if not listWidgetItem:
            listWidgetItem = self.ui.listWidget_2.currentItem()
        auftrag = self.ui.listWidget_2.itemWidget(listWidgetItem).getAuftrag()
        self.mainwindow.auftragAusfuehren(auftrag)
            

    def toggleBio(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Beleg ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        widget = self.ui.listWidget_2.itemWidget(item)
        auftrag = widget.getAuftrag()
        if auftrag.bio:
            if QtWidgets.QMessageBox.warning(self, u'Kein BIO?', u'Dieser Auftrag ist doch kein BIO-Obst?.', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel) == QtWidgets.QMessageBox.Yes:
                auftrag.bio = False
                self.speicher.speichereAuftrag(auftrag)
        else:
            reply = QtWidgets.QMessageBox.warning(self, u'BIO-Lieferschein?', u'Bio-Lieferschein erstellen und drucken?\n\nJa = BIO-Beleg für diesen Vorgang drucken\nNein = Bio-Markierung setzen aber keinen Beleg drucken\nAbbrechen = War doch kein Bio', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, defaultButton=QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return
            elif reply == QtWidgets.QMessageBox.No:
                auftrag.bio = True
                self.speicher.speichereAuftrag(auftrag)
            elif reply == QtWidgets.QMessageBox.Yes:
                showBioAnlieferungDialog(auftrag.kunde)
        self.updateAuftraege()

            

    def reload(self):
        self.updateAuftraege()
        

    def sortingChanged(self, newSortingIndex):
        if newSortingIndex == 0:
            self.__list_sorting = 'DateDesc'
        elif newSortingIndex == 1:
            self.__list_sorting = 'DateAsc'
        elif newSortingIndex == 2:
            self.__list_sorting = 'Name'
        self.updateAuftraege()

    def aktuellenAuftragLoeschen(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Auftrag ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        auftrag = self.ui.listWidget_2.itemWidget(item).getAuftrag()

        if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(self, u'Löschen', u'Auftrag wirklich löschen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
            if not self.speicher.loescheAuftrag(auftrag):
                print ('FEHLER beim Löschen')
            self.updateAuftraege()

    def listedrucken(self):
        pass
        # FIXME


    def auftragDruckenThermo(self):
        item = self.ui.listWidget_2.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Auftrag ausgewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return False

        if item:
            auftrag = self.ui.listWidget_2.itemWidget(item).getAuftrag()
            if not AuftragThermo(auftrag, self.mainwindow.printer):
                QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)




    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()

        return False
