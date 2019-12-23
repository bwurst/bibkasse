#!/usr/bin/python
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

import os, sys
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), 'src'))
from lib.Speicher import Speicher
from lib.printer.esc import ESCPrinter


if __name__ == "__main__":
	os.chdir( os.path.dirname( sys.argv[0] ))
	
	password = raw_input('Bestehender Code: ').strip()
	
	
	s = Speicher()
	if not s.check_password(password):
		print ('Falscher Code!')
		sys.exit(1)

	existing_users = s.list_users()
	print ('Momentan vorhandene Benutzer:')
	for u in existing_users:
		print ('  %s: %s (%s)' % (u['id'], u['name'], u['role']))

	print ('Welchen User ändern? [0=neuer User] ')
	choice = raw_input().strip()
	if choice == '0':
		username = raw_input('Neuer Benutzername: ').strip()
		password = raw_input('Passwort: ').strip()	
	
		userid = s.add_user(username, password)
	else:
		username = None
		for u in existing_users:
			if u['id'] == choice:
				username = u['name']
		if username:
			password = raw_input('Passwort: ').strip()
			if password:
				s.set_user_password(choice, username, password)
		else:
			print ('Nicht gefunden!')
	
