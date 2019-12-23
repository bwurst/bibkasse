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

from lib.helpers import getMoneyValue
from lib.Speicher import Speicher

import datetime, getpass

def send_sms(beleg):
    import socket, os
    
    HOST = 'xml3.aspsms.com' 
    PORT = 5061 
    
    SENT='daten/sms/sent'

    CONFIG = 'daten/sms_credentials.json'
    if not os.path.exists(CONFIG):
        raise RuntimeError('Die Config-Datei existiert nicht!')
    
    import json
    configfile = open(CONFIG, 'r')
    conf = json.load(configfile)
    
    if not os.path.exists(SENT):
        os.makedirs(SENT)
    sent = open(os.path.join(SENT, datetime.datetime.now().isoformat().replace(':', '-')), 'wb')
     
    userkey = conf['userkey']
    password = conf['password']
    originator = '+497192936434' # diese Nummer ist bei aspsms.com für uns freigeschaltet
    
    recipients = beleg.getTelefon().split(' / ')
    recipient = None
    for r in recipients:
        if r.startswith('01'):
            recipient = '+49'+r[1:]
            break
            
    if not recipient:
        raise ValueError('Keine Handynummer eingetragen!')
    
    recipient = recipient.replace('-', '').replace('.', '')

    text = u"Ihr Saft ist fertig. Möglichst zeitnahe Abholung bitte telefonisch absprechen. Gesamtbetrag: %s (%i Liter). Mosterei Wurst" % (getMoneyValue(beleg.getSumme()), beleg.getLiterzahl())
    
    text = text.replace(u'€', 'EUR')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    msgid = beleg.ID
    if not msgid:
        msgid = '0000'

    CONTENT=u"""<?xml version="1.0" encoding="UTF-8"?>
    <aspsms>
      <Userkey>""" + str(userkey) +  u"""</Userkey>
      <Password>""" + str(password) + u"""</Password>
      <Originator>""" + str(originator) + u"""</Originator>
      <Recipient>
        <PhoneNumber>""" + str(recipient) + u"""</PhoneNumber>
        <TransRefNumber>""" + str(msgid) + u"""</TransRefNumber>
      </Recipient>
      <MessageData>""" + str(text) + u"""</MessageData>
      <Action>SendTextSMS</Action>
      <URLBufferedMessageNotification>http://sms.mosterei-wurst.de/feedback.py?status=buffered&amp;beleg=</URLBufferedMessageNotification> 
      <URLDeliveryNotification>http://sms.mosterei-wurst.de/feedback.py?status=delivered&amp;beleg=</URLDeliveryNotification>
      <URLNonDeliveryNotification>http://sms.mosterei-wurst.de/feedback.py?status=error&amp;beleg=</URLNonDeliveryNotification>
    </aspsms>
    """
    
    sent.write(CONTENT.encode('utf-8'))
    
    length=len(CONTENT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(b"POST /xmlsvr.asp HTTP/1.0\r\n")
    s.send(b"Content-Type: text/xml\r\n")
    s.send(("Content-Length: "+str(length)+"\r\n\r\n").encode('ascii'))
    s.send(CONTENT.encode('utf-8'))
    datarecv=s.recv(1024)
    sent.write(('''
    Reply Received: 
    '''+ str(datarecv)).encode('utf-8'))
    s.close()
    sent.close()
    
    
    
def receive_status_backend(belegliste):
    if type(belegliste) != type([]):
        belegliste = [belegliste, ]
    import requests
    try:
        rq = requests.get('http://sms.mosterei-wurst.de/read.py', params={'beleg': [beleg.ID for beleg in belegliste]}, timeout=1)
        data = rq.json()
        s = Speicher()
        for beleg in belegliste:
            if beleg.ID in data.keys():
                anrufe = s.getAnrufe(beleg)
                for ts, status in data[beleg.ID]:
                    found = False
                    for a in anrufe:
                        if a['ergebnis'] == 'sms-' + status:
                            found = True
                    if not found:
                        s.speichereAnruf(beleg, 'sms-' + status, 'SMS-Status von ' + datetime.datetime.fromtimestamp(ts).isoformat())
    except:
        pass


def receive_status(belegliste):
    receive_status_backend(belegliste)
    # Datenbank-Verbindung geht nicht über mehrere Threads
    #thread.start_new_thread(receive_status_backend, (belegliste,))
    

    
if __name__ == '__main__':
    from lib.Beleg import Beleg
    import sys
    s = Speicher()
    password = getpass.getpass('Code: ')
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)


    b = Beleg()
    b.newItem(10, '5er')
    b.newItem(10, '10er')
    b.newItem(10, 'frischsaft')
    
    b.setTelefon('07192936434 / 01719354145 / 07192936436')
    send_sms(b)
    b.setID('0000')

    receive_status([b,])

