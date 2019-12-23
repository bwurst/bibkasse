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
import sys

from gui.phonenumber_listentry import TelefonnummerWidget

def showPhoneNumberInputDialog(kunde):
    dialog = PhoneNumberInputDialog(kunde)
    dialog.show()
    dialog.exec_()
    return kunde


class PhoneNumberInputDialog(QtWidgets.QDialog):
    def __init__(self, kunde):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/telefoninput.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.showFullScreen()

        self.kunde = kunde
        self.kontakte = self.kunde.listKontakte()

        if len(self.kontakte) == 0:
            self.kunde.addKontakt('telefon', '')

        self.currentWidget = None
        self.currentNumber = None
        self.buildList()
        self.connectSlots()
        self.ui.listWidget.setCurrentRow(0)

    def buildList(self):
        self.ui.listWidget.clear()
        self.ui.listWidget
        for i in range(len(self.kontakte)):
            k = self.kontakte[i]
            # Sortiere E-Mail aus
            if k['typ'] in ['telefon', 'mobil']:
                entry = TelefonnummerWidget(self, i, k['wert'])
                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(QtCore.QSize(0, 70))
                self.ui.listWidget.addItem(item)
                self.ui.listWidget.setItemWidget(item, entry)
            
    def listItemClicked(self, listItem):
        if not listItem:
            return
        for index in range(self.ui.listWidget.count()):
            widget = self.ui.listWidget.itemWidget(self.ui.listWidget.item(index))
            widget.loseFocus()
        widget = self.ui.listWidget.itemWidget(listItem)
        self.currentWidget = widget
        widget.getFocus()
                
    def numberPressed(self, digit):
        def func():
            self.currentWidget.numberPressed(digit)
        return func
    
   
    def ok(self):
        self.close()
    
    def abbrechen(self):
        # Wenn instant gespeichert wird, ist das sinnlos
        self.close()
        
    def clear(self):
        self.currentWidget.clear()
    
    def backspace(self):
        self.currentWidget.backspace()
        
    def more(self):
        self.kunde.addKontakt('telefon', '')
        self.buildList()
        newindex = self.ui.listWidget.count()-1
        self.ui.listWidget.setCurrentRow(newindex)
        
    def deleteNumber(self, index):
        del self.kontakte[index]
        self.buildList()
        lastindex = self.ui.listWidget.count()-1
        self.ui.listWidget.setCurrentRow(lastindex)

    def connectSlots(self):
        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_backspace.clicked.connect(self.backspace)
        self.ui.button_more.clicked.connect(self.more)
        self.ui.button_clear.clicked.connect(self.clear)
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen.clicked.connect(self.abbrechen)

        self.ui.listWidget.currentItemChanged.connect(self.listItemClicked)







if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    from lib.Kunde import Kunde
    k = Kunde()
    #k.addKontakt('telefon', '071923455')
    #k.addKontakt('telefon', '0152345679')
    showPhoneNumberInputDialog(k)

    print ('Telefon: »%s«' % k.listKontakte())


