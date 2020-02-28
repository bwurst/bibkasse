#!/usr/bin/python3
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




from PyQt5 import QtCore, QtWidgets
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), 'src'))

import logging



if __name__ == "__main__":
	fh = logging.FileHandler('bib.log')
	fh.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	#logging.basicConfig(handlers=[ch, fh])
	logging.basicConfig(filename='bib.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
	logging.info('BiB-Kasse gestartet')
	pid = os.getpid()
	pidfile = os.path.join(os.path.dirname(__file__), 'bib.pid')
	with open(pidfile, 'w') as pf:
		pf.write("%s\n" % pid)
		
	os.chdir( os.path.dirname( sys.argv[0] ))
	
	app = QtWidgets.QApplication(sys.argv)
	
	translator = QtCore.QTranslator()
	translator.load("qt_de", QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
	app.installTranslator(translator)
	
	app.setStyleSheet('''
		QPushButton {
			border: 1px solid black;
			background-color: white;
			border-radius: 10px;
		}
		QPushButton:checked {
			background-color: blue;
			color: white;
		}
		QLineEdit {
			border: 1px solid black;
		}
		QLineEdit:disabled {
			background-color: #ddd;
		}
		QMessageBox QPushButton { 
			min-width: 150px; 
			min-height: 50px; 
		}
		QScrollBar:vertical {
		  width: 40px;
		}		
		QScrollBar:vertical::handle {
		  height: 40px;
		}		
		QScrollBar:horizontal {
		   height: 40px;
		}		
		QScrollBar:horizontal::handle {
		  width: 40px;
		}		
		''')
	
	from lib.webinterface import start_webinterface
	
	start_webinterface()
	
	from gui.mainwindow import BibMainWindow
	
	main = BibMainWindow(app)
	
	main.show()

	
	ret = app.exec_()
	del(app)

	if os.path.exists(pidfile):
		os.unlink(pidfile)
	
	logging.info('BiB-Kasse beendet')
	sys.exit(ret)
