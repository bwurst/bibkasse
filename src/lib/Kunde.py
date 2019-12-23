# -* coding: utf-8 *-
# (C) 2012 by Bernd Wurst <bernd@schokokeks.org>

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



class Kunde(object):
    def __init__(self):
        self.__data = {'id': None,
                       'angelegt': None,
                       'firma': None,
                       'vorname': None,
                       'nachname': None,
                       'strasse': None,
                       'plz': None,
                       'ort': None,
                       'kontakt' : [],
                       'rechnung': False,
                       'ueberweisung': False,
                       'bio': False,
                       'bio_kontrollstelle': None,
                       'notizen': None,
                       }
    
    def getRAW(self):
        data = self.__data.copy()
        del data['kontakt']
        kontakt = self.__data['kontakt']
        return (data, kontakt)
    
    def setRAW(self, args):
        for key in args.keys():
            if key not in self.__data.keys():
                raise ValueError('assignment to invalid key %s' % key)
            self.__data[key] = args[key]
    
    def addKontaktRAW(self, typ, wert, notiz, id):
        self.__data['kontakt'].append({'id': id, 'typ': typ, 'wert': wert, 'notiz': notiz})
    
    def __setitem__(self, key, value):
        self._setzeWert(key, value)
    
    def __getitem__(self, key):
        return self._leseWert(key)
        
    def _setzeWert(self, schluessel, wert):
        if schluessel not in self.__data.keys():
            raise ValueError(u'Schlüssel nicht bekannt: %s' % schluessel)
        if wert == '':
            self.__data[schluessel] = None
        self.__data[schluessel] = wert

    def _leseWert(self, schluessel):
        if schluessel not in self.__data.keys():
            raise ValueError(u'Schlüssel nicht bekannt: %s' % schluessel)
        return self.__data[schluessel]
    
    def ID(self):
        return self._leseWert('id')
    
    def isBio(self):
        return self._leseWert('bio')
    
    def getOekoKontrollstelle(self):
        return self._leseWert('bio_kontrollstelle')
    
    def setOekoKontrollstelle(self, kst):
        if kst:
            self._setzeWert('bio_kontrollstelle', kst)
            self._setzeWert('bio', True)
        else:
            self._setzeWert('bio_kontrollstelle', None)
            self._setzeWert('bio', False)
    
    def setName(self, free=None, vorname=False, nachname=False, firma=False):
        if free:
            firma = ''
            vorname = ''
            nachname = free
            if '(' in free and ')' in free:
                firma = free[0:free.find('(')].strip()
                nachname = free[free.find('(')+1:-1]
                if ' ' in nachname:
                    vorname, nachname = nachname.split(' ', 1)
            elif ',' in free:
                nachname, vorname = free.split(',', 1)
            elif ' ' in free:
                vorname, nachname = free.split(' ', 1)
            self._setzeWert('vorname', vorname.strip())
            self._setzeWert('nachname', nachname.strip())
        if vorname is not False:
            self._setzeWert('vorname', vorname.strip())
        if nachname is not False:
            self._setzeWert('nachname', nachname.strip())
        if firma is not False:
            self._setzeWert('firma', firma)

    def getName(self):
        name = self._leseWert('nachname') or ''
        if self._leseWert('vorname'):
            name = ('%s, %s' % (self._leseWert('nachname') or '', self._leseWert('vorname') or '')).strip()
        if self._leseWert('firma'):
            name = ('%s %s' % (self._leseWert('vorname') or '', self._leseWert('nachname') or '')).strip()
            if name:
                name = '%s (%s)' % (self._leseWert('firma'), name)
            else:
                name = self._leseWert('firma').strip()
        return name

    def setAdresse(self, strasse=None, plz=None, ort=None):
        self._setzeWert('strasse', strasse)
        self._setzeWert('plz', plz)
        self._setzeWert('ort', ort)


    def getNurAdresse(self):
        addr = ('%s\n%s %s' % (self._leseWert('strasse') or '', self._leseWert('plz') or '', self._leseWert('ort') or '')).strip()
        return addr

    def getAdresse(self):
        addr = ('%s\n%s %s' % (self._leseWert('strasse') or '', self._leseWert('plz') or '', self._leseWert('ort') or '')).strip()
        if self._leseWert('nachname'):
            addr = ('%s %s' % (self._leseWert('vorname') or '', self._leseWert('nachname'))).strip()+'\n'+addr
        if self._leseWert('firma'):
            addr = ('%s' % (self._leseWert('firma'),)).strip()+'\n'+addr
        return addr

    def addKontakt(self, typ, wert, notiz=None, id=None):
        if typ in ['telefon', 'mobil']:
            for c in '-/ ()':
                wert = wert.replace(c, '')
        if wert and not wert.startswith('0'):
            wert = '07192'+wert
        self.__data['kontakt'].append({'id': id, 'typ': typ, 'wert': wert, 'notiz': notiz})

    def editKontakt(self, index, typ, wert, notiz=False):
        entry = self.__data['kontakt'][index]
        entry['typ'] = typ
        if typ in ['telefon', 'mobil']:
            for c in '-/ ()':
                wert = wert.replace(c, '')
        if wert and not wert.startswith('0'):
            wert = '07192'+wert
        entry['wert'] = wert
        if notiz is not False:
            entry['notiz'] = notiz
            

    def listKontakte(self):
        kontakte = self._leseWert('kontakt')
        return kontakte
    
    def listKontakteTelefon(self):
        kontakte = self._leseWert('kontakt')
        res = []
        for k in kontakte:
            if k['typ'] in ['telefon', 'mobil']:
                res.append(k)
        return res
    
    def getErsteTelefon(self):
        kont = self.listKontakte()
        ret = ''
        for k in kont:
            if k['typ'] == 'mobil':
                return k['wert']
            if k['typ'] == 'telefon' and not ret:
                ret = k['wert']
        return ret

    def getMobiltelefon(self):
        kontakte = self._leseWert('kontakt')
        for k in kontakte:
            if k['typ'] == 'mobil':
                return k['wert']
        

    def __str__(self):
        s = u'<ID %s>\n  %s\n  %s\n' % (self._leseWert('id'), self.getName(), self.getAdresse())
        for k in self.listKontakte():
            s += u"  %s: %s\n" % (k['typ'], k['wert'])
        if self._leseWert('rechnung'):
            s += u'Kunde will Rechnung'
        if self._leseWert('ueberweisung'):
            s += u'Kunde überweist'
        return s

    def __nonzero__(self):
        return self.__bool__()
    
    def __bool__(self):
        return (self._leseWert('firma') is not None or self._leseWert('nachname') is not None or len(self._leseWert('kontakt')) > 0)

    def copy(self):
        newkunde = Kunde()
        data, kontakt = self.getRAW()
        del(data['id'])
        newkunde.setRAW(data)
        for line in kontakt:
            newkunde.addKontaktRAW(line['typ'], line['wert'], line['notiz'], None)
        return newkunde


if __name__ == '__main__':
    import getpass, sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), '..'))
    from lib.Speicher import Speicher
    s = Speicher()
    password = getpass.getpass('Code: ')
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)

    l = s.sucheKundeTelefon('654')
    for k in l:
        print (str(k))        
    #k = Kunde(s)
    #k.setName('Egon', 'Maier')
    #k.setAdresse('Hinterm Berg 12', '12345', 'Beispielort')
    #k.addKontakt('telefon', '07123-65489')
    #k.addKontakt('mobil', '0173-321456')
    #assert k.ID() is not None, 'Kundennr. ist None'
    #print (str(k))

    #print 'lade #%s' % k.ID()
    #x = s.ladeKunde(k.ID())
    #print (str(x))
    