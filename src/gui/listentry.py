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

from PyQt5 import QtCore, QtWidgets, QtGui, uic
import sys
from gui.invoiceentry import showInvoiceEntryDialog
from gui.numberinput import showNumberInputDialog

try:
    (ui_class, ui_base) = uic.loadUiType('ressource/ui/listentry.ui')
except:
    print ('Kann UI-Datei nicht laden!')
    sys.exit(1)

edit_icon = QtGui.QIcon('ressource/icons/pencil.png')
delete_icon = QtGui.QIcon('ressource/icons/cancel.png')

class ListEntry(QtWidgets.QFrame):
    itemChanged = QtCore.pyqtSignal()
    
    def __init__(self, parent, invoiceEntry):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QFrame.__init__(self)
        self.parent = parent

        self.ui = ui_class()
        self.ui.setupUi(self)

        self.ui.input_anzahl.installEventFilter(self)
        self.installEventFilter(self)
        self.__invoiceEntry = invoiceEntry
        self.numberinput_altestueckzahl = 0
        self.update()
        self.textChanged = False
        self.ui.button_loeschen.setIcon(delete_icon)
        self.ui.button_loeschen.clicked.connect(self.delete)
        self.ui.input_anzahl.textChanged.connect(self.anzahlAuslesen)

    def anzahlAuslesen(self, qstring):
        self.textChanged = True

    def lineEditClicked(self):
        showNumberInputDialog(self.__invoiceEntry)
        self.update()

    def update(self):
        e = self.__invoiceEntry
        if round(e['anzahl'], 2) == round(e['anzahl'], 0):
            self.ui.input_anzahl.setText(u'%i' % int(e['anzahl']))
        else:
            self.ui.input_anzahl.setText(u'%.2f' % e['anzahl'])
        self.ui.einheit.setText(e['einheit'])
        if e.preislistenID and e.preisliste_link:
            self.ui.beschreibung.setText(e['beschreibung'])
        else:
            self.ui.beschreibung.setText(str(e['beschreibung'])+'<sup style="color: red;">*</sup>')
        self.ui.einzelpreis.setText(u'je %.2f €' % e['einzelpreis'])
        self.ui.gesamtpreis.setText(u'%.2f €' % e['gesamtpreis']) 
        self.itemChanged.emit()


    def delete(self):
        self.__invoiceEntry.unregister()
        self.itemChanged.emit()


    def edit(self):
        showInvoiceEntryDialog(self.__invoiceEntry)
        self.update()
        

    def eventFilter(self, qobject, qevent):
        if qobject == self:
            if qevent.type() == QtCore.QEvent.MouseButtonDblClick:
                self.edit()
        else:
            if qevent.type() == QtCore.QEvent.MouseButtonPress:
                self.lineEditClicked()
            if qevent.type() == QtCore.QEvent.FocusOut and self.textChanged:
                qstring = self.ui.input_anzahl.text()
                self.__invoiceEntry.setStueckzahl( int(qstring) )
                self.update()
                self.textChanged = False

        return False


