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


def showValueInputDialog(invoiceEntry = None, beschreibung = None):
        valuedialog = ValueInputDialog(invoiceEntry, beschreibung)
        valuedialog.show()
        valuedialog.exec_()
        return valuedialog.getEinzelpreis()


class ValueInputDialog(QtWidgets.QDialog):
    def __init__(self, invoiceEntry = None, beschreibung = None):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/valueinput.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.showFullScreen()

        self.invoiceEntry = invoiceEntry
        self.ui.label_kopfzeile.setText(beschreibung)
        self.ui.input_einzelpreis.setText('0.0')
        if self.invoiceEntry:
            self.start_einzelpreis = invoiceEntry.getPreis()
            self.ui.label_anzahl.setText('%i' % self.invoiceEntry['anzahl'])
            self.ui.label_kopfzeile.setText(invoiceEntry.getBeschreibung())
            self.ui.input_einzelpreis.setText('%.2f' % invoiceEntry['einzelpreis'])
        else:
            self.ui.label_gesamtpreis.hide()

        if str(self.ui.input_einzelpreis.text()).startswith('-'):
            # Bei negativen Werten sollte das Minus nicht mitselektiert werden
            self.ui.input_einzelpreis.setSelection(1,len(self.ui.input_einzelpreis.text()))
        else:
            self.ui.input_einzelpreis.selectAll()
        self.updateEinzelpreis(self.ui.input_einzelpreis.text())
        self.ui.input_einzelpreis.setValidator(QtGui.QDoubleValidator())
        self.connectSlots()

    def numberPressed(self, number):
        def action():
            self.ui.input_einzelpreis.insert(number)
            self.updateEinzelpreis()
        return action

    def negateValue(self):
        text = self.ui.input_einzelpreis.text()
        if len(text) > 0 and text[0] == '-':
            # Minus vorhanden
            self.ui.input_einzelpreis.setText( text[1:] )
        else:
            # kein Minus vorhanden
            self.ui.input_einzelpreis.setText( u'-' + text )


    def updateEinzelpreis(self, param=None):
        if not param:
            param = self.ui.input_einzelpreis.text()
        self.preis = 0.0
        if type(param) == str:
            try:
                self.preis = float(str(param).replace(',', '.'))
            except:
                print('illegal string: %s' % param)
                pass
        elif type(param) == float:
            self.preis = param
        else:
            raise ValueError('Illegal parameter %s of type %s' % (param, type(param)))
        if self.invoiceEntry:
            self.invoiceEntry.setPreis(self.preis)
            self.ui.label_gesamtpreis.setText((u'%.2f €' % self.invoiceEntry['gesamtpreis']).replace('.', ','))



    def getEinzelpreis(self):
        if self.invoiceEntry:
            return self.invoiceEntry.getPreis()
        else:
            return self.preis

    def ok(self):
        self.close()

    def abbrechen(self):
        self.updateEinzelpreis(self.start_einzelpreis)
        self.close()

    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False
    
    def connectSlots(self):
        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_delete.clicked.connect(self.ui.input_einzelpreis.clear)
        self.ui.button_comma.clicked.connect(self.numberPressed('.'))
        self.ui.button_negate.clicked.connect(self.negateValue)
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen.clicked.connect(self.abbrechen)
        self.ui.input_einzelpreis.clicked = self.updateEinzelpreis
        self.ui.input_einzelpreis.installEventFilter(self)




