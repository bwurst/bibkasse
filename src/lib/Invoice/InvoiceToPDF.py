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

from lib.Invoice.InvoiceObjects import InvoiceTable, InvoiceText
import re

# reportlab imports
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as Canvas


def _formatPrice(price, symbol='€'):
    '''_formatPrice(price, symbol='€'):
    Gets a floating point value and returns a formatted price, suffixed by 'symbol'. '''
    s = ("%.2f" % price).replace('.', ',')
    pat = re.compile(r'([0-9])([0-9]{3}[.,])')
    while pat.search(s):
        s = pat.sub(r'\1.\2', s)
    return s+' '+symbol

fontpath = 'ressource/fonts/'

def _registerFonts():
    pdfmetrics.registerFont(TTFont("DejaVu", fontpath + "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", fontpath + "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Italic", fontpath + "DejaVuSans-Oblique.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", fontpath + "DejaVuSans-BoldOblique.ttf"))







class PDF(object):
    # Set default font size
    default_font_size = 8
    font = 'DejaVu'
    # set margins
    topmargin = 2*cm
    bottommargin = 2.2*cm
    leftmargin = 2*cm
    rightmargin = 2*cm
    rightcolumn = 13*cm
    
    canvas = None
    num_pages = 1
    font_height = 0.3*cm
    line_padding = 0.1*cm
    line_height = font_height+0.1*cm
    
    iv = None
    
    def __init__(self):
        _registerFonts()
        from io import BytesIO
        self.fd = BytesIO()
        self.canvas = Canvas.Canvas(self.fd, pagesize=A4)
        
        self.topcontent = -self.topmargin
        self.leftcontent = self.leftmargin
        self.rightcontent = A4[0] - self.rightmargin
        self.bottomcontent =  -(A4[1] - self.bottommargin)

        self.font_size = 8
        self.x = 2.0 * cm
        self.y = -4.8 * cm - self.font_size - 1
        
        self.canvas.setFont(self.font, self.font_size)
    

    def _splitToWidth(self, text, width, font, size):
        '''_splitToWidth(canvas, text, width, font, size)
        Split a string to several lines of a given width.'''
        lines = []
        paras = text.split('\n')
        for para in paras:
            words = para.split(' ')
            while len(words) > 0:
                mywords = [words[0], ]
                del words[0]
                while len(words) > 0 and self.canvas.stringWidth(' '.join(mywords) + ' ' + words[0], font, size) <= width:
                    mywords.append(words[0])
                    del words[0]
                lines.append(' '.join(mywords))
        return lines
    
    
    def _PageMarkers(self):
        """Setzt Falzmarken"""
        self.canvas.setStrokeColor((0,0,0))
        self.canvas.setLineWidth(0.01*cm)
        self.canvas.lines([(0.3*cm,-10.5*cm,0.65*cm,-10.5*cm),
                           (0.3*cm,-21.0*cm,0.65*cm,-21.0*cm),
                           (0.3*cm,-14.85*cm,0.7*cm,-14.85*cm)]);



    
    def _partHeight(self, part):
        height = 0
        if type(part) == InvoiceText:
            left, right = self.leftcontent, self.rightcontent
            if part.urgent:
                left += 1.5*cm
                right -= 1.5*cm
                height += len(part.paragraphs) * 3 * self.line_padding
                # Rechne eine Zeile mehr für den Rahmen
                height += self.line_height
            if part.headline:
                height += (len(self._splitToWidth(part.headline, right-left, self.font+'-Bold', self.default_font_size+1)) * self.line_height) + self.line_padding
            for para in part.paragraphs:
                height += (len(self._splitToWidth(para, right-left, self.font, self.default_font_size)) * self.line_height) + self.line_padding
        elif type(part) == InvoiceTable:
            # Eine Zeile plus 2 mal line_padding für Tabellenkopf
            height = self.line_height + 2 * self.line_padding
            # Wenn nur ein Element (plus Summen) hin passt, reicht uns das
            el = part.entries[0]
            # Die Abstände oben und unten
            height += 2 * self.line_padding
            # Die Breite ist konservativ
            if el['type'] == 'title':
                height += self.line_height + 0.2*cm
            else:
                height += self.line_height*len(self._splitToWidth(el['subject'], 9.3*cm, self.font, self.font_size))
            if 'desc' in el and el['desc'] != '':
                height += self.line_height * len(self._splitToWidth(el['desc'], 11*cm, self.font, self.font_size))
            if part.vatType == 'net':
                # Eine Zeile mehr
                height += self.line_height + self.line_padding
            # Für die MwSt-Summen
            height += (self.line_height + self.line_padding) * len(part.vat)
            # Für den Rechnungsbetrag
            height += self.line_height + self.line_padding
        return height


    def _tableHead(self, part):
        self.canvas.setFont(self.font, self.font_size)
        self.canvas.drawString(self.leftcontent+(0.1*cm), self.y-self.line_height+self.line_padding, 'Anz.')
        self.canvas.drawString(self.leftcontent+(2.1*cm), self.y-self.line_height+self.line_padding, 'Beschreibung')
        if len(part.vat) == 1:
            self.canvas.drawRightString(self.leftcontent+(14.3*cm), self.y-self.line_height+self.line_padding, 'Einzelpreis')
        else:
            self.canvas.drawRightString(self.leftcontent+(13.3*cm), self.y-self.line_height+self.line_padding, 'Einzelpreis')
        self.canvas.drawRightString(self.leftcontent+(16.8*cm), self.y-self.line_height+self.line_padding, 'Gesamtpreis')
        self.canvas.setLineWidth(0.01*cm)
        self.canvas.line(self.leftcontent, self.y - self.line_height, self.rightcontent, self.y - self.line_height)
        self.y -= self.line_height + 0.02*cm
    
    
    def _PageWrap(self):
        '''Seitenumbruch'''
        self.num_pages += 1
        self.canvas.setFont(self.font, self.default_font_size-2)
        self.canvas.drawRightString(self.rightcontent, self.bottomcontent + self.line_padding, 'Fortsetzung auf Seite %i' % self.num_pages)
        self.canvas.showPage()
        self.basicPage()
        self.y = self.topcontent - self.font_size
        self.canvas.setFillColor((0,0,0))
        self.canvas.setFont(self.font, self.font_size-2)
        self.canvas.drawCentredString(self.leftcontent + (self.rightcontent - self.leftcontent) / 2, self.y, '- Seite %i -' % self.num_pages)
  
    
    def _Footer(self):
        self.canvas.setStrokeColor((0, 0, 0))
        self.canvas.setFillColor((0,0,0))
        self.canvas.line(self.leftcontent, self.bottomcontent, self.rightcontent, self.bottomcontent)
        self.canvas.setFont(self.font, 8)
        self.canvas.drawCentredString(self.leftcontent+((self.rightcontent-self.leftcontent)/2), self.bottomcontent-10, 'Mosterei Wurst · Bernd Wurst · Köchersberg 30 · 71540 Murrhardt · www.mosterei-wurst.de')
        self.canvas.drawCentredString(self.leftcontent+((self.rightcontent-self.leftcontent)/2), self.bottomcontent-20, 'USt-ID: DE239631414')
        self.canvas.drawCentredString(self.leftcontent+((self.rightcontent-self.leftcontent)/2), self.bottomcontent-30, 'Bankverbindung: Volksbank Backnang · BIC: GENODES1VBK · IBAN: DE80 6029 1120 0041 3440 06')
    
    def basicPage(self):
        # Set marker to top.
        self.canvas.translate(0, A4[1])

        self._PageMarkers()
        self._Footer()
    


    def addressBox(self):
        self.canvas.drawString(self.x, self.y+0.1*cm, ' Mosterei Wurst · Köchersberg 30 · 71540 Murrhardt')
        self.canvas.line(self.x, self.y, self.x + (8.5 * cm), self.y)
        self.y = self.y - self.font_size - 3
        
        font_size = 11
        x = self.x + 0.5*cm
        self.y -= 0.5*cm
        self.canvas.setFont(self.font, font_size)
        for line in self.iv.addresslines:
            self.canvas.drawString(x, self.y, line)
            self.y -= font_size * 0.03527 * cm * 1.2


    def firstPage(self):
        self.basicPage()
        self.addressBox()
        
        self.y = self.topcontent
        self.canvas.drawInlineImage("ressource/logo.png", self.rightcolumn, self.topcontent-(2*cm), width=2.19*cm, height=2*cm)
        self.y -= (2.5*cm)
        self.canvas.setFont(self.font+"-Bold", self.font_size)
        self.canvas.drawString(self.rightcolumn, self.y, "Mosterei Wurst")
        self.y -= (self.font_size + 5)
        self.canvas.setFont(self.font, self.font_size)
        self.canvas.drawString(self.rightcolumn, self.y, "Inh. Bernd Wurst")
        self.y -= (self.font_size + 5)
        self.canvas.drawString(self.rightcolumn, self.y, "Köchersberg 30")
        self.y -= (self.font_size + 5)
        self.canvas.drawString(self.rightcolumn, self.y, "71540 Murrhardt")
        self.y -= (self.font_size + 10)
        self.canvas.drawString(self.rightcolumn, self.y, "Tel: 07192-936434")
        self.y -= (self.font_size + 5)
        self.canvas.drawString(self.rightcolumn, self.y, "E-Mail: info@mosterei-wurst.de")
        self.y -= (self.font_size + 10)
        self.y = -9.5*cm


    def title(self, title):
        self.canvas.setTitle(title)
        self.canvas.drawString(self.leftcontent, self.y, title)


    def renderRechnung(self, iv):
        self.iv = iv
        self.firstPage()
        self.canvas.setFont(self.font+'-Bold', self.font_size+3)
        if self.iv.tender:
            self.title('Angebot')
        else:
            self.title('Rechnung')

        if self.iv.tender:
            self.canvas.setFont(self.font, self.font_size)
            self.canvas.drawString(self.rightcolumn, self.y, "Erstellungsdatum:")
            self.canvas.drawRightString(self.rightcontent, self.y, "%s" % self.iv.date.strftime('%d. %m. %Y'))
            self.y -= (self.font_size + 0.1*cm)
        else:
            self.canvas.setFont(self.font+'-Bold', self.font_size)
            self.canvas.drawString(self.rightcolumn, self.y, "Bei Fragen bitte immer angeben:")
            self.y -= (self.font_size + 0.2*cm)
            self.canvas.setFont(self.font, self.font_size)
            self.canvas.drawString(self.rightcolumn, self.y, "Rechnungsdatum:")
            self.canvas.drawRightString(self.rightcontent, self.y, "%s" % self.iv.date.strftime('%d. %m. %Y'))
            self.y -= (self.font_size + 0.1*cm)
            self.canvas.drawString(self.rightcolumn, self.y, "Rechnungsnummer:")
            self.canvas.drawRightString(self.rightcontent, self.y, "%s" % iv.id)
            self.y -= (self.font_size + 0.1*cm)
        if self.iv.customerno:
            self.canvas.drawString(self.rightcolumn, self.y, "Kundennummer:")
            self.canvas.drawRightString(self.rightcontent, self.y, "%s" % self.iv.customerno)
            self.y -= (self.font_size + 0.5*cm)
        self.canvas.setFont(self.font, self.font_size)
        
        if self.iv.salutation:
            self.canvas.drawString(self.leftcontent, self.y, self.iv.salutation)
            self.y -= self.font_size + 0.2*cm
            introText = 'hiermit stellen wir Ihnen die nachfolgend genannten Leistungen in Rechnung.'
            if self.iv.tender:
                introText = 'hiermit unterbreiten wir Ihnen folgendes Angebot.'
            intro = self._splitToWidth(introText, self.rightcontent - self.leftcontent, self.font, self.font_size)
            for line in intro:
                self.canvas.drawString(self.leftcontent, self.y, line)
                self.y -= self.font_size + 0.1*cm
            self.y -= self.font_size + 0.1*cm
        
        
        font_size = self.default_font_size
        for part in self.iv.parts:
            if self.y - self._partHeight(part) < (self.bottomcontent + (0.5*cm)):
                self._PageWrap()
                self.y = self.topcontent - self.font_size - self.line_padding*3
            if type(part) == InvoiceTable:
                  
                left = self.leftcontent
                right = self.rightcontent
                self._tableHead(part)
                temp_sum = 0.0
                odd = True
                for el in part.entries:
                    if el['type'] == 'title':
                        self.y -= self.line_padding + 0.2*cm
                        self.canvas.setFillColorRGB(0, 0, 0)
                        self.canvas.setFont(self.font+'-Italic', font_size)
                        self.canvas.drawString(left, self.y-self.font_height, el['title'])
                        self.canvas.setFont(self.font, font_size)
                        self.y -= self.line_height + self.line_padding
                    else:
                        subject = []
                        if len(part.vat) == 1:
                            subject = self._splitToWidth(el['subject'], 9.8*cm, self.font, font_size)
                        else:
                            subject = self._splitToWidth(el['subject'], 8.8*cm, self.font, font_size)
                        desc = []
                        if 'desc' in el and el['desc'] != '':
                            desc = self._splitToWidth(el['desc'], 14.0*cm, self.font, font_size)
                        need_lines = len(subject) + len(desc)
                        # need page wrap?
                        if self.y - (need_lines+1 * (self.line_height + self.line_padding)) < (self.bottomcontent + 1*cm):
                            self.canvas.setFont(self.font + '-Italic', font_size)
                            # Zwischensumme
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Zwischensumme:')
                            self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(temp_sum))
                            # page wrap
                            self._PageWrap()
                            self.y = self.topcontent - font_size - self.line_padding*3
                            # header
                            self._tableHead(part)
                            self.y -= self.line_padding * 3
                            odd=True
                            # übertrag
                            self.canvas.setFont(self.font + '-Italic', font_size)
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Übertrag:')
                            self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(temp_sum))
                            self.y -= self.font_height + self.line_padding * 3
                            self.canvas.setFont(self.font, self.default_font_size)
                            
                        # Zwischensumme (inkl. aktueller Posten)
                        temp_sum += el['total']
    
                        
                        # draw the background
                        if not odd:
                            self.canvas.setFillColorRGB(0.9, 0.9, 0.9)
                        else:
                            self.canvas.setFillColorRGB(1, 1, 1)
                        self.canvas.rect(left, self.y - (need_lines*self.line_height)-(2*self.line_padding), height = (need_lines*self.line_height)+(2*self.line_padding), width = right-left, fill=1, stroke=0)
                        self.canvas.setFillColorRGB(0, 0, 0)
                        self.y -= self.line_padding
                        self.canvas.drawRightString(left+1.1*cm, self.y-self.font_height, '%.0f' % el['count'])
                        self.canvas.drawString(left+1.2*cm, self.y-self.font_height, el['unit'])
                        self.canvas.drawString(left+2.2*cm, self.y-self.font_height, subject[0])
                        if len(part.vat) == 1:
                            self.canvas.drawRightString(left+14.3*cm, self.y-self.font_height, _formatPrice(el['price']))
                        else:
                            self.canvas.drawRightString(left+13.3*cm, self.y-self.font_height, _formatPrice(el['price']))
                            self.canvas.drawString(left+13.7*cm, self.y-self.font_height, str(part.vat[el['vat']][1]))
                        if el['tender']:  
                            self.canvas.drawRightString(left+16.8*cm, self.y-self.font_height, 'eventual')
                        else:
                            self.canvas.drawRightString(left+16.8*cm, self.y-self.font_height, _formatPrice(el['total']))
                        subject = subject[1:]
                        x = 1
                        for line in subject:
                            self.canvas.drawString(left+2.2*cm, self.y-(x * self.line_height)-self.font_height, line)
                            x += 1
                        for line in desc:
                            self.canvas.drawString(left+2.2*cm, self.y-(x * self.line_height)-self.font_height, line)
                            x += 1
                        odd = not odd
                        self.y -= (need_lines * self.line_height) + self.line_padding
                if part.summary:
                    need_lines = 5
                    if self.y - (need_lines+1 * (self.line_height + self.line_padding)) < (self.bottomcontent + 1*cm):
                        self.canvas.setFont(self.font + '-Italic', font_size)
                        # Zwischensumme
                        self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Zwischensumme:')
                        self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(temp_sum))
                        # page wrap
                        self._PageWrap()
                        self.y = self.topcontent - font_size - self.line_padding*3
                        # header
                        self._tableHead(part)
                        odd=True
                        # übertrag
                        self.canvas.setFont(self.font + '-Italic', font_size)
                        self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Übertrag:')
                        self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(temp_sum))
                        self.y -= self.font_height + self.line_padding
                    self.y -= (0.3*cm)
                    if part.vatType == 'gross':
                        self.canvas.setFont(self.font+'-Bold', font_size)
                        if self.iv.tender or not self.iv.official:
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Gesamtbetrag:')
                        else:
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Rechnungsbetrag:')
                        self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(part.sum))
                        if self.iv.official:
                            self.canvas.setFont(self.font, font_size)
                            self.y -= self.line_height + self.line_padding
                            summaries = []
                            if len(part.vat) == 1 and list(part.vat.keys())[0] == 0.0:
                                self.canvas.drawString(left, self.y-self.font_height, 'Diese Rechnung enthält durchlaufende Posten ohne Berechnung von MwSt.')
                                self.y -= self.line_height
                            else:
                                if len(part.vat) == 1:
                                    vat = list(part.vat.keys())[0]
                                    if iv.tender:
                                        summaries.append(('Im Gesamtbetrag sind %.1f%% MwSt enthalten:' % (vat*100), _formatPrice((part.sum/(vat+1))*vat)))
                                    else:
                                        summaries.append(('Im Rechnungsbetrag sind %.1f%% MwSt enthalten:' % (vat*100), _formatPrice((part.sum/(vat+1))*vat)))
                                else:
                                    for vat, vatdata in part.vat.items():
                                        if vat > 0:
                                            summaries.append(('%s: Im Teilbetrag von %s sind %.1f%% MwSt enthalten:' % (vatdata[1], _formatPrice(vatdata[0]), vat*100), _formatPrice((vatdata[0]/(vat+1))*vat)))
                                        else:
                                            summaries.append(('%s: Durchlaufende Posten ohne Berechnung von MwSt.' % (vatdata[1]), 0.0))
                            summaries.append(('Nettobetrag:', _formatPrice(part.sum - (part.sum/(vat+1))*vat)))
                            summaries.sort()
                            for line in summaries:
                                self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, line[0])
                                if line[1]:
                                    self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, line[1])
                                self.y -= self.line_height
                    elif len(part.vat) == 1 and part.vatType == 'net':
                        self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Nettobetrag:')
                        self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(part.sum))
                        self.y -= self.line_height
                        summaries = []
                        if list(part.vat.keys())[0] == 0.0:
                            self.canvas.drawString(left, self.y-self.font_height, 'Diese Rechnung enthält durchlaufende Posten ohne Berechnung von MwSt.')
                            self.y -= self.line_height
                        else:
                            if len(part.vat) == 1:
                                vat = list(part.vat.keys())[0]
                                summaries.append(('zzgl. %.1f%% MwSt:' % (vat*100), _formatPrice(vat*part.sum)))
                            else:
                                for vat, vatdata in part.vat.items():
                                    summaries.append(('zzgl. %.1f%% MwSt (%s):' % (vat*100, vatdata[1]), _formatPrice(vat*vatdata[0])))
                        summaries.sort()
                        for line in summaries:
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, line[0])
                            self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, line[1])
                            self.y -= self.line_height
                        sum = 0
                        for vat, vatdata in part.vat.items():
                            sum += (vat+1)*vatdata[0]
                        self.canvas.setFont(self.font+'-Bold', font_size)
                        if self.iv.tender:
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Gesamtbetrag:')
                        else:
                            self.canvas.drawRightString(left + 14.5*cm, self.y-self.font_height, 'Rechnungsbetrag:')
                        self.canvas.drawRightString(left + 16.8*cm, self.y-self.font_height, _formatPrice(sum))
                        self.canvas.setFont(self.font, font_size)
                        self.y -= self.line_height + self.line_padding
            elif type(part) == InvoiceText:
                my_font_size = font_size
                self.canvas.setFont(self.font, my_font_size)
                left, right = self.leftcontent, self.rightcontent
                firsttime = True
                headlines = []
                if part.urgent:
                    left += 1.5*cm
                    right -= 1.5*cm
                if part.headline:
                    headlines = self._splitToWidth(part.headline, right-left, self.font, my_font_size)
                for para in part.paragraphs:
                    lines = self._splitToWidth(para, right-left, self.font, my_font_size)
                    if part.urgent:
                        need_height = len(lines) * self.line_height
                        if len(headlines) > 0:
                            need_height += len(headlines) * (self.line_height + 1) + self.line_padding
                        self.canvas.setFillColorRGB(0.95, 0.95, 0.95)
                        self.canvas.rect(left-0.5*cm, self.y - (need_height+(6*self.line_padding)), height = need_height+(6*self.line_padding), width = right-left+1*cm, fill=1, stroke=1)
                        self.canvas.setFillColorRGB(0, 0, 0)
                        self.y -= self.line_padding*3
                    if part.headline and firsttime:
                        firsttime = False
                        self.canvas.setFont(self.font+'-Bold', my_font_size+1)
                        for line in headlines:
                            self.canvas.drawString(left, self.y-(self.font_height+1), line)
                            self.y -= self.line_height + 1
                        self.y -= self.line_padding
                        self.canvas.setFont(self.font, my_font_size)
                    for line in lines:
                        self.canvas.drawString(left, self.y-self.font_height, line)
                        self.y -= self.line_height
                    self.y -= self.line_padding*3
                left, right = self.leftcontent, self.rightcontent
            else:
                raise NotImplementedError("Cannot handle part of type %s" % type(part))
            self.y -= (0.5*cm)
          
        self.canvas.showPage()
        self.canvas.save()
        pdfdata = self.fd.getvalue()
        return pdfdata


def InvoiceToPDF(iv):
    pdf = PDF()
    return pdf.renderRechnung(iv)




if __name__ == '__main__':
    import datetime
    from lib.Beleg import Beleg
    from lib.BelegRechnung import BelegRechnung
    beleg = Beleg()
    for n in range(30):
        dummy = beleg.newItem(n, None, 'Dummy #%i' % n, 0.01, 0, 'Stk', False, 19.0, 0.0)
    beleg.kunde.setName('Müller')
    beleg.setAdresse('Testkunde\nTeststraße 1\nTestort')
    beleg.setRechnungsdaten('2014-12-10', '2014-9999')
    beleg.setZeitpunkt(datetime.datetime.now())
    filename = BelegRechnung(beleg)
    print (filename)



