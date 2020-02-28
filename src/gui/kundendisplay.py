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
from PIL import Image
from PIL import ImageQt

from lib.BelegHTML import BelegHTML


import sys, os
from PyQt5.QtCore import QSize
import json
import subprocess
from PyQt5.QtGui import QPixmap, QIcon
IMAGE_PATH = 'ressource/kundendisplay'
IMAGE_DELAY = 45
#IMAGE_DELAY = 15

qrcode_dummy = QtGui.QIcon('ressource/images/qrcode.png')


class Animation(QtCore.QObject):
    def __init__(self, image):
        super().__init__()
        self.image = image
        
    
    def _set_pos(self, pos):
        self.image.setPos(pos)
        
    pos = QtCore.pyqtProperty(QtCore.QPointF, fset=_set_pos)
                 
    
        



class KundenDisplay(QtWidgets.QWidget):
    def __init__(self, application, run, mainwindow=None):
        self.active = True
        screens = application.screens()
        if len(screens) < 2: # or True: # FIXME: zweits Display bleibt auf diesem System aus!
            # Kein zweiter Bildschirm
            print ('Kein zweiter Bildschirm')
            self.active = False
            return
        if not run:
            self.active = False
            return
        
        self.mainwindow = mainwindow
    
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QWidget.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        #QtWidgets.QMainWindow.__init__(self, flags=QtCore.Qt.Window)
        try:
            self.ui = uic.loadUi('ressource/ui/kundendisplay.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
            
        self.showFullScreen()

        primary = application.primaryScreen()
        target_screen = None
        for screen in screens:
            if screen != primary:
                target_screen = screen
                break
        assert target_screen is not None
        screenres = target_screen.geometry()
        print ("Schiebe Kundendisplay auf folgende Koordinaten:")
        print ("x: %s, y: %s, w: %s, h: %s" % (screenres.x(), screenres.y(), screenres.width(), screenres.height()))
        self.move(screenres.x(), screenres.y());
        self.resize(screenres.width(), screenres.height());
        self.scene = QtWidgets.QGraphicsScene(0, 0, screenres.width(), screenres.height())
        self.ui.graphicsView.setScene(self.scene)
        
        self.ui.widgets.setCurrentIndex(2)
        self.images = []
        self.loadImages()
        if self.active:
            self.currentImage = 0
            self.currentPageCounter = QtWidgets.QGraphicsTextItem() 
            self.currentPageCounter.setFont(QtGui.QFont('Linux Biolinum O', 14))
            self.currentPageCounter.setPos(self.scene.width()-50,self.scene.height()-30);
            self.currentPageCounter.setPlainText("0 / %i" % (len(self.images)));
            self.currentPageCounter.setZValue(5)
            self.scene.addItem(self.currentPageCounter);
            self.animationimage = QtWidgets.QGraphicsPixmapItem()
            self.scene.addItem(self.animationimage)
            self.animationimage.setZValue(-1)

            self.showCurrentImage()
            self.timer = QtCore.QTimer(self)
            self.timer.start(IMAGE_DELAY * 1000)
            self.timer.timeout.connect(self.nextImage)
            self.ui.button_qrcode.clicked.connect(self.qrcode)
            self.ui.button_drucken.clicked.connect(self.drucken)
            self.ui.button_fertig.clicked.connect(self.fertig)
        
    def nextImage(self):
        self.currentImage += 1
        if self.currentImage == len(self.images):
            self.currentImage = 0 
        self.showCurrentImage()
        
    def loadImages(self):
        imgpath = os.path.realpath(os.path.join(IMAGE_PATH, "%sx%s" % (self.geometry().width(), self.geometry().height())))
        if not os.path.exists(imgpath):
            sys.stderr.write('image path für kundendisplay stimmt nicht oder keine passende Auflösung')
            self.active = False
            return
        files = sorted(list(os.listdir(imgpath)))
        for img in files:
            img = os.path.realpath(os.path.join(imgpath, img))
            print ('loading %s' % img)
            item = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(ImageQt.ImageQt(Image.open(img))))
            self.images.append(item)
            #self.scene.addItem(item)
        

    def showCurrentImage(self):
        previous = self.currentImage - 1
        if previous < 0:
            previous = len(self.images) - 1
        self.temppixmap = QtGui.QPixmap(self.scene.width(), self.scene.height()*2)
        painter = QtGui.QPainter(self.temppixmap)
        painter.drawPixmap(0, 0, self.images[previous].pixmap())
        painter.drawPixmap(0, self.scene.height(), self.images[self.currentImage].pixmap())

        self.animationimage.setZValue(-1)
        self.images[previous].setZValue(2)
        self.images[self.currentImage].setZValue(1)
        self.animationimage.setPixmap(self.temppixmap)
        self.animationimage.setY(0)
        
        self.animationimage.setZValue(3)

        self.animation = QtCore.QPropertyAnimation(Animation(self.animationimage), b"pos")
        self.animation.setDuration(2000)
        self.animation.setStartValue(QtCore.QPoint(0,0))
        self.animation.setEndValue(QtCore.QPoint(0,-self.scene.height()))
        self.animation.start()

        self.images[self.currentImage].setZValue(2)
        self.images[previous].setZValue(1)
        self.animationimage.setZValue(0)
        
        self.currentPageCounter.setPlainText("%i / %i" % (self.currentImage+1, len(self.images)));
        self.scene.update()

    def fertig(self):
        self.mainwindow.reset()

    def upload(self, filename):
        import requests
        upload = 'https://rechnung.mosterei-wurst.de/upload.php'
        files = {'pdf': (os.path.basename(filename), open(filename, 'rb'), 'application/pdf')}
        response = requests.post(upload, files=files)
        if not response.ok:
            return None
        data = json.loads(response.content)
        return data['url']


    def qrcode(self):
        url = self.upload(self.aktueller_beleg)
        proc = subprocess.run(['qrencode', '-o', '-', '-s', '12', '-d', '72', '-t', 'PNG', url], stdout=subprocess.PIPE)
        image = proc.stdout
        icon = QPixmap(250, 250)
        icon.loadFromData(image, 'png')
        self.ui.button_qrcode.setIcon(QIcon(icon))
        self.ui.button_qrcode.setIconSize(QSize(250,250))
        self.ui.button_qrcode.setEnabled(False)

    def drucken(self):
        filename = self.aktueller_beleg
        if not self.mainwindow.printer:
            # Kein Bondrucker
            QtWidgets.QMessageBox.warning(self.mainwindow, 'Kein Bondrucker', 'Der Bondrucker wurde nicht erkannt!', buttons=QtWidgets.QMessageBox.Ok)
            return
        if filename.endswith('.pdf'):
            filename = filename.replace('.pdf', '.esc')
        try:
            with open(filename, 'rb') as escfile:
                self.mainwindow.printer.raw(escfile.read())
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self.mainwindow, 'Keine Belegdaten', 'Die Belegdaten sind nicht hinterlegt!', buttons=QtWidgets.QMessageBox.Ok)
            
        self.mainwindow.reset()
        
            
    def toggle(self, state):
        if state:
            if self.modus == 'beleg':
                self.ui.widgets.setCurrentIndex(1)
            elif self.modus == 'vorgang':
                self.ui.widgets.setCurrentIndex(0)
            else:
                self.ui.widgets.setCurrentIndex(2)
        else:
            self.ui.widgets.setCurrentIndex(2)
            
    def showBeleg(self, filename = None):
        self.modus = 'beleg'
        self.ui.button_qrcode.setEnabled(True)
        self.aktueller_vorgang = None
        if filename:
            self.aktueller_beleg = filename
        if not self.active:
            return
        self.ui.button_qrcode.setIcon(qrcode_dummy)
        htmlfile = filename.replace('.pdf', '.html')
        try:
            with open(htmlfile, mode='r', encoding='utf-8') as f:
                text = f.read()
                self.ui.textBrowser_beleg.setHtml(text)
        except FileNotFoundError:
            self.ui.textBrowser_beleg.setHtml('<em>Datei für diesen Beleg nicht gefunden!</em>')
        self.ui.textBrowser.setStyleSheet('''
        * {
          font-size: 12pt;
        }
        ''')
        self.ui.widgets.setCurrentIndex(1)
            
        

    def showVorgang(self, vorgang = None):
        self.modus = 'vorgang'
        self.aktueller_beleg = None
        if vorgang: 
            self.aktueller_vorgang = vorgang
        if not self.active:
            return
        text = BelegHTML(vorgang, public=True)
        self.ui.textBrowser.setHtml(text)
        self.ui.textBrowser.setStyleSheet('''
        * {
          font-size: 20pt;
        }
        ''')
        self.ui.widgets.setCurrentIndex(0)

    def showSlideshow(self):
        self.modus = 'slideshow'
        self.aktueller_beleg = None
        if not self.active:
            return
        self.ui.widgets.setCurrentIndex(2)
        
    def terminate(self):
        if self.active:
            self.close()
