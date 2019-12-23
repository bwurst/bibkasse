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

import os

from lib.Invoice.PDFBioLieferschein import PDFBioLieferschein
from lib.Speicher import Speicher

from datetime import date

PFAD = 'daten/bio/lieferschein'


def findeNaechsteNummer():
    files = sorted(list(os.listdir(PFAD)))
    try:
        max = int(files[-1].replace('.pdf', '').rsplit('-')[-1])
    except:
        max = 0
    return '%04i-%03i' % (date.today().year, max + 1)


def BioLieferschein(data, filename = None):
    if not ('adresse' in data.keys() and
            'menge' in data.keys() and
            'kontrollstelle' in data.keys() and
            'obstart' in data.keys()
            ):
        raise ValueError('some data is missing')
    pdfdata = PDFBioLieferschein(data)
    if not os.path.exists(PFAD):
        os.makedirs(PFAD)
    if not filename:
        nummer = findeNaechsteNummer()    
        filename = 'BIO-LS-%s.pdf' % nummer
    filename = "%s/%s" % (PFAD, filename) 
    if os.path.exists(filename):
        raise RuntimeError('Eine Datei mit diesem Namen existiert bereits!')
    f = open(filename, "wb")
    f.write(pdfdata)
    f.close()
    return filename


