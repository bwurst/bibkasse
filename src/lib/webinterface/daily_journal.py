# -* coding: utf-8 *-
from lib.Speicher import Speicher

from . import check_authenticated, get_authtoken
from . import html

import datetime

class daily_journal(object):
    
    def GET(self, date = None):
        check_authenticated()
        if not date:
            date = datetime.date.today().isoformat()
        year = date[:4]
        s = Speicher(year=year, authtoken=get_authtoken())
        try:
            zahlungen = s.listZahlungenTagesjournal(str(date))
        except:
            raise
            return 'Speicher nicht entsperrt!'
        data = {}
        for z in zahlungen:
            if not z['zahlart'] in data.keys():
                data[z['zahlart']] = [] 
            data[z['zahlart']].append(z)
            
        output = u'Journal vom %s' % date
        zahlart = {'ec':'EC-Cash', 'bar': 'Barzahlung'}
        for key in ['ec', 'bar']:
            if key not in data.keys():
                continue
            anonymous = 0.0
            output += u'<br /><h3>%s</h3>\n<table style="width: 100%%"><tr><th>Name</th><th style="width: 10em">Betrag</th></tr>\n' % zahlart[key]
            summe = 0.0
            for z in data[key]:
                name = z['name']
                summe += z['betrag']
                if not z['name']:
                    name = '<i>Anonymer Kunde</i>'
                    #anonymous += z['betrag']
                    #continue
                output += u'<tr><td>%s</td><td class="right">%.2f €</td></tr>' % (name, z['betrag'])
            if anonymous > 0:
                output += u'<tr><td>Anonyme Kunden</td><td class="right">%.2f €</td></tr>' % anonymous
            output += u'<tr><td class="right"><b>Summe %s:</b></td><td class="right"><b>%.2f €</b></td></tr></table>' % (zahlart[key], summe)
                
        return html.page('Journal vom %s' % date, output)



