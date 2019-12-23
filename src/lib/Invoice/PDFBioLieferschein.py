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

from lib.Invoice.InvoiceObjects import InvoiceText

# reportlab imports
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as Canvas

fontpath = 'ressource/fonts/'

def _registerFonts():
    pdfmetrics.registerFont(TTFont("DejaVu", fontpath + "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", fontpath + "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Italic", fontpath + "DejaVuSans-Oblique.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", fontpath + "DejaVuSans-BoldOblique.ttf"))



def _splitToWidth(canvas, text, width, font, size):
    '''_splitToWidth(canvas, text, width, font, size)
    Split a string to several lines of a given width.'''
    lines = []
    paras = text.split('\n')
    for para in paras:
        words = para.split(' ')
        while len(words) > 0:
            mywords = [words[0], ]
            del words[0]
            while len(words) > 0 and canvas.stringWidth(' '.join(mywords) + ' ' + words[0], font, size) <= width:
                mywords.append(words[0])
                del words[0]
            lines.append(' '.join(mywords))
    return lines


def _PageMarkers(canvas):
    """Setzt Falzmarken"""
    canvas.setStrokeColorRGB(0,0,0)
    canvas.setLineWidth(0.01*cm)
    canvas.lines([(0.3*cm,-10.5*cm,0.65*cm,-10.5*cm),
                  (0.3*cm,-21.0*cm,0.65*cm,-21.0*cm),
                  (0.3*cm,-14.85*cm,0.7*cm,-14.85*cm)]);



def _PageWrap(canvas):
    '''Seitenumbruch'''
    canvas.showPage()
    canvas.translate(0, A4[1])
    _PageMarkers(canvas)



