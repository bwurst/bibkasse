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

from lib.BelegDummy import BelegDummy
from lib.Speicher import Speicher

Wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

try:
    (ui_class, ui_base) = uic.loadUiType('ressource/ui/alte_abfuellungen_listentry.ui')
except:
    print ('Kann UI-Datei nicht laden!')
    sys.exit(1)


ueberweisung_image = QtGui.QImage()
ueberweisung_image.load('ressource/icons/ueberweisung.png')
ueberweisung_pixmap = QtGui.QPixmap.fromImage(ueberweisung_image)

bezahlt_image = QtGui.QImage()
bezahlt_image.load('ressource/icons/bargeld.png')
bezahlt_pixmap = QtGui.QPixmap.fromImage(bezahlt_image)

ec_image = QtGui.QImage()
ec_image.load('ressource/icons/ec.png')
ec_pixmap = QtGui.QPixmap.fromImage(ec_image)

anzahlung_image = QtGui.QImage()
anzahlung_image.load('ressource/icons/anzahlung.png')
anzahlung_pixmap = QtGui.QPixmap.fromImage(anzahlung_image)

rechnung_image = QtGui.QImage()
rechnung_image.load('ressource/icons/rosette.png')
rechnung_pixmap = QtGui.QPixmap.fromImage(rechnung_image)

bio_image = QtGui.QImage()
bio_image.load('ressource/icons/bio.png')
bio_pixmap = QtGui.QPixmap.fromImage(bio_image)

telefon_image = QtGui.QImage()
telefon_image.load('ressource/icons/telefon.png')
telefon_pixmap = QtGui.QPixmap.fromImage(telefon_image)

telefon_ok_image = QtGui.QImage()
telefon_ok_image.load('ressource/icons/telefon_ok.png')
telefon_ok_pixmap = QtGui.QPixmap.fromImage(telefon_ok_image)

telefon_ab_image = QtGui.QImage()
telefon_ab_image.load('ressource/icons/telefon_ab.png')
telefon_ab_pixmap = QtGui.QPixmap.fromImage(telefon_ab_image)

telefon_nichterreicht_image = QtGui.QImage()
telefon_nichterreicht_image.load('ressource/icons/telefon_nichterreicht.png')
telefon_nichterreicht_pixmap = QtGui.QPixmap.fromImage(telefon_nichterreicht_image)

sms_image = QtGui.QImage()
sms_image.load('ressource/icons/sms.png')
sms_pixmap = QtGui.QPixmap.fromImage(sms_image)

sms_ok_image = QtGui.QImage()
sms_ok_image.load('ressource/icons/sms_ok.png')
sms_ok_pixmap = QtGui.QPixmap.fromImage(sms_ok_image)

sms_error_image = QtGui.QImage()
sms_error_image.load('ressource/icons/sms_error.png')
sms_error_pixmap = QtGui.QPixmap.fromImage(sms_error_image)

sms_question_image = QtGui.QImage()
sms_question_image.load('ressource/icons/sms_question.png')
sms_question_pixmap = QtGui.QPixmap.fromImage(sms_question_image)


class AbfuellungWidget(QtWidgets.QFrame):
    def __init__(self, invoice):
        self.invoice = invoice
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QFrame.__init__(self)
        
        self.ui = ui_class()
        self.ui.setupUi(self)

        kundenname = invoice.getKundenname()
        if not kundenname:
            kundenname = u'<i>Barverkauf</i>'
        self.ui.label_kundenname.setText(kundenname)
        if invoice.getStatus() in ['ignored', 'deleted']:
            self.ui.label_kundenname.setStyleSheet('''color: #aaa;''')
            self.ui.label_gesamtpreis.setStyleSheet('''color: #aaa;''')
        else:
            self.ui.label_kundenname.setStyleSheet('')
            self.ui.label_gesamtpreis.setStyleSheet('')
        
        zeitpunkt = invoice.getZeitpunkt()
        if zeitpunkt:
            self.ui.label_zeitpunkt.setText('%s, %s Uhr' % (Wochentage[zeitpunkt.weekday()], zeitpunkt.strftime('%d.%m.%Y / %H:%M') ))
        else:
            self.ui.label_zeitpunkt.setText('unbekannt')
        self.ui.label_liter.setText('%i Liter' % invoice.getLiterzahl())
        self.ui.label_gesamtpreis.setText(u'%.2f €' % invoice.getSumme())

        self.__invoice = invoice
        self.update()

    def update(self):
        if self.invoice.getPayed() and self.invoice.getZahlart() == 'ec':
            self.ui.label_bezahlung.setPixmap(ec_pixmap)
        elif self.invoice.getBanktransfer():
            self.ui.label_bezahlung.setPixmap(ueberweisung_pixmap)
        elif self.invoice.getPayed():
            self.ui.label_bezahlung.setPixmap(bezahlt_pixmap)
        elif self.invoice.getPartlyPayed():
            self.ui.label_bezahlung.setPixmap(anzahlung_pixmap)
        else:
            self.ui.label_bezahlung.setPixmap(QtGui.QPixmap())
            
        if self.invoice.isRechnung():
            self.ui.label_rechnung.setPixmap(rechnung_pixmap)
        else:
            self.ui.label_rechnung.setPixmap(QtGui.QPixmap())

        if self.invoice.isBio():
            self.ui.label_bio.setPixmap(bio_pixmap)
        else:
            self.ui.label_bio.setPixmap(QtGui.QPixmap())
            
        if not self.invoice.getBanktransfer() and not self.invoice.getPayed():
            if self.invoice.getTelefon():
                self.ui.label_anruf.setPixmap(telefon_pixmap)
                anrufe = Speicher().getAnrufe(self.invoice)
                if len(anrufe) > 0:
                    anruf = anrufe[-1]
                    if anruf['ergebnis'] == 'erreicht':
                        self.ui.label_anruf.setPixmap(telefon_ok_pixmap)
                    elif anruf['ergebnis'] == 'ab':
                        self.ui.label_anruf.setPixmap(telefon_ab_pixmap)
                    elif anruf['ergebnis'] == 'nichterreicht':
                        self.ui.label_anruf.setPixmap(telefon_nichterreicht_pixmap)
                    elif anruf['ergebnis'].startswith('sms'):
                        self.ui.label_anruf.setPixmap(sms_question_pixmap)
                        if anruf['ergebnis'] == 'sms-delivered':
                            self.ui.label_anruf.setPixmap(sms_ok_pixmap)
                        elif anruf['ergebnis'] in ('sms-buffered', 'sms-error'):
                            self.ui.label_anruf.setPixmap(sms_error_pixmap)
                else:
                    # Hintergrundfarbe, wenn kein Anruf hinterlegt ist (Vor-Ort-Kunde)
                    if not self.invoice.getPayed():
                        # Bei bezahlten nicht, sonst ist die erweiterte Ansicht gestört
                        # FIXME: Hier müsste man irgendwie durchreichen, ob die erweiterte Ansicht aktiv ist.
                        self.setStyleSheet('background-color: #ffa;')


    def getBeleg(self):
        if type(self.__invoice) == BelegDummy:
            self.__invoice = Speicher().ladeBeleg(self.__invoice.ID) 
        return self.__invoice
    