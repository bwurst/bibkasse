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

import tempfile, os, datetime, math, cups, sys

from lib.DatumEtiketten import DatumEtiketten


PRINTER_OPTIONS = {'media': 'A4',
                   'MediaType': 'Labels',
                   'sides': 'one-sided',
                   'InputSlot': 'MF1'}


class WidgetLabels(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_labels.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.spinboxlock = False

        self.anzahl=44
        self.skip=0
        self.datum=datetime.date.today()
        self.updateUI()

        self.ui.calendarWidget.selectionChanged.connect(self.dateChanged)
        self.ui.spinBox_etiketten.valueChanged.connect(self.spinBoxEtikettenChanged)
        self.ui.spinBox_seiten.valueChanged.connect(self.spinBoxSeitenChanged)
        self.ui.spinBox_skip.valueChanged.connect(self.spinBoxSkipChanged)

        self.ui.button_seiten_minus.clicked.connect(self.ui.spinBox_seiten.stepDown)
        self.ui.button_seiten_plus.clicked.connect(self.ui.spinBox_seiten.stepUp)

        self.ui.button_etiketten_minus.clicked.connect(self.ui.spinBox_etiketten.stepDown)
        self.ui.button_etiketten_plus.clicked.connect(self.ui.spinBox_etiketten.stepUp)

        self.ui.button_skip_minus.clicked.connect(self.ui.spinBox_skip.stepDown)
        self.ui.button_skip_plus.clicked.connect(self.ui.spinBox_skip.stepUp)

        self.ui.button_drucken.clicked.connect(self.drucken)
        self.ui.button_reset.clicked.connect(self.reset)
        

    def update(self):
        self.reset()

    def reset(self):
        self.anzahl=44
        self.skip=0
        self.datum=datetime.date.today()
        self.updateUI()
        

    def updateUI(self):
        self.ui.spinBox_etiketten.setValue(self.anzahl)
        self.ui.spinBox_seiten.setValue(math.ceil(float(self.anzahl) / 44)) 
        self.ui.spinBox_skip.setValue(self.skip)
        self.ui.calendarWidget.setSelectedDate(self.datum)
        scene = self.ui.graphicsView.scene()
        if not scene:
            scene = QtWidgets.QGraphicsScene()
        scene.clear()
        scene.setSceneRect(0,0,200,287)
        skip = self.skip
        if self.skip + self.anzahl > 44:
            skip = 0
        num = 0
        desired = (self.skip + self.anzahl) % 44
        if desired == 0:
            desired = 44
        for j in range(11):
            for i in range(4):
                brush = QtGui.QBrush(QtGui.QColor("black"))
                if skip > 0 or num >= desired:
                    brush.setColor(QtGui.QColor("white"))
                scene.addRect(i*50, j*26, 40, 24, brush=brush)
                if skip > 0:
                    skip -= 1
                num += 1
        self.ui.graphicsView.setScene(scene)
        if (self.anzahl + self.skip) > 44:
            self.ui.groupBox_vorschau.setTitle("Vorschau letzte Seite")
        else:
            self.ui.groupBox_vorschau.setTitle("Vorschau")
        
    def spinBoxEtikettenChanged(self, foo=None):
        if self.spinboxlock:
            return
        self.spinboxlock = True
        self.anzahl = self.ui.spinBox_etiketten.value()
        self.updateUI()
        self.spinboxlock = False
    
    def spinBoxSeitenChanged(self, foo=None):
        if self.spinboxlock:
            return
        self.spinboxlock = True
        self.anzahl = 44 * self.ui.spinBox_seiten.value()
        self.skip = 0
        self.updateUI()
        self.spinboxlock = False

    def spinBoxSkipChanged(self, foo=None):
        if self.spinboxlock:
            return
        self.spinboxlock = True
        self.skip = self.ui.spinBox_skip.value()
        self.updateUI()
        self.spinboxlock = False
        
    def dateChanged(self):
        self.datum = self.ui.calendarWidget.selectedDate().toPyDate()
        self.updateUI()

    def drucken(self):
        if self.datum != datetime.date.today():
          if QtWidgets.QMessageBox.No == QtWidgets.QMessageBox.warning(self, u'Datum ist nicht heute', u'Das gewählte Datum ist nicht das heutige Datum! Trotzdem drucken?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No):
            return
          
        tmp = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        tmp.write(DatumEtiketten(self.anzahl, self.skip, self.datum))
        tmp.close()
        
        c = cups.Connection()
        c.printFile(c.getDefault(), tmp.name, 'Etiketten %s' % self.datum.isoformat(), PRINTER_OPTIONS)
        #subprocess.call(['/usr/bin/xdg-open', tmp.name], shell=False)
        # xdg-open beendet sich sofort!
        os.unlink(tmp.name)
        self.reset()
        self.mainwindow.reset()
        
        
