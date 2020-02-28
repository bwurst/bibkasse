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
import datetime, sys

from gui.listentry import ListEntry
from gui.numberinput import showNumberInputDialog
from gui.valueinput import showValueInputDialog
from gui.textinput import showTextInputDialog
from gui.kundenauswahl import showKundenAuswahlDialog
from gui.kundendaten import showKundendatenDialog
from gui.speicherndialog import SpeichernDialog

from lib.Vorgang import Vorgang
from lib.Preisliste import Preisliste
from lib.Speicher import Speicher
from lib.BelegThermo import VorgangThermo, RegalschildThermo
from lib.SMS import send_sms

PRINTER_OPTIONS = {'media': 'A5',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}

  


class WidgetAbfuellung(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_abfuellung.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.speicher = Speicher()


        self.pl = Preisliste()
        self.rabattStufen = [i[1] for i in self.pl.rabattStufen('5er')]

        while self.ui.combo_manuelleLiter.count() > 0:
            self.ui.combo_manuelleLiter.removeItem(0)
        for liter in self.rabattStufen:
            self.ui.combo_manuelleLiter.addItem('%s' % liter)
    
        self.connectSlots()

        self.stylesheetInputHighlighted = 'background-color: #faa; font-style: italic; border: 1px solid black;'
        self.stylesheetInputRegular = 'border: 1px solid black; background-color: white;'
        
        #for widget in self.ui.stackedWidget.findChildren(QtWidgets.QToolButton):
        #    widget.setStyleSheet('border: 1px solid black;\nbackground-color: white;')
        
        self.ui.stackedWidget.widget(0).setStyleSheet('background-color: #96ff96;')
        self.ui.stackedWidget.widget(1).setStyleSheet('background-color: #ffffff;')
        self.ui.stackedWidget.widget(2).setStyleSheet('background-color: #9696ff;')
        self.ui.stackedWidget.widget(3).setStyleSheet('background-color: #ff9696;')
        
        self.alte_kundenvorgaenge = None
        self.liter_alte_abfuellungen = 0
        self.rabattstufe_berechnen = True
        self.modus = 'speichern'
        self.neuerVorgang()


    def closeEvent(self, closeEvent):
        if self.vorgang.changed:
            if QtWidgets.QMessageBox.No == QtWidgets.QMessageBox.question(self, u'Änderungen verwerfen', u'Die aktuell geöffnete Abfüllung wurde noch nicht gespeichert. Trotzdem beenden?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
                closeEvent.ignore()

    
    def updateVorgang(self):
        if self.alte_kundenvorgaenge and self.rabattstufe_berechnen:
            liter_gesamt = self.liter_alte_abfuellungen + self.vorgang.getLiterzahl()
            stufe = 0
            for s in self.rabattStufen:
                if liter_gesamt+self.pl.TOLERANZ >= s:
                    stufe = s
            if stufe != self.vorgang.getManuelleLiterzahl():
                self.vorgang.setManuelleLiterzahl(stufe)
                self.update()
                

        self.ui.listWidget.clear()
        for entry in self.vorgang.getEntries():
            entry = ListEntry(self, entry)
            entry.itemChanged.connect(self.itemChanged)
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(self.ui.listWidget.size().width() - 2, 60))
            self.ui.listWidget.addItem(item)
            self.ui.listWidget.setItemWidget(item, entry)
        self.ui.listWidget.scrollToBottom()
        self.ui.label_gesamtpreis.setText(u'%.2f €' % self.vorgang.getSumme())
        self.ui.label_literzahl.setText(u'%i Liter' % self.vorgang.getLiterzahl())

    def isShown(self):
        self.rabattstufe_berechnen = True
        if not self.vorgang.kunde and self.modus == 'speichern':
            self.showKundenAuswahlDialog()
    
    def update(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.listWidget_kundenhinweise.clear()
        if self.vorgang.kunde.ID():
            self.alte_kundenvorgaenge = self.speicher.listVorgaengeByKunde(self.vorgang.kunde.ID())
            if self.alte_kundenvorgaenge:
                self.liter_alte_abfuellungen = 0
                for b in self.alte_kundenvorgaenge:
                    if b.ID == self.vorgang.ID:
                        continue
                    self.liter_alte_abfuellungen += b.getLiterzahl()
                    hinweis = u'Abfüllung am %s: %s Liter' % (b.getZeitpunkt(), b.getLiterzahl())
                    self.ui.listWidget_kundenhinweise.addItem(hinweis)
                self.ui.listWidget_kundenhinweise.addItem(u'Vorherige Abfüllungen dieses Jahr insgesamt: %s Liter' % (self.liter_alte_abfuellungen,))
        if self.vorgang.getKundenname() == '' and self.modus == 'speichern':
            self.ui.input_kundenname.setMinimumHeight(200)
            self.ui.input_kundenname.setStyleSheet(self.stylesheetInputHighlighted)
            self.ui.input_kundenname.setText(u'Hier Kunde wählen')
        else:
            self.ui.input_kundenname.setMinimumHeight(0)
            self.ui.input_kundenname.setStyleSheet(self.stylesheetInputRegular)
            self.ui.input_kundenname.setText(self.vorgang.getKundenname().replace('&', '&&'))
        if self.vorgang.getManuelleLiterzahl():
            state_checkbox = self.ui.checkBox_manuelleLiter.blockSignals(True)
            state_combo = self.ui.combo_manuelleLiter.blockSignals(True)
            self.ui.checkBox_manuelleLiter.setChecked(True)
            self.ui.combo_manuelleLiter.setEnabled(True)
            self.ui.checkBox_manuelleLiter.setStyleSheet('color: #f00;')
            index = self.ui.combo_manuelleLiter.findText(str(self.vorgang.getManuelleLiterzahl()))
            self.ui.combo_manuelleLiter.setCurrentIndex(index)
            self.ui.checkBox_manuelleLiter.blockSignals(state_checkbox)
            self.ui.combo_manuelleLiter.blockSignals(state_combo)
        else:
            self.ui.checkBox_manuelleLiter.setChecked(False)
            self.ui.checkBox_manuelleLiter.setStyleSheet('color: #000;')
            self.ui.combo_manuelleLiter.setEnabled(False)
            self.ui.combo_manuelleLiter.setCurrentIndex(self.ui.combo_manuelleLiter.count()-1)
        self.updateVorgang()
    
    
    def itemChanged(self):
        self.updateVorgang()
    
    
    def removeListEntryCallback(self):
        return lambda : self.ui.tableWidget.removeRow(self.ui.tableWidget.currentRow())
    

    def newDoubleEntry(self, id1, id2, default2 = None):
        def function():
            handle = self.vorgang.newItem(0, id1)
            entry = self.vorgang.getEntry(handle)
            icon = None
            text = None
            try:
                button = getattr(self.ui, 'button_%s' % id1)
                icon = button.icon()
                text = button.text()
            except:
                print ('Keinen button gefunden für %s' % id1)
                pass
            if not showNumberInputDialog(entry, icon=icon, text=text) or entry['anzahl'] == 0:
                self.vorgang.deleteItem(handle)
            else:
                self.updateVorgang()
                anz = entry['anzahl']
                if default2 != None:
                    anz = default2
                handle = self.vorgang.newItem(anz, id2)
                entry = self.vorgang.getEntry(handle)
                if not showNumberInputDialog(entry, gebrauchte = True, icon=icon, text=text) or entry['anzahl'] == 0:
                    self.vorgang.deleteItem(handle)
            self.updateVorgang()
        return function
    
    
    def newEntryCallback(self, preislistenID):
        def showDialog():
            handle = self.vorgang.newItem(0, preislistenID)
            entry = self.vorgang.getEntry(handle)
            icon = None
            text = None
            try:
                button = getattr(self.ui, 'button_%s' % preislistenID)
                icon = button.icon()
                text = button.text()
            except:
                print ('Keinen button gefunden für %s' % preislistenID)
                pass
            if not showNumberInputDialog(entry, gebrauchte = False, icon=icon, text=text) or entry['anzahl'] == 0:
                self.vorgang.deleteItem(handle)
            self.updateVorgang()
    
        def insertSingleItem():
            found = False
            for entry in self.vorgang.getEntries():
                if entry.preislistenID == preislistenID:
                    entry.setStueckzahl(entry.getStueckzahl() + 1)
                    found = True
                    break 
            if not found: 
                self.vorgang.newItem(1, preislistenID)
            self.updateVorgang()
    
        if preislistenID in ['frischsaft', 'frischsaft_q', 'saft_offen', '3er', '3er_q', 'ohnepressen']:
            return showDialog
        else:
            return insertSingleItem
    

    def newFreeEntry(self, initvalue = 0.0):
        handle = self.vorgang.newItem(1)
        entry = self.vorgang.getEntry(handle)
        entry.setEinheit('')
        entry.setSteuersatz(19.0)
        entry.setBeschreibung(showTextInputDialog('Beschreibung', ['Gutschein', 'Mosten', 'Kleinteile', 'Obstankauf', 'Sonstiges', 'Zeitschriften', 'Mindermengenzuschlag', 'Anzahlung'], ''))
        if entry.getBeschreibung() == '':
            del entry
            self.vorgang.deleteItem(handle)
            return
        entry.setPreis(initvalue)
        showValueInputDialog(entry)
        if entry.getSumme() == 0:
            del entry
            self.vorgang.deleteItem(handle)
        self.update()
    
    def newBetragEntry(self):
        # Positiver Betrag
        self.newFreeEntry(0.0)
    
    def newAbzugEntry(self):
        # Negativer Betrag
        self.newFreeEntry(-0.0)
    
    
    def showKundenAuswahlDialog(self):
        self.vorgang.setKunde(showKundenAuswahlDialog(self.vorgang.getKunde()))
        self.update()
    
    def editKundendaten(self):
        self.vorgang.kunde = showKundendatenDialog(self.vorgang.kunde)
        self.speicher.speichereKunde(self.vorgang.kunde)
        self.update()
    
    def setzeManuellePreiskategorie(self, nonsense=None):
        liter = None
        if self.ui.checkBox_manuelleLiter.isChecked():
            self.rabattstufe_berechnen = False
            try:
                liter = int(self.ui.combo_manuelleLiter.currentText())
            except ValueError:
                liter = None
        else:
            self.rabattstufe_berechnen = False
        self.vorgang.setManuelleLiterzahl(liter)
        self.update()
    
    
    
    
    def plausibilitaetsCheck(self):
        errors = []
        _10er = 0
        _5er = 0
        _3er = 0
        _3er_gebraucht = 0
        _5er_gebraucht = 0
        _10er_gebraucht = 0
        for item in self.vorgang.getEntries():
            if item.preislistenID == '3er_gebraucht':
                _3er_gebraucht += item['anzahl']
            elif item.preislistenID == '5er_gebraucht':
                _5er_gebraucht += item['anzahl']
            elif item.preislistenID == '10er_gebraucht':
                _10er_gebraucht += item['anzahl']
            elif item.preislistenID and '3er' in item.preislistenID:
                _3er += item['anzahl']
            elif item.preislistenID and '5er' in item.preislistenID:
                _5er += item['anzahl']
            elif item.preislistenID and '10er' in item.preislistenID:
                _10er += item['anzahl']
        if _3er_gebraucht > _3er:
            errors.append(u'Mehr gebrauchte 3er-Kartons als insgesamt abgefüllt wurden!')
        if _5er_gebraucht > _5er:
            errors.append(u'Mehr gebrauchte 5er-Kartons als insgesamt abgefüllt wurden!')
        if _10er_gebraucht > _10er:
            errors.append(u'Mehr gebrauchte 10er-Kartons als insgesamt abgefüllt wurden!')
    
        if self.vorgang.getSumme() < 0.0:
            errors.append(u'Betrag ist Negativ, es wird eine Gutschrift erstellt!')
        if self.vorgang.getSumme() == 0.0:
            errors.append(u'Betrag ist 0!')
        return errors
    
    def speichern(self):
        self.speicher.speichereVorgang(self.vorgang)
    
    def regalschilder_drucken(self):
        for i in range(self.vorgang.getPaletten()):
            if not RegalschildThermo(self.vorgang, self.mainwindow.printer):
                QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                break
    
    def beleg_drucken(self):
        if not VorgangThermo(self.vorgang, self.mainwindow.printer):
            QtWidgets.QMessageBox.warning(self, u'Fehler beim Drucken', 'Drucker nicht angeschlossen, nicht eingeschaltet oder Rechte falsch?', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
        #pdfdata = BelegA5(self.vorgang)
        #t = tempfile.NamedTemporaryFile(delete=False)
        #t.write(pdfdata)
        #t.close()
        #c = cups.Connection()
        #c.printFile(c.getDefault(), t.name, 'Vorgang %s' % self.vorgang.getKundenname(), PRINTER_OPTIONS)
        #subprocess.call(['/usr/bin/xdg-open', t.name], shell=False)
        # xdg-open beendet sich sofort!
        #os.unlink(t.name)
    
    def speichereVorgang(self):
        fehler = self.plausibilitaetsCheck()
        for f in fehler:
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Möglicher Fehler', f + '\nIst das korrekt?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                return False
        dialog = SpeichernDialog(self.vorgang)
        dialog.show()
        dialog.exec_()
        if dialog.result() == 1:
            # OK gedrückt!
            if not dialog.speicherungErsetzen():
                self.vorgang.setID(None)
                self.vorgang.setZeitpunkt(datetime.datetime.now())
            self.speichern()
            if dialog.isBio:
                l = dialog.gewaehlterBioLieferschein()
                if l and not l['produktionsdatum']:
                    l['produktionsdatum'] = datetime.date.today()
                    self.speicher.speichereBioLieferschein(l)
            drucken = dialog.belegDrucken()
            if drucken:
                self.regalschilder_drucken()
            anrufe = self.speicher.getAnrufe(self.vorgang)
            if not anrufe and not dialog.kunde_nimmt_mit:
                telefon = self.vorgang.getTelefon()
                if telefon:
                    for num in telefon.split(' / '):
                        if num.startswith('+491') or num.startswith('01'):
                            if (QtWidgets.QMessageBox.Yes == 
                                QtWidgets.QMessageBox.question(self, u'SMS senden?', u'Soll eine SMS an die Handynummer\n%s\ngesendet werden?' % num, buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)):
                                try:
                                    send_sms(self.vorgang)
                                except RuntimeError as e:
                                    QtWidgets.QMessageBox.warning(self, u'Fehler', str(e.args))
                                except ValueError as e:
                                    QtWidgets.QMessageBox.warning(self, u'Fehler', str(e.args))
                                else:
                                    self.speicher.speichereAnruf(self.vorgang, 'sms', '')
                            break
                    
            self.neuerVorgang()
            self.mainwindow.reset()
        self.update()
    
    def kassieren(self):
        fehler = self.plausibilitaetsCheck()
        for f in fehler:
            if (QtWidgets.QMessageBox.No ==
                QtWidgets.QMessageBox.warning(self, u'Möglicher Fehler', f + '\nIst das korrekt?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                return False
        self.speichern()
        self.mainwindow.vorgangKassieren(self.vorgang)
        
    
    def neuerVorgang(self):
        self.vorgang = Vorgang()
        self.alte_kundenvorgaenge = None
        self.liter_alte_abfuellungen = 0
        self.rabattstufe_berechnen = True
        self.modusSpeichern()
        self.update()
    
    def vorgangOeffnen(self, vorgang, kassiervorgang=False):
        self.vorgang = self.speicher.getVorgang(vorgang.ID)
        self.modusKassieren(kassiervorgang=kassiervorgang)
        self.update()
        return True
    

    def modusDirektverkauf(self):
        self.modus = 'kassieren'

        self.ui.button_speichern.setVisible(False)

        self.ui.button_kassieren.setVisible(True)
        self.ui.button_kassieren.setStyleSheet('background-color: #0f0; color: #000; border: 1px solid black;')
        self.ui.button_kassieren.setMinimumHeight(100)
        self.ui.button_kassieren.setText(u'Kassieren')

    
    def modusKassieren(self, kassiervorgang):
        self.modus = 'kassieren'

        if kassiervorgang:
            self.ui.button_speichern.setVisible(False)
        else:
            self.ui.button_speichern.setVisible(True)
            self.ui.button_speichern.setText(u'Nur Änderungen\nSpeichern')
            self.ui.button_speichern.setStyleSheet('border: 1px solid black; background-color: white;')
            self.ui.button_speichern.setMinimumHeight(100)

        self.ui.button_kassieren.setVisible(True)
        self.ui.button_kassieren.setText(u'Kassieren')
        self.ui.button_kassieren.setStyleSheet('background-color: #0f0; color: #000; border: 1px solid black;')
        self.ui.button_kassieren.setMinimumHeight(100)

    
    def modusSpeichern(self):
        self.modus = 'speichern'

        self.ui.button_speichern.setVisible(True)
        self.ui.button_speichern.setStyleSheet('background-color: #0f0; color: #000; border: 1px solid black;')
        self.ui.button_speichern.setMinimumHeight(100)
        self.ui.button_speichern.setText(u'Speichern')

        self.ui.button_kassieren.setVisible(False)
    
    
    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False
    
    
    def abbrechen(self):
        if self.vorgang.changed:
            if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(self, u'Alles Löschen', u'Wirklich alle Änderungen verwerfen und von vorne anfangen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
                if self.vorgang.ID:
                    self.speicher.ladeVorgang(self.vorgang.ID)
                self.neuerVorgang()
                return True
        else:
            self.neuerVorgang()
            return True
        # Wenn die Frage von oben mit Nein beantwortet wurde
        return False

    def itemClicked(self, listItem):
        self.ui.listWidget.itemWidget(listItem).edit()
            
    
    def connectSlots(self):
        self.ui.label_kundenname.clicked = self.showKundenAuswahlDialog
        self.ui.label_kundenname.installEventFilter(self)
        self.ui.input_kundenname.clicked = self.showKundenAuswahlDialog
        self.ui.input_kundenname.installEventFilter(self)

        self.ui.button_kundendaten.clicked.connect(self.editKundendaten)
        
        self.ui.button_3er.clicked.connect(self.newEntryCallback('3er'))
        self.ui.button_5er.clicked.connect(self.newDoubleEntry('5er', '5er_gebraucht'))
        self.ui.button_10er.clicked.connect(self.newDoubleEntry('10er', '10er_gebraucht'))
        self.ui.button_frischsaft.clicked.connect(self.newEntryCallback('frischsaft'))
        self.ui.button_3er_q.clicked.connect(self.newEntryCallback('3er_q'))
        self.ui.button_5er_q.clicked.connect(self.newDoubleEntry('5er_q', '5er_gebraucht'))
        self.ui.button_10er_q.clicked.connect(self.newDoubleEntry('10er_q', '10er_gebraucht'))
        self.ui.button_frischsaft_q.clicked.connect(self.newEntryCallback('frischsaft_q'))
        self.ui.button_holzstaender_klassisch.clicked.connect(self.newEntryCallback('holzstaender_klassisch'))
        self.ui.button_holzstaender_5er_ablage.clicked.connect(self.newEntryCallback('holzstaender_eh_5er_ablage'))
        self.ui.button_holzstaender_5er_ohne.clicked.connect(self.newEntryCallback('holzstaender_eh_5er_ohne'))
        self.ui.button_holzstaender_10er.clicked.connect(self.newEntryCallback('holzstaender_eh_10er'))
        self.ui.button_unsersaft_5er.clicked.connect(self.newDoubleEntry('5er_abfuellung_vk', '5er_gebraucht'))
        self.ui.button_unsersaft_10er.clicked.connect(self.newDoubleEntry('10er_abfuellung_vk', '10er_gebraucht'))
        
        self.ui.button_vk_quittensaft_3er.clicked.connect(self.newEntryCallback('quitte_3er_vk'))
        self.ui.button_vk_quittensaft_5er.clicked.connect(self.newEntryCallback('quitte_5er_vk'))
        
        self.ui.button_vk5er.clicked.connect(self.newEntryCallback('5er_vk'))
        self.ui.button_vk10er.clicked.connect(self.newEntryCallback('10er_vk'))
        self.ui.button_vkbirnen.clicked.connect(self.newEntryCallback('birnen_5er_vk'))
        self.ui.button_vkbirnen_3er.clicked.connect(self.newEntryCallback('birnen_3er_vk'))
        self.ui.button_vkmost5er.clicked.connect(self.newEntryCallback('most_5er_vk'))
        self.ui.button_vkmost10er.clicked.connect(self.newEntryCallback('most_10er_vk'))
        self.ui.button_5lkanister.clicked.connect(self.newEntryCallback('kanister_5l'))
        self.ui.button_saft_offen.clicked.connect(self.newEntryCallback('saft_offen'))
        
        self.ui.button_obstler_025.clicked.connect(self.newEntryCallback('obstler_025'))
        self.ui.button_obstler_050.clicked.connect(self.newEntryCallback('obstler_050'))
        self.ui.button_obstler_100.clicked.connect(self.newEntryCallback('obstler_100'))
        
        self.ui.button_gelee_apfel.clicked.connect(self.newEntryCallback('gelee_apfel'))
        self.ui.button_gelee_apfel_zimt.clicked.connect(self.newEntryCallback('gelee_apfel_zimt'))
        self.ui.button_gelee_apfel_rum.clicked.connect(self.newEntryCallback('gelee_apfel_rum'))
        self.ui.button_gelee_quitten.clicked.connect(self.newEntryCallback('gelee_quitten'))

        
        self.ui.button_3er_gebraucht.clicked.connect(self.newEntryCallback('3er_gebraucht'))
        self.ui.button_5er_gebraucht.clicked.connect(self.newEntryCallback('5er_gebraucht'))
        self.ui.button_10er_gebraucht.clicked.connect(self.newEntryCallback('10er_gebraucht'))
        self.ui.button_ohnepressen.clicked.connect(self.newEntryCallback('ohnepressen'))
        self.ui.button_betrag.clicked.connect(self.newBetragEntry)
        self.ui.button_abzug.clicked.connect(self.newAbzugEntry)          
        
        self.ui.button_speichern.clicked.connect(self.speichereVorgang)
        self.ui.button_kassieren.clicked.connect(self.kassieren)
        
        self.ui.checkBox_manuelleLiter.toggled.connect(self.setzeManuellePreiskategorie)
        self.ui.checkBox_manuelleLiter.toggled.connect(self.ui.combo_manuelleLiter.setEnabled)
        self.ui.combo_manuelleLiter.currentIndexChanged.connect(self.setzeManuellePreiskategorie)

        self.ui.listWidget.itemClicked.connect(self.itemClicked)

        self.ui.button_section_abfuellung.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.button_section_verkauf_saft.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.button_section_verkauf_sonstiges.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))
        self.ui.button_section_besonderes.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))
    
        
    
    

