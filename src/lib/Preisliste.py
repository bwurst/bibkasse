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


import os
from xml.etree.ElementTree import ElementTree as ET
from collections import OrderedDict


class Preisliste(object):
	'''Erlaubt den Zugriff auf die Preisliste.'''
	FILENAME = "daten/preisliste.xml"
	TOLERANZ = 10
	
	def __init__(self):
		self.preise = {}
		self.mindestpreis = {}
		self.liter = {}
		self.beschreibungen = {}
		self.einheiten = {}
		self.registeredObjects = {}
		self.rabattGruppen = {}
		self.steuersatz = {}
		self.__manuelleLiterzahl = None
		self.__ladePreise(self.FILENAME)
		
	def __repr__(self):
		out = ''
		for key in self.preise.keys():
			out += '%s / %s (je %i Liter):\n' % (key, self.beschreibungen[key], self.liter[key])
			stufen = sorted(list(self.preise[key].keys()))
			for stufe in stufen:
				if stufe[0] == 'liter':
					out += '	ab %3i Liter:	%5.2f €\n' % (stufe[1], self.preise[key][stufe])
				elif stufe[0] == 'stueck':
					out += '	ab %3i Stück:	%5.2f €\n' % (stufe[1], self.preise[key][stufe])
			out += '\n'
		return out
		
	def __ladePreise(self, dateiname):
		'''Lädt Preise aus einer XML-Datei (daten/preisliste.xml)'''
		#if not os.path.exists(dateiname):
		#	# Wenn die Preisliste nicht da ist, soll man diese vom USB-Stick importieren können
		#	from gui.self_update import showUpdateDialog
		#	showUpdateDialog()
		tree = ET()
		try:
			tree.parse(dateiname)
		except:
			print('Die Preisliste wurde nicht gefunden. Bitte daten/preisliste.xml.example nach preisliste.xml kopieren und anpassen!')
			raise Exception("Could not open pricelist file")
		for item in tree.findall('item'):
			if not 'key' in item.attrib:
				raise ValueError("Invalid Pricelist-Entry!")
			key = item.attrib['key']
			self.preise[key] = {}
			einheit = 'Stk'
			if 'unit' in item.attrib:
				einheit = item.attrib['unit']
			self.einheiten[key] = einheit
			if 'rebategroup' in item.attrib:
				rg = item.attrib['rebategroup']
				if rg in self.rabattGruppen.keys():
					self.rabattGruppen[rg].append(key)
				else:
					self.rabattGruppen[rg] = [key, ]
			if 'vat' in item.attrib:
				self.steuersatz[key] = float(item.attrib['vat'])
			if key == 'minprice':
				minpricekeys = []
				for k in item.findall('key'):
					minpricekeys.append(k.text)
				price = item.find('price').text
				self.mindestpreis['keys'] = minpricekeys
				self.mindestpreis['gesamtpreis'] = float(price)
			for c in item.findall('price'):
				value = float(c.text)
				stufe = 0
				if 'liter' in c.attrib:
					if self.rabattArt(key) != 'liter':
						raise ValueError('Fehler in der Preisliste: %s: Liter-Rabatt nicht vorgesehen' % key)
					stufe = int(c.attrib['liter'])
					self._rabattStufeSetzen(key, stufe, value)
				elif 'count' in c.attrib:
					if self.rabattArt(key) == 'liter' or not self.rabattArt(key):
						raise ValueError('Fehler in der Preisliste: %s: Stückzahl-Rabatt nicht vorgesehen' % key)
					stufe = float(c.attrib['count'])
					self._rabattStufeSetzen(key, stufe, value)
				else:
					self._rabattStufeSetzen(key, 0, value)
			if 'desc' in item.attrib:
				self.beschreibungen[key] = item.attrib['desc']
			else:
				self.beschreibungen[key] = key
			if 'liter' in item.attrib:
				self.liter[key] = int(item.attrib['liter'])
			else:
				self.liter[key] = 0
		

	def rabattArt(self, key):
		for rg, list in self.rabattGruppen.items():
			if key in list:
				return rg
		return 'default'

	def _rabattStufeSetzen(self, key, stufe, value):
		rabattArt = self.rabattArt(key)
		self.preise[key][(rabattArt, stufe)] = value

	def rabattStufen(self, key):
		stufen = sorted(list(self.preise[key].keys()))
		ret = OrderedDict()
		for s in stufen:
			ret[s] = self.preise[key][s]
		return ret

	def getSteuersatz(self, key):
		if key in self.steuersatz.keys():	
			return self.steuersatz[key]
		else:
			return 0.0

	def getRabattStufe(self, key):
		'''Liefert die logische Rabattstufe aller momentan registrierten Rechnungsposten
		   der betreffenden Rabatt-Gruppe 
		'''
		rabattGruppe = self.rabattArt(key)
		if rabattGruppe not in self.rabattGruppen.keys():
			return None
		# Zunächst Daten aller angemeldeten Objekte sammeln
		amount = 0
		liter_frischsaft = 0
		# Rabatt für Pressen wird mit den Bag-in-Box-Litern addiert
		# Für Liter-Rabatte werden alle angemeldeten Objekte gelesen, auch die, die keinen Liter-Rabatt bekommen (3-Liter, Verkauf-Säfte)
		if rabattGruppe in ['liter', 'liter_frisch']:
			# Liter erhalten immer die Toleranz dazu
			amount = self.TOLERANZ
			for mykey in self.registeredObjects.keys():
				for obj in self.registeredObjects[mykey]:
					if not obj.preisliste_link:
						continue
					liter = 0
					try:
						liter = int(obj.getLiterzahl())
						if mykey == 'frischsaft' and key == 'frischsaft':
							liter = obj.getStueckzahl()
							liter_frischsaft = liter
					except:
						print ('Ungültiges Preislisten-Callback-Objekt: %s' % obj)
					amount += liter
		else:
			for mykey in self.rabattGruppen[rabattGruppe]:
				if not mykey in self.registeredObjects.keys():
					continue
				for obj in self.registeredObjects[mykey]:
					if not obj.preisliste_link:
						continue
					stk = 0
					try:
						stk = int(obj.getStueckzahl())
					except:
						print ('Ungültiges Preislisten-Callback-Objekt: %s' % obj)
					amount += stk
		# Wenn der Kunde weniger als 30 Liter offen mit nimmt, dann ist das immer der Basispreis
		if key == 'frischsaft' and liter_frischsaft < 30:
			amount = 1
		return self.getRabattStufeForAmount(key, amount)
	
	
	def getRabattStufeForAmount(self, key, value):
		# Dann Rabattstufen durchgehen
		rabatte = self.rabattStufen(key)
		ret = None
		# Rechne aus und speichere welches die kommende Rabattstufe wäre 
		naechste_stufe = None
		for rabatt_key in rabatte.keys():
			if (rabatt_key[1] <= value):
				ret = rabatt_key
			else:
				if not naechste_stufe:
					naechste_stufe = rabatt_key
		if ret is None:
			raise ValueError('Fehler in der Rabattstufe für (%s, %s)' % (key, value))
		# Günstigerprüfung: Wenn die volle Menge bei der kommenden Rabattstufe günstiger 
		# wäre, dann springe auf nächstbilligere Stufe
		if key == 'frischsaft' and naechste_stufe:
			preis1 = (value-self.TOLERANZ) * self.preise[key][ret]
			#print ('Preis 1: %s * %s = %s' % (value, self.preise[key][ret], preis1))
			preis2 = naechste_stufe[1] * self.preise[key][naechste_stufe]
			#print ('Preis 2: %s * %s = %s' % (naechste_stufe[1], self.preise[key][naechste_stufe], preis2))
			if preis1 > preis2:
				ret = naechste_stufe
		return ret
		
	def getEinheit(self, key):
		return self.einheiten[key]
		
	def getLiterzahl(self):
		'''Liefert die Literzahl aller momentan registrierten Rechnungsposten.'''
		liter = 0
		for key in self.registeredObjects.keys():
			for obj in self.registeredObjects[key]:
				if not obj.preisliste_link:
					continue
				l = 0
				try:
					l = int(obj.getLiterzahl())
				except:
					print ('Ungültiges Preislisten-Callback-Objekt: %s' % obj)
				liter += l
		return liter


	def getLiterProEinheit(self, key):
		if key in self.liter:
			return int(self.liter[key])
		else:
			return 0
		

	def getBeschreibung(self, key):
		if key in self.beschreibungen:
			return self.beschreibungen[key]
		else:
			return None


	def getBeschreibungen(self):
		return self.beschreibungen


	def getPreis(self, key, amount=None):
		'''Liefert den Preis des benannten Preislisten-Eintrags, basierend
			 auf der übergebenen Liter- oder Stückzahl oder (wenn keine Menge 
			 übergeben wird) aufgrund der betreffenden Menge aller 
			 registrierten Rechnungsposten.'''
		if key == 'minprice':
			if self.mindestpreis:
				betrag = self.mindestpreis['gesamtpreis']
				have_minprice_items = False
				for key in self.mindestpreis['keys']:
					if key in self.registeredObjects.keys():
						for obj in self.registeredObjects[key]:
							have_minprice_items = True
							betrag -= obj.getSumme()
				if not have_minprice_items:
					return 0.0
				return max(betrag, 0.0)
			else:
				raise IndexError("Kein Mindestpreis definiert")
		if key not in self.preise:
			raise IndexError("Don't have a pricelist entry named %s" % key)
		if amount is None:
			if self.getRabattStufe(key) is None:
				amount = 1
			else:
				amount = self.getRabattStufe(key)[1]
		preisstufe = self.getRabattStufeForAmount(key, amount)
		return self.preise[key][preisstufe]
		
		
	def registerObject(self, key, obj):
		'''Registriert einen neuen Rechnungsposten an der Preisliste. 
			 "key" ist ein Preislisten-Element, 
			 "obj" bezeichnet ein Objekt das mindestens die Methoden 
			 setPreis(neuerpreis), getLiterzahl() und getStueckzahl() 
			 enthält.'''
		if key not in self.preise.keys():
			raise IndexError("We have not Pricelist-Entry named %s" % key)
		if key not in self.registeredObjects.keys():
			self.registeredObjects[key] = []
		self.registeredObjects[key].append(obj)
		return True


	def unregisterObject(self, obj):
		'''Entfernt das Objekt "obj" aus der Liste der registrierten 
			 Objekte'''
		for key in self.registeredObjects.keys():
			if obj in self.registeredObjects[key]:
				try:
					self.registeredObjects[key].remove(obj)
				except:
					pass
	


	def unregisterAllObjects(self):
		self.registeredObjects.clear()






