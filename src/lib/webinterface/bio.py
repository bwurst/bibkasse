# -* coding: utf-8 *-

import web

from lib.Speicher import Speicher

from . import check_authenticated, get_authtoken
from . import html

class bio_lieferschein:
    
    def GET(self):
        check_authenticated()
        s = Speicher(authtoken=get_authtoken())
        biokunden = s.getBioKunden()
        options = ''
        for k in biokunden:
            options += u'<option value="%s">%s</option>\n' % (k['kontrollstelle'], k['adresse'])
        content = u'''
<h4>Bio-Anlieferschein erstellen</h4>
<div class="bio_lieferschein_form">
<form method="post" enctype="multipart/form-data" >
  <p><label for="biokunden">Bisherige Bio-Kunden:</label> <select name="biokunden" id="biokunden"><option value="0">- Neuer Kunde -</option>
    ''' + options + u'''
    </select></p>
  <p><label for="adresse">Adresse:</label> <textarea name="adresse" id="adresse" cols="30" rows="4"></textarea></p>
  <p><label for="kontrollstelle">Kontrollstellen-Code:</label> <input type="text" name="kontrollstelle" id="kontrollstelle"></p>
  <p><label for="menge">Obst-Menge:</label> <input type="text" name="menge" id="menge"></p>
  <p>Obst-Art: <input type="checkbox" name="obst" value="apfel" id="obst_apfel" checked="checked"> <label for="obst_apfel">Bio-Äpfel</label>   <input type="checkbox" name="obst" value="birne" id="obst_birne"> <label for="obst_birne" checked="checked">Bio-Birnen</label></p>
  <p><label for="zertifikat">Bio-Zertifikat hochladen (PDF):</label> <input type="file" name="zertifikat" id="zertifikat"></p>
  <p class="submit"><input type="submit" name="submit" value="Lieferschein erstellen" /></p> 
</form>
</div>'''
        return html.page(u"Bio-Lieferschein", content)

    def POST(self):
        from lib.BioLieferschein import BioLieferschein
        check_authenticated()
        s = Speicher(authtoken=get_authtoken())
        postdata = web.input(adresse='', kontrollstelle='', menge='', obst=[], zertifikat={})
        data = {
            'adresse': postdata['adresse'].replace("\r\n", "\n"),
            'menge': postdata['menge'],
            'kontrollstelle': postdata['kontrollstelle'],
            'obstart': {},
            }
        for key in postdata['obst']:
            data['obstart'][key]= True
        s.speichereBioLieferschein(data)
        pdffile = BioLieferschein(data)
        print (pdffile)
        return pdffile
        
        
