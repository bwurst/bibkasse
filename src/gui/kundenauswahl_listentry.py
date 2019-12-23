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

from lib.helpers import formatPhoneNumber

try:
    (ui_class, ui_base) = uic.loadUiType('ressource/ui/kundenauswahl_listentry.ui')
except:
    print ('Kann UI-Datei nicht laden!')
    sys.exit(1)


bio_image = QtGui.QImage()
bio_image.load('ressource/icons/bio.png')
bio_pixmap = QtGui.QPixmap.fromImage(bio_image)

telefon_image = QtGui.QImage()
telefon_image.load('ressource/icons/telefon.png')
telefon_pixmap = QtGui.QPixmap.fromImage(telefon_image)


class KundenAuswahlWidget(QtWidgets.QFrame):
    def __init__(self, kunde):
        self.kunde = kunde
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QFrame.__init__(self)
        
        self.ui = ui_class()
        self.ui.setupUi(self)

        kundenname = self.kunde.getName()
        self.ui.label_name.setText(kundenname)
        adresse = self.kunde.getNurAdresse().replace('\n', ', ')
        self.ui.label_adresse.setText(adresse)
        telefon = set()
        for t in self.kunde.listKontakte():
            if t['typ'] in ['mobil', 'telefon']:
                telefon.add(formatPhoneNumber(t['wert']))
        self.ui.label_telefon.setText(' / '.join(telefon))
        