if __name__ == '__main__':
	p = Preisliste()

	print (p)
	print (p.getPreis('10er', 4))
	print (p.getPreis('10er', 17))
	print (p.rabattStufen('10er'))
	print (p.getPreis('5er', 4))
	print (p.getPreis('5er', 27))
	print (p.rabattGruppen)
	print (p.registeredObjects)
	print (p.getLiterzahl())
	print (p.getPreis('5er'))

	class LiterGenerator(object):
		preis = 0.0
		preisliste_link = True
		def __repr__(self):
			return 'LiterGenerator(%s => %s l)' % (self.stueck, self.liter)
		def __init__(self, stueck, liter):
			self.stueck = stueck
			self.liter = liter
		def getLiterzahl(self):
			return self.liter
		def setPreis(self, preis):
			self.preis = preis
		def getSumme(self):
			return self.preis * self.stueck

	class StueckGenerator(object):
		preis = 0.0
		preisliste_link = True
		def __repr__(self):
			return 'StueckGenerator(%s)' % self.stueck
		def __init__(self, stueck):
			self.stueck = stueck
		def getLiterzahl(self):
			return 0
		def getStueckzahl(self):
			return self.stueck
		def setPreis(self, preis):
			self.preis = preis
		def getSumme(self):
			return self.preis * self.stueck

	# obj = LiterGenerator(100)
	# p.registerObject('5er', obj)
	obj = LiterGenerator(20, 200)
	p.registerObject('10er', obj)
	obj.setPreis(p.getPreis('10er'))
	print ('Summe:', obj.getSumme())
	print (p.getBeschreibung('minprice')+':', p.getPreis('minprice'))
	try:
		p.registerObject('3er', obj)
	except:
		print ('Konnte 3er-Objekt nicht registrieren!')
		
	print (p.registeredObjects)
	print (p.getLiterzahl())
	print (p.getPreis('5er'))
	print (p.getPreis('holzstaender_klassisch'))
	print ('Einzelpreis:', obj.preis)

	p.unregisterObject(obj)

	print (p.getPreis('5er_vk'))
	print (p.getPreis('10er_vk'))
	print (p.getPreis('saft_offen'))

	obj = StueckGenerator(80)
	p.registerObject('saft_offen', obj)

	print (p.registeredObjects)
	print (p.getLiterzahl())
	print (p.getPreis('5er_vk'))
	print (p.getPreis('10er_vk'))
	print (p.rabattStufen('10er'))
	print (p.getPreis('saft_offen'))
	print (p.getPreis('holzstaender_klassisch'))
	
	obj = LiterGenerator(10, 100)
	p.registerObject('10er', obj)
	obj = StueckGenerator(280)
	p.registerObject('frischsaft', obj)
	print (p.registeredObjects)
	print (p.getPreis('frischsaft'))
	print (p.getLiterzahl())
	
	
	
