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

from PyQt5 import QtGui, QtCore, QtWidgets, uic

import time, sys
import signal
import logging

from gui.widget_abfuellung import WidgetAbfuellung
from gui.widget_history import WidgetHistory
from gui.widget_labels import WidgetLabels
from gui.widget_statistics import WidgetStatistics
from gui.widget_zaehlprotokoll import WidgetZaehlprotokoll
from gui.widget_kasse import WidgetKasse
from gui.widget_codeentry import WidgetCodeEntry
from gui.widget_startpage import WidgetStartpage
from gui.widget_auftraege import WidgetAuftraege

from gui.self_update import showUpdateDialog

from gui.kundendisplay import KundenDisplay

from lib.printer.esc import ESCPrinter
from lib.Shutdown import shutdown, restart
from lib.Speicher import Speicher
from gui.widget_beleg import WidgetBeleg

UNLOCK_TIME = 120

icon_kundendisplay_off = QtGui.QIcon("ressource/images/kundendisplay_aus.png")
icon_kundendisplay_on = QtGui.QIcon("ressource/images/kundendisplay_an.png")


class BibMainWindow(QtWidgets.QMainWindow):
    application = None
    
    def __init__(self, application):
        self.application = application
        # Konstruktor der Superklasse aufrufen
        #QtWidgets.QMainWindow.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        QtWidgets.QMainWindow.__init__(self, flags=QtCore.Qt.Window)
        try:
            self.ui = uic.loadUi('ressource/ui/main.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
            

        screen = self.application.primaryScreen()
        # Maximiere auf Bildschirm 1
        screenres = screen.geometry();
        print ("Schiebe Hauptprogramm auf folgende Koordinaten:")
        print ("x: %s, y: %s, w: %s, h: %s" % (screenres.x(), screenres.y(), screenres.width(), screenres.height()))
        self.move(screenres.x(), screenres.y());
        self.resize(screenres.width()-100, screenres.height()-100);
        self.showFullScreen()

        # Maximiere auf Bildschirm 2
        #if QtWidgets.QApplication.desktop().screenCount() > 1:
        #    screenres = QtWidgets.QApplication.desktop().screenGeometry(2);
        #    self.move(screenres.x(), screenres.y());
        #    self.resize(screenres.width(), screenres.height());
        #    self.showFullScreen()


        self.kundendisplay = KundenDisplay(self.application, run=True, mainwindow=self)
        
        self.__restart_requested = False
        self.reallyLocked = False
        self.showAfterUnlock = None
        self.unlocked = False
        self.unlock_timer = QtCore.QTimer(self)
        
        self.WIDGETS = {'startpage': WidgetStartpage(self),
                        'abfuellung': WidgetAbfuellung(self),
                        'history': WidgetHistory(self), 
                        'auftraege': WidgetAuftraege(self), 
                        'history_last10': WidgetHistory(self, last10=True), 
                        'labels': WidgetLabels(self),
                        'statistics': WidgetStatistics(self),
                        'zaehlprotokoll': WidgetZaehlprotokoll(self),
                        'kasse': WidgetKasse(self),
                        'codeentry': WidgetCodeEntry(self),
                        'changepin': WidgetCodeEntry(self, True),
                        'beleg': WidgetBeleg(self),
                        }
        
        self.LOCK = []
        #self.LOCK = ['history', 'history_complete', 'statistics', 'changepin']

        self.letzte_belege = []

        for w in self.WIDGETS.values():
            self.ui.widgets.addWidget(w.ui)
        
        self.currentWidget = 'abfuellung'
        self.showStartpage()
        self.ui.lock_status.setCurrentIndex(0)
        self.connectSlots()
        self.reallyLock()
        self.printer = None
        try:
            self.printer = ESCPrinter()
        except RuntimeError:
            print ("Drucker nicht bereit!")
            #QtWidgets.QMessageBox.warning(self.ui, u'Fehler', str("Drucker nicht bereit oder Rechte nicht korrekt!"), buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)        

    def closeEvent(self, event):
        for wid in list(self.WIDGETS.keys()):
            logging.info('beende Widget %s' % wid)
            try:
                self.WIDGETS[wid].shutdown()
            except:
                pass
            finally:
                del(self.WIDGETS[wid])
        super().closeEvent(event)

    def toggleKundendisplay(self, foo=None):
        state = self.ui.button_kundendisplay.isChecked()
        if state:
            self.ui.button_kundendisplay.setIcon(icon_kundendisplay_on)
        else:
            self.ui.button_kundendisplay.setIcon(icon_kundendisplay_off)
        self.kundendisplay.toggle(state)

    def addRecentInvoice(self, vorgang):
        for i in range(len(self.letzte_belege)):
            if self.letzte_belege[i].ID == vorgang.ID:
                del self.letzte_belege[i]
                break
        self.letzte_belege[:0] = [vorgang,]
        if len(self.letzte_belege) > 10:
            del self.letzte_belege[10]
        

    def showWidget(self, id):
        if id in self.LOCK and self.isLocked():
            self.showAfterUnlock = id
            self.showWidget('codeentry')
        else:
            self.ui.widgets.setCurrentWidget(self.WIDGETS[id].ui)
        try:
            if not (id in self.LOCK and self.isLocked()):
                # Rufe update()-Methode auf sofern sie existiert 
                self.WIDGETS[id].update()
                # rufe isShown() auf wenn das Widget angezeigt wird
                self.WIDGETS[id].isShown()
        except AttributeError:
            pass
        self.currentWidget = id
        if id == 'startpage':
            self.ui.lock_status.setCurrentIndex(1)
            self.unlocked = time.time()
            self.unlock_timer.start(100)
        else:
            self.ui.lock_status.setCurrentIndex(0)
            self.unlock_timer.stop()

    def reset(self):
        #self.kundendisplay.showSlideshow()
        self.ui.leftPanel.setCurrentIndex(0)
        self.WIDGETS['abfuellung'].neuerVorgang()
        self.showStartpage()

    def vorgangOeffnen(self, vorgang, kassiervorgang=False):
        self.WIDGETS['abfuellung'].vorgangOeffnen(vorgang, kassiervorgang=kassiervorgang)
        self.showWidget('abfuellung')
        if kassiervorgang:
            self.ui.leftPanel.setCurrentIndex(2)
        else:
            self.ui.leftPanel.setCurrentIndex(0)
        
        
    def vorgangKassieren(self, vorgang):
        self.ui.leftPanel.setCurrentIndex(2)
        self.WIDGETS['kasse'].vorgangKassieren(vorgang)
        self.showWidget('kasse')
        
    def belegAnzeigen(self, filename):
        self.ui.leftPanel.setCurrentIndex(2)
        self.WIDGETS['beleg'].showBeleg(filename)
        self.showWidget('beleg')
    
    
    def keepUnlocked(self):
        return self.ui.button_keep_unlocked.isChecked()

    def setLocked(self, bool = True):
        if self.reallyLocked and bool == False:
                self.ui.leftPanel.setCurrentIndex(0)
                self.ui.button_keep_unlocked.setChecked(False)
                speicher = Speicher()
                user = speicher.get_current_user()
                role = user['role']
                if role == 'admin':
                    self.ui.menubar.show()
                self.reallyLocked = False
                self.showStartpage()
        
        if bool == False:
            self.unlocked = time.time()
            if self.currentWidget == 'codeentry':
                if self.showAfterUnlock in self.WIDGETS.keys():
                    self.showWidget(self.showAfterUnlock)
                    self.showAfterUnlock = None
                else:
                    self.showStartpage()
            self.ui.lock_status.setCurrentIndex(1)
            self.unlockTimerTriggered()
            self.ui.button_keep_unlocked.setChecked(False)
            self.unlock_timer.timeout.connect(self.unlockTimerTriggered)
            self.ui.button_lock.clicked.connect(self.setLocked)
            self.ui.button_keep_unlocked.clicked.connect(self.keepUnlocked)
            self.unlock_timer.start(100)
        else:
            self.unlocked = False
            self.showAfterUnlock = None
            self.ui.lock_status.setCurrentIndex(0)
            self.unlock_timer.stop()

    def unlockTimerTriggered(self):
        value = float(UNLOCK_TIME) - (time.time() - self.unlocked)
        if self.keepUnlocked():
            self.unlocked = time.time()
        if value > 0.0:
            self.ui.progressBar_unlocked.setValue(value*10)
            self.ui.progressBar_unlocked.setFormat('%.1f s' % value)
        else:
            self.reallyLock()
        
    def isLocked(self):
        if self.keepUnlocked():
            return False 
        if self.unlocked != False:
            if self.unlocked < (time.time() - UNLOCK_TIME):
                self.unlocked = False
        return not self.unlocked


    def showStartpage(self):
        self.kundendisplay.showSlideshow()
        if self.currentWidget == 'abfuellung':
            if not self.WIDGETS['abfuellung'].abbrechen():
                return False
        if self.reallyLocked:
            self.reallyLock()
        else:
            self.showWidget('startpage')
            self.ui.leftPanel.setCurrentIndex(1)


    def showAbfuellungenWidget(self):
        self.WIDGETS['abfuellung'].modusSpeichern()
        self.showWidget('abfuellung')
        self.ui.leftPanel.setCurrentIndex(0)
            
    def showVerkaufWidget(self):
        self.WIDGETS['abfuellung'].modusDirektverkauf()
        self.showWidget('abfuellung')
        self.ui.leftPanel.setCurrentIndex(0)

    def showAuftraegeWidget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('auftraege')
    
    def showHistoryWidget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('history')
    
    def showLast10Widget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('history_last10')
    
    def showLabelsWidget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('labels')
    
    def showStatisticsWidget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('statistics')

    def showZaehlprotokollWidget(self):
        self.ui.leftPanel.setCurrentIndex(0)
        self.showWidget('zaehlprotokoll')

    def showBelegWidget(self):
        self.ui.leftPanel.setCurrentIndex(2)
        self.showWidget('beleg')

    def selfUpdate(self):
        showUpdateDialog()
        
    def reallyLock(self):
        self.kundendisplay.showSlideshow()
        self.reallyLocked = True
        self.ui.lock_status.setCurrentIndex(0)
        self.unlocked = False
        self.unlock_timer.stop()
        self.ui.leftPanel.setCurrentIndex(1)
        self.ui.menubar.hide()
        self.showWidget('codeentry')
        
        
    def changepin(self):
        #QtWidgets.QMessageBox.warning(self, u'Fehler', 'Das funktioniert momentan nicht!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
        self.showWidget('changepin')
        
    def shutdown(self):
        if (QtWidgets.QMessageBox.Yes ==
            QtWidgets.QMessageBox.warning(self, u'Wirklich Herunterfahren', 'Soll dieser Computer wirklich herunter gefahren werden?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
            shutdown()

    def restart(self):
        if (QtWidgets.QMessageBox.Yes ==
            QtWidgets.QMessageBox.warning(self, u'Wirklich Neustarten', 'Soll das Programm geschlossen und neu gestartet werden?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):        
            restart(self)

    def force_restart(self, *garbage):
        restart(self)
        
    def delayed_restart(self, *garbage):
        self.__restart_requested = True
        
    def oeffneKasse(self):
        if not self.printer:
            return None
        try:
            self.printer.openDrawer()
        except:
            print ('Drucker nicht bereit, kann Kassenlade nicht öffnen')
    
    def terminate(self, *garbage):
        self.reallyLock()
        speicher = Speicher()
        speicher.lock()
        speicher.unmount()
        try:
            self.printer.terminate()
        except:
            pass
        try:
            self.kundendisplay.terminate()
        except:
            pass
        time.sleep(0.1)
        self.close()
        
    def timer_event(self, *garbage):
        if self.__restart_requested and self.currentWidget == 'codeentry':
            restart(self)
    
    def connectSlots(self):
        self.timer = QtCore.QTimer(self)
        self.timer.start(200)
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGHUP, self.force_restart)
        signal.signal(signal.SIGUSR1, self.delayed_restart)
        self.timer.timeout.connect(self.timer_event)

        self.ui.button_zurueck.clicked.connect(self.showStartpage)
        self.ui.button_widget_kasse.clicked.connect(self.oeffneKasse)

        self.ui.button_kundendisplay.toggled.connect(self.toggleKundendisplay)

        self.ui.button_lock.clicked.connect(self.reallyLock)

        self.ui.action_restart.triggered.connect(self.restart)
        self.ui.actionBeenden.triggered.connect(self.terminate)
        self.ui.actionStatistik_2.triggered.connect(self.showStatisticsWidget)
        self.ui.actionZaehlprotokoll.triggered.connect(self.showZaehlprotokollWidget)
        self.ui.action_update.triggered.connect(self.selfUpdate)
        self.ui.action_changepin.triggered.connect(self.changepin)

        self.ui.actionSperren.triggered.connect(self.reallyLock)
        self.ui.actionHerunterfahren.triggered.connect(self.shutdown)


