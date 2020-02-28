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
from lib.Config import config

import datetime, getpass

MINUTES = 5 # Maximal in dieser Häufigkeit wird nach dem SMS status geschaut
last_update = None

def send_sms(vorgang):
    import socket, os

    conf = config('sms')
    
    HOST = conf['host'] 
    PORT = conf['port']
    
    SENT=conf['sentfolder']

    if not os.path.exists(SENT):
        os.makedirs(SENT)
    sent = open(os.path.join(SENT, datetime.datetime.now().isoformat().replace(':', '-')), 'wb')
     
    userkey = conf['userkey']
    password = conf['password']
    originator = conf['number'] # diese Nummer ist bei aspsms.com für uns freigeschaltet
    
    recipients = vorgang.getTelefon().split(' / ')
    recipient = None
    for r in recipients:
        if r.startswith('01'):
            recipient = '+49'+r[1:]
            break
            
    if not recipient:
        raise ValueError('Keine Handynummer eingetragen!')
    
    recipient = recipient.replace('-', '').replace('.', '')

    text = u"Ihr Saft ist fertig. Möglichst zeitnahe Abholung bitte telefonisch absprechen. Gesamtbetrag: %s (%i Liter). Mosterei Wurst" % (getMoneyValue(vorgang.getSumme()), vorgang.getLiterzahl())
    
    text = text.replace(u'€', 'EUR')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    msgid = vorgang.ID
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
      <URLBufferedMessageNotification>http://sms.mosterei-wurst.de/feedback.py?status=buffered&amp;vorgang=</URLBufferedMessageNotification> 
      <URLDeliveryNotification>http://sms.mosterei-wurst.de/feedback.py?status=delivered&amp;vorgang=</URLDeliveryNotification>
      <URLNonDeliveryNotification>http://sms.mosterei-wurst.de/feedback.py?status=error&amp;vorgang=</URLNonDeliveryNotification>
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
        rq = requests.get('http://sms.mosterei-wurst.de/read.py', params={'vorgang': [vorgang.ID for vorgang in belegliste]}, timeout=1)
        data = rq.json()
        s = Speicher()
        for vorgang in belegliste:
            if vorgang.ID in data.keys():
                anrufe = s.getAnrufe(vorgang)
                for ts, status in data[vorgang.ID]:
                    found = False
                    for a in anrufe:
                        if a['ergebnis'] == 'sms-' + status:
                            found = True
                    if not found:
                        s.speichereAnruf(vorgang, 'sms-' + status, 'SMS-Status von ' + datetime.datetime.fromtimestamp(ts).isoformat())
    except:
        pass


def receive_status(belegliste):
    global last_update
    if not last_update or last_update < datetime.datetime.now() - datetime.timedelta(minutes = MINUTES):
        receive_status_backend(belegliste)
        last_update = datetime.datetime.now()
    else:
        print('no SMS status update needed')
    # Datenbank-Verbindung geht nicht über mehrere Threads
    #thread.start_new_thread(receive_status_backend, (belegliste,))
    

    
if __name__ == '__main__':
    from lib.Vorgang import Vorgang
    from lib.Kunde import Kunde
    import sys
    s = Speicher()
    password = getpass.getpass('Code: ')
    if not s.check_password(password):
        print ('Falscher Code!')
        sys.exit(1)

    b = Vorgang()
    b.newItem(10, '5er')
    b.newItem(10, '10er')
    b.newItem(10, 'frischsaft')
    
    b.setKunde(s.sucheKundeTelefon('7192936436')[0])
    send_sms(b)
    b.setID('0000')

    receive_status([b,])

