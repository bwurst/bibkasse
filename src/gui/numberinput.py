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

def showNumberInputDialog(invoiceEntry, gebrauchte = False, icon=None, text=None):
    numberdialog = NumberInputDialog(invoiceEntry, gebrauchte=gebrauchte, icon=icon, text=text)
    numberdialog.show()
    numberdialog.exec_()
    return numberdialog.getAnzahl()


class NumberInputDialog(QtWidgets.QDialog):
    def __init__(self, invoiceEntry, gebrauchte = False, icon=None, text=None):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/numberinput.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.showFullScreen()

        if (icon and text):
            self.ui.button_aktuellesprodukt.setIcon(icon)
            self.ui.button_aktuellesprodukt.setText(text)
        else:
            self.ui.button_aktuellesprodukt.hide()
        self.invoiceEntry = invoiceEntry
        self.gebrauchte = gebrauchte
        self.__alte_anzahl = invoiceEntry['anzahl']
        self.ui.button_alle.setText('Alle (%i)' % invoiceEntry['anzahl'])
        self.ui.frame_gebrauchte.setVisible(self.gebrauchte)
        self.ui.button_abbrechen.setVisible(not self.gebrauchte)

        self.start_einzelpreis = invoiceEntry['anzahl']
        self.ui.label_kopfzeile.setText(invoiceEntry['beschreibung'])
        self.ui.input_anzahl.setValidator(QtGui.QIntValidator())
        if self.gebrauchte:
            self.ui.input_anzahl.clear()
        else:
            self.ui.input_anzahl.setText('%i' % invoiceEntry['anzahl'])
        self.ui.input_anzahl.setFocus()
        self.ui.input_anzahl.selectAll()
        self.updateEinzelpreis(self.ui.input_anzahl.text())
        self.connectSlots()


    def numberPressed(self, number):
        return lambda : self.ui.input_anzahl.insert(number)

    def updateEinzelpreis(self, text):
        try:
            anzahl = int(text)
        except:
            anzahl = 0
            pass
        self.invoiceEntry.setStueckzahl(anzahl)
        self.ui.label_einzelpreis.setText( (u'%.2f €' % self.invoiceEntry['einzelpreis']).replace('.', ',') )
        self.ui.label_gesamtpreis.setText( (u'%.2f €' % self.invoiceEntry['gesamtpreis']).replace('.', ',') )
    
    
    def getAnzahl(self):
        return self.invoiceEntry['anzahl']
    
    def ok(self):
        self.updateEinzelpreis(self.ui.input_anzahl.text())
        self.close()
    
    def abbrechen(self):
        self.invoiceEntry.setStueckzahl(self.__alte_anzahl)
        self.close()

    def keine(self):
        self.invoiceEntry.setStueckzahl(0)
        self.close()
    
    def alle(self):
        self.invoiceEntry.setStueckzahl(self.__alte_anzahl)
        self.close()

    def connectSlots(self):
        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_delete.clicked.connect(self.ui.input_anzahl.backspace)
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen.clicked.connect(self.abbrechen)
        self.ui.input_anzahl.textChanged.connect(self.updateEinzelpreis)
        self.ui.button_keine.clicked.connect(self.keine)
        self.ui.button_alle.clicked.connect(self.alle)







if __name__ == "__main__":
    def preiskalkulator(stueck):
        if stueck > 10:
            return 2.4
        else:
            return 2.6



    app = QtWidgets.QApplication(sys.argv)
    anzahl = 0
    try:
        anzahl = int(sys.argv[1])
    except:
        pass
  
    numberdialog = NumberInputDialog('Zahleneingabe', preiskalkulator, anzahl)
    numberdialog.show()
    ret = numberdialog.exec_()

    print ('Es wurde "%i" eingegeben!' % numberdialog.anzahl)
    print ('Exit-Code: %i' % ret)

    sys.exit(ret)

