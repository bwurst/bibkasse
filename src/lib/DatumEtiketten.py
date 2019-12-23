# -* coding: utf8 *-
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

import io, datetime, subprocess, os

# reportlab imports
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as Canvas

fontpath = 'ressource/fonts/'

def _registerFonts():
    pdfmetrics.registerFont(TTFont("Libertine", fontpath + "LinLibertine_Re.ttf"))
    pdfmetrics.registerFont(TTFont("Libertine-Bold", fontpath + "LinLibertine_Bd.ttf"))
    pdfmetrics.registerFont(TTFont("Libertine-Italic", fontpath + "LinLibertine_It.ttf"))
    pdfmetrics.registerFont(TTFont("Libertine-BoldItalic", fontpath + "LinLibertine_BI.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu", fontpath + "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", fontpath + "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Italic", fontpath + "DejaVuSans-Oblique.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", fontpath + "DejaVuSans-BoldOblique.ttf"))

def _PageWrap(canvas):
    '''Seitenumbruch'''
    canvas.showPage()
    canvas.translate(0, A4[1])


def DatumEtiketten(count, skip, datum=datetime.date.today()):
    _registerFonts()
    fd = io.BytesIO()
    canvas = Canvas.Canvas(fd, pagesize=A4)
    canvas.setTitle('Etiketten %s' % datetime.date.today().isoformat())
    # set margins
    topmargin = 0.7*cm
    leftmargin = 0.95*cm
    
    label_width = 4.83*cm
    label_height = 2.54*cm
    
    
    # define label
    logo = 'ressource/logo.png'

    def doLabel(canvas, x, y):
        canvas.drawInlineImage(logo, x + 2.8*cm, y - 2.3*cm, width=1.64*cm, height=1.5*cm)

        canvas.setFont("DejaVu-BoldItalic", 10)
        canvas.drawString(x + 0.3*cm, y - 0.6*cm, "Abfüllung:   %s" % datum.strftime("%d.%m.%y"))
        canvas.setFont("Libertine-Bold", 9)
        canvas.drawString(x + 0.3*cm, y - 1.1*cm, "Mosterei Wurst")
        canvas.setFont("Libertine", 9)
        canvas.drawString(x + 0.3*cm, y - 1.45*cm, "Köchersberg 30")
        canvas.drawString(x + 0.3*cm, y - 1.8*cm, "71540 Murrhardt")
        canvas.drawString(x + 0.3*cm, y - 2.3*cm, "Tel.: 07192 - 936434")

    num_labels = 0
    while num_labels < count:
        # Set marker to top.
        canvas.translate(0, A4[1])
        for j in range(11):
            for i in range(4):
                if skip > 0:
                    skip -= 1
                else:
                    doLabel(canvas, leftmargin + i * label_width, -topmargin - j*label_height)
                    num_labels += 1
                    if num_labels >= count:
                        break
            if num_labels >= count:
                break
        canvas.showPage()
    canvas.save()
    return fd.getvalue()

    
if __name__ == '__main__':
    pdfdata = DatumEtiketten(count=44, skip=0)
    import tempfile
    tmp = tempfile.NamedTemporaryFile('w', delete=False)
    tmp.write(pdfdata)
    tmp.close()
    subprocess.call(['/usr/bin/xdg-open', tmp.name], shell=False, stderr=open('/dev/null', 'a'))
    
