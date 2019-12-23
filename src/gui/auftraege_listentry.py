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

from PyQt5 import QtWidgets, QtGui, uic
import sys

from lib.Speicher import Speicher

Wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

try:
    (ui_class, ui_base) = uic.loadUiType('ressource/ui/auftraege_listentry.ui')
except:
    print ('Kann UI-Datei nicht laden!')
    sys.exit(1)


frischsaft_image = QtGui.QImage()
frischsaft_image.load('ressource/icons/frischsaft.png')
frischsaft_pixmap = QtGui.QPixmap.fromImage(frischsaft_image)

gebrauchte_image = QtGui.QImage()
gebrauchte_image.load('ressource/icons/gebrauchte.png')
gebrauchte_pixmap = QtGui.QPixmap.fromImage(gebrauchte_image)

gitterbox_image = QtGui.QImage()
gitterbox_image.load('ressource/icons/gitterbox.png')
gitterbox_pixmap = QtGui.QPixmap.fromImage(gitterbox_image)

anhaenger_image = QtGui.QImage()
anhaenger_image.load('ressource/icons/anhaenger.png')
anhaenger_pixmap = QtGui.QPixmap.fromImage(anhaenger_image)

bio_image = QtGui.QImage()
bio_image.load('ressource/icons/bio.png')
bio_pixmap = QtGui.QPixmap.fromImage(bio_image)

telefon_image = QtGui.QImage()
telefon_image.load('ressource/icons/telefon.png')
telefon_pixmap = QtGui.QPixmap.fromImage(telefon_image)



class AuftragWidget(QtWidgets.QFrame):
    def __init__(self, auftrag):
        self.auftrag = auftrag
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QFrame.__init__(self)
        
        self.ui = ui_class()
        self.ui.setupUi(self)

        if auftrag.kunde:
            self.ui.label_kundenname.setText(auftrag.kunde.getName())
        else:
            self.ui.label_kundenname.setText('<i>Anonym</i>')
        zeitpunkt = auftrag.zeitpunkt
        if zeitpunkt:
            self.ui.label_zeitpunkt.setText('%s, %s Uhr' % (Wochentage[zeitpunkt.weekday()], zeitpunkt.strftime('%d.%m.%Y / %H:%M') ))
        else:
            self.ui.label_zeitpunkt.setText('unbekannt')
        

        self.update()

    def update(self):
        if self.auftrag.bio:
            self.ui.label_bio.setPixmap(bio_pixmap)
        else:
            self.ui.label_bio.setPixmap(QtGui.QPixmap())

        if self.auftrag.frischsaft:
            self.ui.label_frischsaft.setPixmap(frischsaft_pixmap)
            
        if self.auftrag.gebrauchte not in [None, False, '0']:
            self.ui.label_gebrauchte.setPixmap(gebrauchte_pixmap)
        
        if self.auftrag.lieferart == 'anhaenger':
            self.ui.label_gitterbox.setPixmap(anhaenger_pixmap)
        elif self.auftrag.lieferart == 'gitterbox':
            self.ui.label_gitterbox.setPixmap(gitterbox_pixmap)
            
        if self.auftrag.sonstiges or self.auftrag.anmerkungen:
            self.ui.label_sonstiges.setText('Hinweis vorhanden!')
        else:
            self.ui.label_sonstiges.setText('')
            
        if self.auftrag.neue == '5er' and self.auftrag.gebrauchte in [True, '1', False, '0', '5er']:
            self.ui.label_groesse.setText('5er')
        elif self.auftrag.neue == '10er' and self.auftrag.gebrauchte in [True, False, '0', '1', '10er']:
            self.ui.label_groesse.setText('10er')
        else:
            self.ui.label_groesse.setText('Gemischt')
            
            
    def getAuftrag(self):
        return self.auftrag
    