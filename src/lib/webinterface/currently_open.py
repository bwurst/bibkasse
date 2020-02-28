# -* coding: utf-8 *-
from lib.Speicher import Speicher
from lib.BelegHTML import BelegHTML
from lib.helpers import formatPhoneNumber

from . import check_authenticated, get_authtoken
from . import html

class currently_open:
    
    def GET(self):
        check_authenticated()
        s = Speicher(authtoken=get_authtoken())
        try:
            belege = s.listVorgaengeUnbezahlt()
        except:
            return 'Speicher nicht entsperrt!'
        data = []
        for b in belege:
            data.append(BelegSummaryWeb(b))
            
        out = '<div class="container">'
        out += '\n\n'.join(data)
        out += '</div>'
        
        return html.page('Offene Posten', out)



class display_beleg(object):
    def GET(self, handle):
        check_authenticated()
        self.speicher = Speicher(authtoken=get_authtoken())
        try:
            vorgang = self.speicher.ladeVorgang(handle)
        except:
            return 'Speicher nicht entsperrt!'
        
        return html.page(u'Beleg für %s' % vorgang.getKundenname(), self.BelegDetails(vorgang))



    def BelegDetails(self, b):
        
        phonenumbers = ' / '.join([ '<a href="tel:%s">%s</a>' % (x, formatPhoneNumber(x)) for x in b.getTelefon().split(' / ') ])
        
        out = u'<a class="back" href="/open">Zurück</a>'
        out += u'<div><h4 class="kundenname">%s</h4><p class="telefon-details">Telefon: %s<p></div>' % (b.getKundenname(), phonenumbers)
        
        anrufe = self.speicher.getAnrufe(b)
        text = u''
        for anruf in anrufe:
            if anruf['ergebnis'] == 'erreicht':
                text += u'%s - Erreicht - %s' % (anruf['timestamp'],anruf['bemerkung'])
            elif anruf['ergebnis'] == 'ab':
                text += u'%s - AB' % (anruf['timestamp'],)
            elif anruf['ergebnis'] == 'nichterreicht':
                text += u'%s - NICHT erreicht' % (anruf['timestamp'],)
            else:
                text += u'%s - %s' % (anruf['ergebnis'], anruf['timestamp'])
            text += '\n'
        out += u'<div class="card"><div class="card-header">Bisherige Anrufe:</div><div class="card-body"><pre class="phonehistory">%s</pre></div></div>' % text
        out += u'<div class="phonebuttons row">'
        out += u'<div class="col col-4"><a class="btn btn-primary" href="/phone/%s/call_ok">Jemanden erreicht</a></div>' % (b.ID,)
        out += u'<div class="col col-4"><a class="btn btn-warning" href="/phone/%s/call_na">Nicht erreicht</a></div>' % (b.ID,)
        out += u'<div class="col col-4"><a class="btn btn-secondary" href="/phone/%s/call_ab">Auf AB gesprochen</a></div>' % (b.ID,)
        out += u'</div>' 
        out += u'<br><br>'
        
        out += BelegHTML(b)
        
        return out



Wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']



def BelegSummaryWeb(b):
    out = u'<a href="open/%s" class="vorgang">' % b.ID
    kunde = b.getKundenname()
    if not kunde:
        kunde = '<i>Barverkauf</i>'
    out += u'<div class="vorgang"><div class="row"><div class="col col-12"><h4>%s</h4></div></div>' % kunde
    zeitpunkt = b.getZeitpunkt()
    out += '<div class="row"><div class="col col-6">'
    out += u'<div class="baseinfo"><p class="liter">%i Liter</p>' % b.getLiterzahl()
    out += u'<p class="datum">%s, %s Uhr</p>' % (Wochentage[zeitpunkt.weekday()], zeitpunkt.strftime('%d.%m.%Y / %H:%M'))
    if b.getTelefon():
        out += u'<p class="telefon">Telefon: %s</p>' % b.getTelefon()
    out += u'</div></div>'
    icons = icons_for_invoice(b)
    out += u'<div class="icons col col-2">%s</div>' % ''.join(icons)
    out += u'<div class="gesamtpreis col col-4">%.2f&nbsp;&euro;</div>' % b.getNormalsumme()
    out += u'</div></div></a>'
    return out




def icons_for_invoice(invoice):
    icons = []
    if invoice.getBanktransfer():
        icons.append('ueberweisung.png')
    elif invoice.getPayed():
        icons.append('bargeld.png')
    elif invoice.getPartlyPayed():
        icons.append('anzahlung.png')
        
    if invoice.isRechnung():
        icons.append('rosette.png')

    if invoice.isBio():
        icons.append('bio.png')
        
    if not invoice.getBanktransfer() and not invoice.getPayed():
        if invoice.getTelefon():
            telefon = True
            anrufe = Speicher(authtoken=get_authtoken()).getAnrufe(invoice)
            if len(anrufe) > 0:
                anruf = anrufe[-1]
                if anruf['ergebnis'] == 'erreicht':
                    icons.append('telefon_ok.png')
                    telefon = False
                elif anruf['ergebnis'] == 'ab':
                    icons.append('telefon_ab.png')
                    telefon = False
                elif anruf['ergebnis'] == 'nichterreicht':
                    icons.append('telefon_nichterreicht.png')
                    telefon = False
                elif anruf['ergebnis'].startswith('sms'):
                    # hier wäre das normale SMS- oder das SMS-question-Icon geeignet. 
                    # Aber wir erhalten keinerlei Feedback vom Server solange die SMS wegen 
                    # ausgeschaltetem Handy noch nicht zugestellt werden konnte.
                    # Und das ist für uns eben "nicht erreicht".
                    icon = 'sms_error.png'
                    if anruf['ergebnis'] == 'sms-delivered':
                        icon = 'sms_ok.png'
                    elif anruf['ergebnis'] in ('sms-buffered', 'sms-error'):
                        icon = 'sms_error.png'
                    icons.append(icon)
            if telefon:
                icons.append('telefon.png')
    
    icons = ['<img src="/static/icons/%s">' % fn for fn in icons]
    return icons
