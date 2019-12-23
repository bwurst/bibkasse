# -*- coding: utf-8 -*-
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

import glob, os, subprocess, sys, shutil

import socket, datetime, zipfile
import paramiko

BACKUP_HOST='192.168.0.100'

from PyQt5 import QtCore, QtWidgets, uic

def showUpdateDialog():
    up = SelfUpdate()
    up.show()
    up.exec_()
    


class SelfUpdate(QtWidgets.QDialog):
    def __init__(self):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self)
        try:
            self.ui = uic.loadUi('ressource/ui/self_update.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        self.ui.textBrowser.clear()
        self.ui.button_backup.clicked.connect(self.do_backup)
        self.ui.button_update.clicked.connect(self.do_update)
        self.ui.button_close.clicked.connect(self.close)
        self.sftp = None

    def output(self, text):
        if type(text) == str:
            pass
        else:
            text = text.decode('utf-8')
        self.ui.textBrowser.append(text.strip())


    
        
    def open_connection(self):
        if self.sftp:
            try:
                self.sftp.listdir('.')
            except:
                pass
            else:
                # Verbindung besteht schon
                return
        t = paramiko.Transport((BACKUP_HOST, 22))
        t.start_client()
        path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
        key = paramiko.RSAKey.from_private_key_file(path)
        t.auth_publickey('kasse', key)
        self.sftp = paramiko.SFTPClient.from_transport(t)
        


    def get_usbstick(self):
        candidates = glob.glob('/media/*/bib2012/bib2012.git')
        if len(candidates) > 1:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Es wurden mehrere USB-Sticks gefunden. So geht das nicht.', buttons=QtWidgets.QMessageBox.Ok)
            raise RuntimeError()
        if len(candidates) == 0:
            candidates = glob.glob('/media/*/*/bib2012/bib2012.git')
            if len(candidates) > 1:
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Es wurden mehrere USB-Sticks gefunden. So geht das nicht.', buttons=QtWidgets.QMessageBox.Ok)
                raise RuntimeError()
            if len(candidates) == 0:
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Es konnte kein USB-Stick gefunden werden.', buttons=QtWidgets.QMessageBox.Ok)
                return None

        return os.path.dirname(candidates[0])



    def do_backup(self):
        usbstick = self.get_usbstick()
        if not usbstick:
            return
        if not os.path.exists(os.path.join(usbstick, 'backup')):
            os.mkdir(os.path.join(usbstick, 'backup'))
        this_host = socket.gethostname()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_id = this_host + '_' + timestamp + '.zip'
        self.output('Make backup to %s' % os.path.join(usbstick, 'backup', backup_id))
        zip = zipfile.ZipFile(os.path.join(usbstick, 'backup', backup_id), 'w')
        
        for (base, dirs, files) in os.walk('daten'):
            for file in files:
                if file.startswith('.'):
                    continue
                self.output(os.path.join(base, file))
                zip.write(os.path.join(base, file))
                
        zip.close()
        self.output('calling fsync()\n')
        f = open(os.path.join(usbstick, 'backup', backup_id), 'r')
        f.flush()
        os.fsync(f.fileno())
        f.close()
        self.output('backup done!\n')
        


    def do_update(self):
        anything_done = False

        update_base = self.get_usbstick()
        if not update_base:
            return
        update_git = os.path.join(update_base, 'bib2012.git')
        
        self.output('Found update source: ' + update_base)
        current_commit = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], stderr=subprocess.STDOUT).strip()
        pull = subprocess.Popen(['git', 'pull', 'file://%s' % update_git], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while pull.poll() == None:
            line = pull.stdout.readline()
            self.output(line)
        self.output('»git pull« exited with code %i\n\n' % pull.returncode)
        self.output(subprocess.check_output(["git", "log", "%s..HEAD" % current_commit], stderr=subprocess.STDOUT))
        commit_after_update = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], stderr=subprocess.STDOUT).strip()
        if current_commit != commit_after_update:
            anything_done = True
        
        update_prices = os.path.join(update_base, 'preisliste.xml')
        if os.path.exists(update_prices):
            if not os.path.exists('daten/preisliste.xml'):
                self.output('No local pricelist found, fetch from Update...')
                anything_done = True
                shutil.copyfile(update_prices, 'daten/preisliste.xml')
            else:
                local = os.stat('daten/preisliste.xml')
                update = os.stat(update_prices)
                if local.st_mtime < update.st_mtime:
                    self.output('\n\nFound new pricelist, here is the diff:\n')
                    diff = subprocess.Popen(['diff', '-u', 'daten/preisliste.xml', update_prices], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    self.output(diff.stdout.read())
                    if (QtWidgets.QMessageBox.Yes ==
                        QtWidgets.QMessageBox.warning(self, u'Preisliste aktualisieren', u'Auf dem USB-Stick befindet sich eine neue Preisliste. Update übernehmen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                        anything_done = True
                        shutil.copyfile(update_prices, 'daten/preisliste.xml')

        update_altekunden = os.path.join(update_base, 'altekunden.txt')
        if os.path.exists(update_altekunden):
            if not os.path.exists('daten/altekunden.txt'):
                self.output('No local altekunden.txt found, fetch from Update...')
                anything_done = True
                shutil.copyfile(update_altekunden, 'daten/altekunden.txt')
            else:
                local = os.stat('daten/altekunden.txt')
                update = os.stat(update_altekunden)
                if local.st_mtime < update.st_mtime:
                    self.output('\n\nFound new altekunden.txt, here is the diff:\n')
                    diff = subprocess.Popen(['diff', '-u', 'daten/altekunden.txt', update_altekunden], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    self.output(diff.stdout.read())
                    if (QtWidgets.QMessageBox.Yes ==
                        QtWidgets.QMessageBox.warning(self, u'Kunden-Namen aktualisieren', u'Auf dem USB-Stick befindet sich eine neue Liste mit bereits eingegebenen Kundennamen. Update übernehmen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                        anything_done = True
                        shutil.copyfile(update_altekunden, 'daten/altekunden.txt')

        update_alterechnungsadressen = os.path.join(update_base, 'alterechnungsadressen.txt')
        if os.path.exists(update_alterechnungsadressen):
            if not os.path.exists('daten/alterechnungsadressen.txt'):
                self.output('No local alterechnungsadressen.txt found, fetch from Update...')
                anything_done = True
                shutil.copyfile(update_alterechnungsadressen, 'daten/alterechnungsadressen.txt')
            else:
                local = os.stat('daten/alterechnungsadressen.txt')
                update = os.stat(update_alterechnungsadressen)
                if local.st_mtime < update.st_mtime:
                    self.output('\n\nFound new alterechnungsadressen.txt, here is the diff:\n')
                    diff = subprocess.Popen(['diff', '-u', 'daten/alterechnungsadressen.txt', update_alterechnungsadressen], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    self.output(diff.stdout.read())
                    if (QtWidgets.QMessageBox.Yes ==
                        QtWidgets.QMessageBox.warning(self, u'Rechnungsadressen aktualisieren', u'Auf dem USB-Stick befindet sich eine neue Liste mit bereits eingegebenen Rechnungsadressen. Update übernehmen?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
                        anything_done = True
                        shutil.copyfile(update_alterechnungsadressen, 'daten/alterechnungsadressen.txt')

        if anything_done and (QtWidgets.QMessageBox.Yes ==
            QtWidgets.QMessageBox.warning(self, u'Programm neustarten?', u'Es wurden Programmdateien aktualisiert. Ein Neustart ist nun nötig. Soll dieser jetzt gemacht werden?', buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, defaultButton=QtWidgets.QMessageBox.No)):
            python = sys.executable
            os.execl(python, python, * sys.argv)
        

    
if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    
    translator = QtCore.QTranslator()
    # FIXME: Das ist wieder mal nicht besonders portabel
    translator.load("qt_de", "/usr/share/qt4/translations")
    app.installTranslator(translator)
    
    showUpdateDialog()
    
    