def PDFBioLieferschein(data):
    '''Erzeugt einen Bio-Lieferschein. Übergeben wird ein dictionary, mit den Keys 
    adresse, menge, kontrollstelle, und obstart '''
    if not ('adresse' in data.keys() and
            'menge' in data.keys() and
            'kontrollstelle' in data.keys() and
            'obstart' in data.keys()
            ):
        raise ValueError('some data is missing')
    
    _registerFonts()
    from io import BytesIO
    fd = BytesIO()
    canvas = Canvas.Canvas(fd, pagesize=A4)
    canvas.setTitle('Bio-Lieferschein')
    font = 'DejaVu'
    canvas.setFont(font, 12)
    # Set marker to top.
    canvas.translate(0, A4[1])
    # Set default font size
    default_font_size = 9
    # set margins
    topmargin = 2*cm
    bottommargin = 2.2*cm
    leftmargin = 2*cm
    rightmargin = 2*cm
    
    num_pages = 1
    
    topcontent = -topmargin
    leftcontent = leftmargin
    rightcontent = A4[0] - rightmargin
    bottomcontent =  -(A4[1] - bottommargin)
    
    rightcolumn = 13*cm
    
    font_height = 0.35*cm
    line_padding = 0.1*cm
    line_height = font_height+0.1*cm
    _PageMarkers(canvas)
    
    def _Footer():
        canvas.line(leftcontent, bottomcontent, rightcontent, bottomcontent)
        canvas.setFont(font, 8)
        canvas.drawCentredString(leftcontent+((rightcontent-leftcontent)/2), bottomcontent-10, 'Mosterei Wurst · Bernd Wurst · Köchersberg 30 · 71540 Murrhardt · www.mosterei-wurst.de')
        canvas.drawCentredString(leftcontent+((rightcontent-leftcontent)/2), bottomcontent-20, 'USt-ID: DE239631414')
        canvas.drawCentredString(leftcontent+((rightcontent-leftcontent)/2), bottomcontent-30, 'Bankverbindung: Volksbank Backnang · BIC: GENODES1VBK · IBAN: DE80 6029 1120 0041 3440 06')
    
    
    font_size = 8
    x = 2.0 * cm
    canvas.y = -4.8 * cm - font_size - 1
    
    canvas.setFont(font, font_size)
    
    canvas.drawString(x, canvas.y+0.1*cm, u' Mosterei Wurst · Köchersberg 30 · 71540 Murrhardt')
    canvas.line(x, canvas.y, x + (8.5 * cm), canvas.y)
    canvas.y = canvas.y - font_size - 3
    
    font_size = 11
    x += 0.5*cm
    canvas.y -= 0.5*cm
    canvas.setFont(font, font_size)
    addresslines = data['adresse'].split('\n')
    for line in addresslines:
        canvas.drawString(x, canvas.y, line)
        canvas.y -= line_height
    
    
    font_size = default_font_size
    
    canvas.y = topcontent
    canvas.drawInlineImage("ressource/logo.png", rightcolumn, topcontent-(2*cm), width=2.19*cm, height=2*cm)
    canvas.y -= (2.5*cm)
    canvas.setFont(font+"-Bold", font_size)
    canvas.drawString(rightcolumn, canvas.y, "Mosterei Wurst")
    canvas.y -= (font_size + 5)
    canvas.setFont(font, font_size)
    canvas.drawString(rightcolumn, canvas.y, "Inh. Bernd Wurst")
    canvas.y -= (font_size + 5)
    canvas.drawString(rightcolumn, canvas.y, "Köchersberg 30")
    canvas.y -= (font_size + 5)
    canvas.drawString(rightcolumn, canvas.y, "71540 Murrhardt")
    canvas.y -= (font_size + 10)
    canvas.drawString(rightcolumn, canvas.y, "Tel: 07192-936434")
    canvas.y -= (font_size + 5)
    canvas.drawString(rightcolumn, canvas.y, "E-Mail: info@mosterei-wurst.de")
    canvas.y -= (font_size + 10)
    canvas.y = -9.5*cm
    canvas.setFont(font+'-Bold', font_size+2)
    canvas.drawString(leftcontent, canvas.y, u'Anlieferschein für Bio-Ware')

    canvas.y -= font_size + 0.2*cm
    
    font_size = default_font_size
    
    def text(message, headline = None):
        left, right = leftcontent, rightcontent
        if headline:
            canvas.setFont(font+'-Bold', font_size)
            canvas.drawString(left, canvas.y-font_height, headline)
            canvas.y -= line_height
            left, right = leftcontent+2*cm, rightcontent

        canvas.setFont(font, font_size)
        lines = _splitToWidth(canvas, message, right-left, font, font_size)
        for line in lines:
            canvas.drawString(left, canvas.y-font_height, line)
            canvas.y -= line_height
        canvas.y -= line_padding*3

    text(u"Das heute gelieferte Obst stammt ausschließlich aus der eigenen ökologischen Produktion des unten genannten Erzeugers.")
    text(data['adresse'] + u'\nKontrollstellen-Code: ' + str(data['kontrollstelle']), u'Erzeuger:')
    if not (' ' in data['menge'] or data['menge'].endswith('kg') or data['menge'].endswith('t')):
        data['menge'] += ' kg'
    obstart = []
    if 'apfel' in data['obstart'].keys() and data['obstart']['apfel']:
        obstart.append(u'Bio-Äpfel')
    if 'birne' in data['obstart'].keys() and data['obstart']['birne']:
        obstart.append(u'Bio-Birnen')
    if len(obstart) < 1:
        obstart = [u'Bio-Äpfel',u'Bio-Birnen']
    text(u"%s Bio-Obst (%s)" % (data['menge'], u' / '.join(obstart)), u"Geliefert wurden (Menge geschätzt):")
    text(u"Das Obst soll verarbeitet werden zu Fruchtsaft in Bag-in-Box-Einheiten. Der aus diesem Obst erzeugte Fruchtsaft wird vom Lieferanten anschließend wieder abgenommen.\nÖko-Kontrollnummer des Verarbeitungsbetriebs: DE-BW-003-62284-B\nZuständige Kontrollstelle des Verarbeitungsbetriebs: DE-ÖKO-003", 'Zweck der Anlieferung:')
    
    text(u'\n\n\n_________________________________________________________________________\nDatum, Unterschrift Erzeuger')
    text(u"❑ Die Lieferung erfolgte durch einen Fahrer:\n\n\n_________________________________________________________________________\nName des Fahrers, Datum, Unterschrift Fahrer (falls abweichend)")
         
    _Footer()
    
    canvas.showPage()
    canvas.save()
    pdfdata = fd.getvalue()
    return pdfdata


if __name__ == '__main__':
    data = {
            'adresse': u"Helmut Wurst\nKöchersberg 19\n71540 Murrhardt",
            'menge': '500 kg',
            'kontrollstelle': u'DE-ÖKO-003',
            'obstart': {'apfel': True, 'birne': False},
            }
    
    print (data) 
    
    pdfdata = PDFBioLieferschein(data)
    pdffile = open('test.pdf', 'w')
    pdffile.write(pdfdata)
    pdffile.close()
