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

PFAD_DB = 'daten/sqlite'
ALTE_KUNDEN = 'daten/altekunden.txt'
ALTE_BIOKUNDEN = 'daten/altebiokunden.txt'
ALTE_RECHNUNGSADRESSEN = 'daten/alterechnungsadressen.txt'

KEYFILE = 'daten/keyfile.dat'
KEY_VALIDATE_FILE = 'daten/key_validate.dat'
OLD_CODEFILE = 'daten/pincode'
USERS_FILE = 'daten/users.xml'

VORGANG_FIELDLIST = "id,handle,version,timestamp,zeitpunkt,originale,user,kunde,name,adresse,abholung,telefon,paletten,rechnungsnummer,rechnungsdatum,zahlung,bezahlt,summe,liter,manuelle_liter,bio,bio_kontrollstelle,bio_lieferant,bio_lieferschein,status"
AUFTRAG_FIELDLIST = "handle, version, currentversion, timestamp, user, kunde, erledigt, abholung, quelle, obst, obstmenge, obstart, angeliefert, lieferart, gbcount, kennz, gebrauchte, neue, neue3er, neue5er, neue10er, sonstiges, frischsaft, telefon, zeitpunkt, status, anmerkungen, bio, bio_lieferschein"

from lib.Vorgang import Vorgang
from lib.Kunde import Kunde
from lib.Auftrag import Auftrag, StatusOffen

import os, datetime
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring

import sqlite3

import time 

import json
import base64
from hashlib import sha256
from Crypto.Cipher import AES

from lib.EncFSLoader import EncFSLoader

class SQLiteSpeicherBackend(object):
    __key = None
    __currentuser = {}
    
    def __init__(self, year = None, createnew = False, dbpath = None):
        if not dbpath:
                dbpath = PFAD_DB
        self.storage_location = dbpath
        self.loaded = False
        self.year = year
        if not year:
            self.year = str(datetime.date.today().year)
        self.createnew = createnew or (self.year == str(datetime.date.today().year))
        if (self.is_unlocked() and 
            not self.createnew and 
            not os.path.exists(os.path.join(dbpath, '%s.sqlite' % self.year))):
            raise ValueError('Keine Daten für %s' % self.year)
           
        self.encfs = EncFSLoader()
        self.dbconn = None
        self.db = None
        self.dbconn_kunden = None
        self.db_kunden = None
            
    def initialize(self):
        assert self.is_unlocked(), "initialize() called too early"
        self.encfs.mount(self.storage_location, self.__class__.__key)
        if not os.path.exists(os.path.join(self.storage_location, '%s.sqlite' % self.year)):
            if self.createnew:
                print ('Datenbank für %s wird erstellt.' % self.year)
            else:
                raise ValueError('Keine Daten für %s' % self.year)
        self.openDB(self.year)

    def openDB(self, year = None):
        if not year:
            year = self.year
        existing = os.path.exists(os.path.join(self.storage_location, '%s.sqlite' % year))
        if self.dbconn:
            print ("double call")
            return
        if not existing and not self.encfs.mounted:
            raise ValueError('storage not unlocked!')
        self.dbconn = sqlite3.connect(os.path.join(self.storage_location, '%s.sqlite' % year), check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES) # @UndefinedVariable
        self.dbconn.row_factory = sqlite3.Row # @UndefinedVariable
        self.db = self.dbconn.cursor()
        if not existing:
            print ('initializing database: '+os.path.join(self.storage_location, '%s.sqlite' % year))
            self.newDB()
        existing = os.path.exists(os.path.join(self.storage_location, 'kunden.sqlite'))
        if self.dbconn_kunden:
            print ("double call")
            return
        if not existing and not self.encfs.mounted:
            raise ValueError('storage not unlocked!')
        self.dbconn_kunden = sqlite3.connect(os.path.join(self.storage_location, 'kunden.sqlite'), check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES) # @UndefinedVariable
        self.dbconn_kunden.row_factory = sqlite3.Row # @UndefinedVariable
        self.db_kunden = self.dbconn_kunden.cursor()
        if not existing:
            print ('initializing database: '+os.path.join(self.storage_location, 'kunden.sqlite'))
            self.newKundenDB()
        self.checkDBchanges()


    def delete_column_from_table(self, table, column):
        self.db.execute('PRAGMA table_info("%s")' % (table,))
        rows = self.db.fetchall()
        field_decl = []
        columns = []
        for row in rows:
            if row['name'] != column:
                columns.append(row['name'])
                pk = ''
                if row['pk'] == 1:
                    pk = 'PRIMARY KEY'
                    if row['type'] == 'INTEGER':
                        pk += ' AUTOINCREMENT'
                null = 'NULL'
                if row['notnull'] == 1:
                    null = 'NOT NULL'
                default = ''
                if row['dflt_value']:
                    default = 'DEFAULT %s' % row['dflt_value']
                field_decl.append('"%s" %s %s %s %s' % (row['name'], row['type'], pk, null, default))
        create_stmt = 'CREATE TABLE "%s_temp" (%s)' % (table, ',\n'.join(field_decl))
        self.db.execute(create_stmt)
        self.db.execute('INSERT INTO "%s_temp" SELECT %s FROM "%s"' % (table, ','.join(columns), table))
        self.db.execute('DROP TABLE "%s"' % (table,))
        self.db.execute('ALTER TABLE "%s_temp" RENAME TO "%s"' % (table, table))


    def checkDBchanges(self):
        rename_beleg_to_vorgang = False
        self.db.execute('''PRAGMA table_info("posten")''')
        rows = self.db.fetchall()
        steuersatz = False
        datum = False
        for row in rows:
            if row['name'] == "datum":
                datum = True
            if row['name'] == "steuersatz":
                steuersatz = True
        if not datum:
            self.db.execute('''ALTER TABLE "posten" ADD COLUMN "datum" DATE''')
            self.db.execute('''UPDATE "posten" SET datum=(SELECT DATE(zeitpunkt) FROM vorgang WHERE id=posten.vorgang)''')
            self.dbconn.commit()
        if not steuersatz:
            self.db.execute('''ALTER TABLE "posten" ADD COLUMN "steuersatz" FLOAT''')
            self.db.execute('''UPDATE "posten" SET steuersatz=NULL''')
            self.dbconn.commit()
        
        self.db.execute('''PRAGMA table_info("vorgang")''')
        rows = self.db.fetchall()
        if not rows:
            # Änderung von "beleg" auf "vorgang" #FIXME
            self.db.execute('''ALTER TABLE "beleg" RENAME TO "vorgang"''')
            self.db.execute('''ALTER TABLE "posten" ADD COLUMN "vorgang" INTEGER NOT NULL''')
            self.db.execute('''UPDATE "posten" SET "vorgang"="beleg"''')
            self.delete_column_from_table("posten", "beleg")
            self.dbconn.commit()
            rename_beleg_to_vorgang = True
        self.db.execute('''PRAGMA table_info("vorgang")''')
        rows = self.db.fetchall()
        telefon = False
        currentversion = False
        abgeholt = False
        bio = False
        bio_kontrollstelle = False
        bio_lieferant = False
        bio_lieferschein = False
        kunde = False
        originale = False
        for row in rows:
            if row['name'] == "telefon":
                telefon = True
            if row['name'] == "abgeholt":
                abgeholt = True
            if row['name'] == "currentversion":
                currentversion = True
            if row['name'] == "bio":
                bio = True
            if row['name'] == "bio_kontrollstelle":
                bio_kontrollstelle = True
            if row['name'] == "bio_lieferant":
                bio_lieferant = True
            if row['name'] == "bio_lieferschein":
                bio_lieferschein = True
            if row['name'] == "kunde":
                kunde = True
            if row['name'] == 'originale':
                originale = True
        if not telefon:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "telefon" VARCHAR''')
        if not abgeholt:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "abgeholt" BOOL DEFAULT 0''')
            self.db.execute('''UPDATE "vorgang" SET abgeholt=1 WHERE (zahlung='bar' AND bezahlt=1) OR zahlung='ueberweisung' ''')
            self.dbconn.commit()
        if not currentversion:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "currentversion" BOOL DEFAULT FALSE''')
            self.db.execute('''UPDATE "vorgang" SET currentversion=(SELECT version==(SELECT max(version) FROM vorgang WHERE handle=outer.handle) FROM "vorgang" "outer" WHERE outer.id=vorgang.id)''')
            self.dbconn.commit()
        if not bio:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "bio" BOOL DEFAULT 0''')
        if not bio_kontrollstelle:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "bio_kontrollstelle" VARCHAR''')
        if not bio_lieferant:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "bio_lieferant" TEXT''')
        if not bio_lieferschein:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "bio_lieferschein" VARCHAR''')
        if not kunde:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "kunde" INTEGER''')
        if not originale:
            self.db.execute('''ALTER TABLE "vorgang" ADD COLUMN "originale" VARCHAR''')
            
        
        self.db.execute('''PRAGMA table_info("anruf")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "anruf" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                     "vorgang" VARCHAR NOT NULL,
                                                     "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                     "nummer" VARCHAR NOT NULL,
                                                     "ergebnis" VARCHAR,
                                                     "bemerkung" VARCHAR)''')
        elif rename_beleg_to_vorgang:
            self.db.execute('''ALTER TABLE "anruf" ADD COLUMN "vorgang"''')
            self.db.execute('''UPDATE "anruf" SET "vorgang"="beleg"''')
            self.delete_column_from_table("anruf", "beleg")
            self.dbconn.commit()
        self.db.execute('''PRAGMA table_info("kassenbeleg")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "kassenbeleg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                           "vorgang" VARCHAR NULL,
                                                           "vorgang_version" VARCHAR NULL,
                                                           "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                           "redatum" DATE NULL,
                                                           "renr" VARCHAR NULL, 
                                                           "type" VARCHAR NOT NULL, 
                                                           "tse_processtype" VARCHAR NULL, 
                                                           "tse_processdata" VARCHAR NULL,
                                                           "tse_time_start" INTEGER NULL,
                                                           "tse_time_end" INTEGER NULL,
                                                           "tse_trxnum" VARCHAR NULL,
                                                           "tse_serial" VARCHAR NULL,
                                                           "tse_sigcounter" INTEGER NULL,
                                                           "tse_signature" VARCHAR NULL,
                                                           "json_kunde" TEXT NULL,
                                                           "json_posten" TEXT NULL,
                                                           "json_summen" TEXT NULL,
                                                           "json_zahlungen" TEXT NULL,
                                                           "referenz" VARCHAR NULL,
                                                           "brutto" BOOL NULL,
                                                           "kassenbewegung" FLOAT NULL,
                                                           "bemerkung" VARCHAR)''')
        else:
            referenz = False
            for r in rows:
                if r['name'] == 'referenz':
                    referenz = True
            if not referenz:
                self.db.execute('''ALTER TABLE "kassenbeleg" ADD COLUMN "referenz" VARCHAR NULL''')
        self.db.execute('''PRAGMA table_info("abschluss")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "abschluss" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                         "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                         "ersterbeleg" INT NULL,
                                                         "letzterbeleg" INT NULL,
                                                         "summe_brutto" FLOAT NULL,
                                                         "summe_netto" FLOAT NULL,
                                                         "summe_mwst" FLOAT NULL,
                                                         "summe_bar" FLOAT NULL,
                                                         "summe_transit" FLOAT NULL,
                                                         "kassenstand" FLOAT NULL,
                                                         "bemerkung" VARCHAR)''')
        else:
            transit = False
            for r in rows:
                if r['name'] == 'summe_transit':
                    transit = True
            if not transit:
                self.db.execute('''ALTER TABLE "abschluss" ADD COLUMN "summe_transit" FLOAT NULL''')
        self.db.execute('''PRAGMA table_info("zahlung")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "zahlung" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                       "vorgang" VARCHAR NOT NULL,
                                                       "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                       "tse_trxnum" INTEGET NULL,
                                                       "zahlart" VARCHAR NOT NULL,
                                                       "betrag" FLOAT,
                                                       "gegeben" FLOAT,
                                                       "zurueck" FLOAT,
                                                       "bemerkung" VARCHAR)''')
        elif rename_beleg_to_vorgang:
            self.db.execute('''ALTER TABLE "zahlung" ADD COLUMN "vorgang" INTEGER NOT NULL''')
            self.db.execute('''UPDATE "zahlung" SET "vorgang"="beleg"''')
            self.delete_column_from_table("zahlung", "beleg")
            self.dbconn.commit()
        trxnum = False
        gegeben = False
        for row in rows:
            if row['name'] == "tse_trxnum":
                trxnum = True
            if row['name'] == "gegeben":
                gegeben = True
        if not trxnum:
            self.db.execute('''ALTER TABLE "zahlung" ADD COLUMN "tse_trxnum" INTEGER''')
        if not gegeben:
            self.db.execute('''ALTER TABLE "zahlung" ADD COLUMN "gegeben" FLOAT''')
            self.db.execute('''ALTER TABLE "zahlung" ADD COLUMN "zurueck" FLOAT''')

        self.db.execute('''PRAGMA table_info("bio_lieferschein")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "bio_lieferschein" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                                "adresse" TEXT NOT NULL,
                                                                "kontrollnummer" VARCHAR,
                                                                "kontrollstelle" VARCHAR,
                                                                "menge" VARCHAR,
                                                                "obstart" VARCHAR,
                                                                "anlieferdatum" DATE,
                                                                "produktionsdatum" DATE,
                                                                "abholdatum" DATE)''')
        else:
            anlieferdatum = False
            for row in rows:
                if row['name'] == 'anlieferdatum':
                    anlieferdatum = True
            kunde = False
            for row in rows:
                if row['name'] == 'kunde':
                    kunde = True
            if not anlieferdatum:
                self.db.execute('''ALTER TABLE "bio_lieferschein" ADD COLUMN "anlieferdatum" DATE''')
                self.db.execute('''ALTER TABLE "bio_lieferschein" ADD COLUMN "produktionsdatum" DATE''')
                self.db.execute('''ALTER TABLE "bio_lieferschein" ADD COLUMN "abholdatum" DATE''')
            if not kunde:
                self.db.execute('''ALTER TABLE "bio_lieferschein" ADD COLUMN "kunde" INTEGER''')

        self.db_kunden.execute('''PRAGMA table_info("kunde")''')
        rows = self.db_kunden.fetchall()
        if not rows:
            self.db_kunden.execute('''CREATE TABLE "kunde" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                     "angelegt" DATE,
                                                     "firma" VARCHAR,
                                                     "vorname" VARCHAR,
                                                     "nachname" VARCHAR,
                                                     "strasse" TEXT,
                                                     "plz" VARCHAR,
                                                     "ort" VARCHAR,
                                                     "rechnung" BOOLEAN,
                                                     "ueberweisung" BOOLEAN,
                                                     "bio" BOOLEAN,
                                                     "bio_kontrollstelle" VARCHAR,
                                                     "notizen" TEXT)''')
            self.db_kunden.execute('''CREATE TABLE "kunde_kontakt" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                             "kunde" INTEGER,
                                                             "typ" VARCHAR,
                                                             "wert" VARCHAR,
                                                             "notiz" VARCHAR
                                                             )''')
        self.db.execute('''PRAGMA table_info("auftrag")''')
        rows = self.db.fetchall()
        if not rows:
            self.db.execute('''CREATE TABLE "auftrag" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                        "handle" VARCHAR NOT NULL,
                                                        "version" INTEGER,
                                                        "currentversion" BOOL DEFAULT TRUE,
                                                        "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                        "user" VARCHAR,
                                                        "kunde" INTEGER,
                                                        "erledigt" BOOL DEFAULT 0,
                                                        "abholung" VARCHAR,
                                                        "quelle" VARCHAR,
                                                        "obst" VARCHAR,
                                                        "obstmenge" VARCHAR,
                                                        "obstart" VARCHAR,
                                                        "angeliefert" BOOL DEFAULT 1,
                                                        "lieferart" VARCHAR,
                                                        "gbcount" INTEGER,
                                                        "kennz" VARCHAR,
                                                        "gebrauchte" VARCHAR,
                                                        "neue" VARCHAR,
                                                        "neue3er" INTEGER, 
                                                        "neue5er" INTEGER,
                                                        "neue10er" INTEGER,
                                                        "sonstiges" TEXT,
                                                        "frischsaft" INTEGER,
                                                        "telefon" VARCHAR,
                                                        "zeitpunkt" TIMESTAMP,
                                                        "status" VARCHAR,
                                                        "anmerkungen" TEXT,
                                                        "bio" BOOL,
                                                        "bio_lieferschein" INTEGER)''')
        else:
            anmerkungen= False
            for row in rows:
                if row['name'] == 'anmerkungen':
                    anmerkungen = True
            if not anmerkungen:
                self.db.execute('''ALTER TABLE "auftrag" ADD COLUMN "anmerkungen" TEXT''')
            timestamp = False
            for row in rows:
                if row['name'] == 'timestamp':
                    timestamp = True
            if not timestamp:
                self.db.execute('''ALTER TABLE "auftrag" ADD COLUMN "timestamp" TIMESTAMP''')
                self.db.execute('''ALTER TABLE "auftrag" ADD COLUMN "user" VARCHAR''')



    def newDB(self):
        self.db.execute('''CREATE TABLE "vorgang" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , 
                                                 "handle" varchar NOT NULL , 
                                                 "version" INTEGER NOT NULL , 
                                                 "currentversion" BOOL DEFAULT TRUE,
                                                 "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP, 
                                                 "user" VARCHAR, 
                                                 "originale" VARCHAR, 
                                                 "zeitpunkt" TIMESTAMP NOT NULL,
                                                 "kunde" INTEGER,
                                                 "name" VARCHAR, 
                                                 "adresse" TEXT, 
                                                 "abholung" VARCHAR, 
                                                 "abgeholt" BOOL DEFAULT 0,
                                                 "telefon" VARCHAR,
                                                 "paletten" INTEGER, 
                                                 "rechnungsnummer" VARCHAR, 
                                                 "rechnungsdatum" DATE, 
                                                 "zahlung" VARCHAR, 
                                                 "bezahlt" BOOL, 
                                                 "summe" FLOAT, 
                                                 "liter" INTEGER, 
                                                 "manuelle_liter" INTEGER, 
                                                 "bio" BOOL DEFAULT 0,
                                                 "bio_lieferschein" INTEGER,
                                                 "bio_kontrollstelle" VARCHAR,
                                                 "bio_kontrollnummer" VARCHAR,
                                                 "bio_lieferant" TEXT,
                                                 "status" VARCHAR)''')
        self.db.execute('''CREATE TABLE "posten" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , 
                                                  "vorgang" INTEGER NOT NULL , 
                                                  "preislisten_id" VARCHAR, 
                                                  "anzahl" FLOAT NOT NULL , 
                                                  "beschreibung" VARCHAR NOT NULL , 
                                                  "einzelpreis" FLOAT NOT NULL , 
                                                  "liter_pro_einheit" INTEGER, 
                                                  "einheit" VARCHAR,
                                                  "datum" DATE, 
                                                  "steuersatz" FLOAT)''')
        self.db.execute('''CREATE TABLE "kassenbeleg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                       "vorgang" VARCHAR NULL,
                                                       "vorgang_version" VARCHAR NULL,
                                                       "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                       "redatum" DATE NULL,
                                                       "renr" VARCHAR NULL, 
                                                       "type" VARCHAR NOT NULL, 
                                                       "tse_processtype" VARCHAR NULL, 
                                                       "tse_processdata" VARCHAR NULL,
                                                       "tse_time_start" INTEGER NULL,
                                                       "tse_time_end" INTEGER NULL,
                                                       "tse_trxnum" VARCHAR NULL,
                                                       "tse_serial" VARCHAR NULL,
                                                       "tse_sigcounter" INTEGER NULL,
                                                       "tse_signature" VARCHAR NULL,
                                                       "json_kunde" TEXT NULL,
                                                       "json_posten" TEXT NULL,
                                                       "json_summen" TEXT NULL,
                                                       "json_zahlungen" TEXT NULL,
                                                       "referenz" VARCHAR NULL,
                                                       "brutto" BOOL NULL,
                                                       "kassenbewegung" FLOAT NULL,
                                                       "bemerkung" VARCHAR)''')
        self.db.execute('''CREATE TABLE "abschluss" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                     "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                     "ersterbeleg" INT NULL,
                                                     "letzterbeleg" INT NULL,
                                                     "summe_brutto" FLOAT NULL,
                                                     "summe_netto" FLOAT NULL,
                                                     "summe_mwst" FLOAT NULL,
                                                     "summe_bar" FLOAT NULL,
                                                     "summe_transit" FLOAT NULL,
                                                     "kassenstand" FLOAT NULL,
                                                     "bemerkung" VARCHAR)''')
        self.db.execute('''CREATE TABLE "anruf" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                 "vorgang" VARCHAR NOT NULL,
                                                 "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                 "nummer" VARCHAR NOT NULL,
                                                 "ergebnis" VARCHAR,
                                                 "bemerkung" VARCHAR)''')
        self.db.execute('''CREATE TABLE "zahlung" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                   "vorgang" VARCHAR NOT NULL,
                                                   "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                                                   "tse_trxnum" INTEGER NULL,
                                                   "zahlart" VARCHAR NOT NULL,
                                                   "betrag" FLOAT,
                                                   "gegeben" FLOAT,
                                                   "zurueck" FLOAT,
                                                   "bemerkung" VARCHAR)''')
        self.db.execute('''CREATE TABLE "bio_lieferschein" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                            "kunde" INTEGER,
                                                            "adresse" TEXT NOT NULL,
                                                            "kontrollnummer" VARCHAR,
                                                            "kontrollstelle" VARCHAR,
                                                            "menge" VARCHAR,
                                                            "obstart" VARCHAR,
                                                            "anlieferdatum" DATE,
                                                            "produktionsdatum" DATE,
                                                            "abholdatum" DATE)''')
        self.db.execute('''CREATE TABLE "auftrag" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                    "handle" VARCHAR NOT NULL,
                                                    "version" INTEGER,
                                                    "currentversion" BOOL DEFAULT TRUE,
                                                    "timestamp" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP, 
                                                    "user" VARCHAR, 
                                                    "kunde" INTEGER,
                                                    "erledigt" BOOL DEFAULT 0,
                                                    "abholung" VARCHAR,
                                                    "quelle" VARCHAR,
                                                    "obst" VARCHAR,
                                                    "obstmenge" VARCHAR,
                                                    "obstart" VARCHAR,
                                                    "angeliefert" BOOL DEFAULT 1,
                                                    "lieferart" VARCHAR,
                                                    "gbcount" INTEGER,
                                                    "kennz" VARCHAR,
                                                    "gebrauchte" VARCHAR,
                                                    "neue" VARCHAR,
                                                    "neue3er" INTEGER, 
                                                    "neue5er" INTEGER,
                                                    "neue10er" INTEGER,
                                                    "sonstiges" TEXT,
                                                    "frischsaft" INTEGER,
                                                    "telefon" VARCHAR,
                                                    "zeitpunkt" TIMESTAMP,
                                                    "status" VARCHAR,
                                                    "anmerkungen" TEXT,
                                                    "bio" BOOL,
                                                    "bio_lieferschein" INTEGER)''')
        
    def newKundenDB(self):
        self.db_kunden.execute('''CREATE TABLE "kunde" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                 "angelegt" DATE,
                                                 "firma" VARCHAR,
                                                 "vorname" VARCHAR,
                                                 "nachname" VARCHAR,
                                                 "strasse" TEXT,
                                                 "plz" VARCHAR,
                                                 "ort" VARCHAR,
                                                 "bio" BOOLEAN,
                                                 "bio_kontrollstelle" VARCHAR,
                                                 "bio_kontrollnummer" VARCHAR,
                                                 "notizen" TEXT)''')
        self.db_kunden.execute('''CREATE TABLE "kunde_kontakt" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                                         "kunde" INTEGER,
                                                         "typ" VARCHAR,
                                                         "wert" VARCHAR,
                                                         "notiz" VARCHAR
                                                         )''')
          
    
    def makeid(self):
        # produziert nach 3 Jahren einen Überlauf.
        # Da wir jahresweise in getrennte Ordner speichern sollte das kein Problem sein.
        return '%09i' % (int(time.time()*10) % 1000000000)

    @staticmethod
    def list_years():
        ret = []
        candidates = os.listdir(PFAD_DB)
        for c in candidates:
            c = c.replace('.sqlite', '')
            if len(c) == 4 and c.isdigit():
                ret.append(c)
        return ret

    def newkey(self):
        self.__class__.__key = open('/dev/urandom', 'rb').read(16)

    def store_key(self, password):
        key = sha256(password).digest()
        mode = AES.MODE_CBC
        encryptor = AES.new(key, mode, IV='\0'*16)
        assert len(self.__class__.__key) == 16, 'Interner Key nicht korrekt!'
        ciphertext = encryptor.encrypt(self.__class__.__key)
        f = open(KEYFILE, 'wb')
        f.write(ciphertext)
        f.close()
        

    def _decrypt_key(self, ciphertext, password):
        key = sha256(password).digest()
        mode = AES.MODE_CBC
        decryptor = AES.new(key, mode, IV='\0'*16)
        plaintext = decryptor.decrypt(ciphertext)
        self.__class__.__key = plaintext 
        #print ('decrypt_key:',self.__class__.__key)

    def get_key(self, password):
        ciphertext = open(KEYFILE, 'rb').read()
        self._decrypt_key(ciphertext, password)
        
        
    def is_unlocked(self):
        return (self.__class__.__key is not None)
    
    def lock(self):
        return # FIXME 
        self.__class__.__key = None
        self.db.close()
        self.db = None
        self.dbconn.close()
        self.dbconn = None
        time.sleep(0.2)
    
    def unmount(self):
        self.__class__.__key = None
        try:
            self.db.close()
            del(self.db)
            self.db = None
        except:
            pass
        try:
            self.dbconn.close()
            del(self.dbconn)
            time.sleep(1)
            self.db = None
        except:
            pass
        time.sleep(0.2)
        try:
            self.encfs.unmount()
        except:
            pass


    def _check_password(self, ciphertext, password):
        key = sha256(password).digest()
        mode = AES.MODE_CBC
        decryptor = AES.new(key, mode, IV='\0'*16)
        plaintext = decryptor.decrypt(ciphertext).strip()
        if plaintext == password:
            return True
        else:
            return False

    def check_password(self, password):
        if type('') == type(u'') and type(password) == str: # Python 3
            password = password.encode('utf-8')
        if os.path.exists(USERS_FILE):
            # New-style (>= 2013)
            xml = fromstring(open(USERS_FILE, 'r').read())
            for user in xml.findall('user'):
                ciphertext = base64.b64decode(user.findtext('password').strip())
                if self._check_password(ciphertext, password):
                    self._decrypt_key(base64.b64decode(user.findtext('key').strip()), password)
                    self.__currentuser['name'] = user.findtext('name').strip()
                    self.__currentuser['id'] = int(user.get('id'))
                    self.__currentuser['role'] = 'user'
                    if user.findtext('role', 'user') == 'admin':
                        self.__currentuser['role'] = 'admin'
                    print('logged in user: %s' % self.__currentuser)
                    self.initialize()
                    return True
            return False
        return False

    def list_users(self):
        assert os.path.exists(USERS_FILE), "User-Datei nicht gefunden"
        xml = fromstring(open(USERS_FILE, 'r').read())
        userlist = []
        for user in xml.findall('user'):
            u = {'name': user.find('name').text, 'id': user.get('id'), 'role': user.get('role', 'user')}
            userlist.append(u)
        return userlist

    def set_user_password(self, userid, username, password):
        key = sha256(password).digest()
        mode = AES.MODE_CBC
        encryptor = AES.new(key, mode, IV='\0'*16)
        assert len(self.__class__.__key) == 16, 'Interner Key nicht korrekt!'
        key_ciphertext = base64.b64encode(encryptor.encrypt(self.__class__.__key))
        encryptor = AES.new(key, mode, IV='\0'*16)
        password_ciphertext = base64.b64encode(encryptor.encrypt(password.ljust(16)))

        xml = Element('users')        
        found = False
        if os.path.exists(USERS_FILE):
            xml = fromstring(open(USERS_FILE, 'r').read())
            for user in xml.findall('user'):
                if user.get('id') == str(userid):
                    user.find('password').text = password_ciphertext
                    user.find('key').text = key_ciphertext
                    user.find('name').text = username
                    found = True
                    break
        if not found:
            user = SubElement(xml, 'user')
            user.set('id', str(userid))
            name = SubElement(user, 'name')
            name.text = username
            pw = SubElement(user, 'password')
            pw.text = password_ciphertext
            key = SubElement(user, 'key')
            key.text = key_ciphertext
        f = open(USERS_FILE, 'w')
        f.write(tostring(xml).encode('utf-8'))
        f.close()

    def get_max_userid(self):
        xml = fromstring(open(USERS_FILE, 'r').read())
        current = 0
        for user in xml.findall('user'):
            try:
                tmp = int(user.get('id'))
                if tmp > current:
                    current = tmp
            except:
                continue
        return current

    def add_user(self, username, password):
        userid = self.get_max_userid() + 1
        self.set_user_password(userid, username, password)
        return userid

    def get_current_user(self):
        return self.__currentuser

    def store_validation_file(self, password):
        # password validation:
        key = sha256(password).digest()
        mode = AES.MODE_CBC
        encryptor = AES.new(key, mode, IV='\0'*16)
        f = open(KEY_VALIDATE_FILE, 'wb')
        plaintext = password.ljust(16)
        f.write(encryptor.encrypt(plaintext))
        f.close()


    def change_password(self, oldpassword, newpassword):
        if self.check_password(oldpassword):
            self.store_key(newpassword)
            self.store_validation_file(newpassword)

    def listVorgaenge(self):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
        
    def listVorgaengeUnbezahlt(self, postponed=False):
        ret = []
        if postponed:
            self.db.execute("SELECT %s FROM vorgang where currentversion=1 AND zahlung='bar' AND bezahlt=0 ORDER BY name" % VORGANG_FIELDLIST)
        else:
            self.db.execute("SELECT %s FROM vorgang where currentversion=1 AND zahlung='bar' AND bezahlt=0 AND (status IS NULL OR status<>'postponed') ORDER BY name" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
        
    def listVorgaengeLastPayed(self, num = 8):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 AND bezahlt=1 ORDER BY timestamp DESC LIMIT ?" % VORGANG_FIELDLIST, (num,))
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
        
    def listVorgaengeByDateAsc(self):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 ORDER BY zeitpunkt ASC" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listVorgaengeByDateDesc(self):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 ORDER BY zeitpunkt DESC" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listVorgaengeByName(self):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 ORDER BY name ASC" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listVorgaengeByKunde(self, kunde):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 AND kunde=?" % VORGANG_FIELDLIST, (str(kunde),))
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listVorgaengeByNameFilter(self, searchstring):
        ret = []
        searchstring = '%'+searchstring+'%'
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 AND name LIKE ? ORDER BY name ASC" % VORGANG_FIELDLIST, (searchstring,))
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listVorgaengeByAmount(self):
        ret = []
        self.db.execute("SELECT %s FROM vorgang where currentversion=1 ORDER BY summe ASC" % VORGANG_FIELDLIST)
        stack = self.db.fetchall()
        for item in stack:
            ret.append(self.ladeVorgang(sqlresult = item))
        return ret
    
    def listeKundennamen(self):
        alteKunden = self.ladeAlteKundennamen()
        self.db.execute("SELECT DISTINCT name FROM vorgang")
        aktuelleKunden = [item['name'] for item in self.db.fetchall() if item['name'] is not None]
        alleKundennamen = sorted(list(set(alteKunden + aktuelleKunden)))
        return alleKundennamen

    def listeRechnungsadressen(self):
        alteAdressen = self.ladeAlteRechnungsadressen() 
        self.db.execute("SELECT DISTINCT adresse FROM vorgang")
        aktuelleAdressen = [item['adresse'] for item in self.db.fetchall() if item['adresse'] is not None]
        adressen = list(set(alteAdressen + aktuelleAdressen))
        return adressen
    
    def speichereAlteRechnungsadressen(self, liste):
        clean = [item.replace('\n', '\t') for item in liste]
        try:
            if os.path.exists(ALTE_RECHNUNGSADRESSEN):
                os.rename(ALTE_RECHNUNGSADRESSEN, ALTE_RECHNUNGSADRESSEN+'.old')
            f = open(ALTE_RECHNUNGSADRESSEN, 'w')
            f.write((u'\n'.join(clean)).encode('utf-8'))
            f.close()
        except:
            print ('Fehler beim Schreiben der alten Kundennamen')
    
        
    
    def ladeAlteKundennamen(self):
        liste = []
        try:
            if os.path.exists(ALTE_KUNDEN):
                f = open(ALTE_KUNDEN, 'r')
                liste = [l.decode('utf-8').strip() for l in f.readlines()]
            else:
                print ('Datei mit alten Kunden-Namen nicht gefunden.')
        except:
            print ('Fehler beim Einlesen der alten Kundennamen!')
        return liste
    
    def ladeAlteRechnungsadressen(self):
        liste = []
        try:
            if os.path.exists(ALTE_RECHNUNGSADRESSEN):
                f = open(ALTE_RECHNUNGSADRESSEN, 'r')
                liste = [l.decode('utf-8').strip().replace('\t', '\n') for l in f.readlines()]
            else:
                print ('Datei mit alten Rechnungsadressen nicht gefunden.')
        except:
            print ('Fehler beim Einlesen der alten Rechnungsadressen!')
        return liste
    
    def speichereAlteKunden(self, liste):
        try:
            if os.path.exists(ALTE_KUNDEN):
                os.rename(ALTE_KUNDEN, ALTE_KUNDEN+'.old')
            f = open(ALTE_KUNDEN, 'w')
            f.write(('\n'.join(liste)).encode('utf-8'))
            f.close()
        except:
            print ('Fehler beim Schreiben der alten Kundennamen')
    
            
        
    def getVorgang(self, handle):
        return self.ladeVorgang(handle=handle)
    
    
    def getVorgangVersionen(self, handle):
        ret = {}
        self.db.execute('SELECT version,timestamp,user FROM vorgang WHERE handle=?', (handle,))
        while True:
            one = self.db.fetchone()
            if not one:
                break
            ret[int(one['version'])] = (one['user'], one['timestamp'])
        return ret


    def ladeVorgang(self, handle=None, sqlresult=None, mitpreisliste = True, version=None):
        # Lade alle Versionen
        if not self.db:
            raise RuntimeError('Datenbank nicht initialisiert')
        if handle:
            if version:
                self.db.execute("SELECT %s FROM vorgang AS outer where version=? AND handle=?" % VORGANG_FIELDLIST, [version,handle,])
            else:
                self.db.execute("SELECT %s FROM vorgang AS outer where currentversion=1 AND handle=?" % VORGANG_FIELDLIST, [handle,])

            sqlresult = self.db.fetchone()
            if not sqlresult:
                raise ValueError("ladeVorgang() called with invalid handle %s" % handle)
            
        if not handle and not sqlresult:
            raise ValueError("ladeVorgang() called without handle and withoud SQLresult")

        daten = sqlresult

        vorgang = Vorgang()

        if not handle:
            handle = daten['handle'] 
                    
        vorgang.setID(daten['handle'])
        vorgang.setVersion(daten['version'])
        if daten['kunde']:
            vorgang.kunde = self.ladeKunde(daten['kunde'])
        else:
            vorgang.kunde = Kunde()
            vorgang.kunde.setName(daten['name'])
            vorgang.kunde.addKontakt('telefon',daten['telefon'])
        #vorgang.setAdresse(daten['adresse'])
        vorgang.setAbholung(daten['abholung'])
        vorgang.setPaletten(daten['paletten'])
        vorgang.setStatus(daten['status'])
        vorgang.setBio(bool(daten['bio']), daten['bio_kontrollstelle'], daten['bio_lieferant'], daten['bio_lieferschein'])
        zeitpunkt = daten['zeitpunkt']
        if zeitpunkt:
            if type(zeitpunkt) == str:
                zeitpunkt = datetime.datetime.strptime(zeitpunkt, "%Y-%m-%d %H:%M:%S.%f")
            vorgang.setZeitpunkt(zeitpunkt)

        rechnungsnummer = daten['rechnungsnummer']
        if rechnungsnummer:
            rechnungsdatum = daten['rechnungsdatum']
            if type(rechnungsdatum) == str:
                rechnungsdatum = datetime.datetime.strptime(daten['rechnungsdatum'], "%Y-%m-%d").date()
            vorgang.setRechnungsdaten(rechnungsdatum, rechnungsnummer)

        vorgang.setPayed(daten['bezahlt'])
        if daten['originale']:
            vorgang.originale = daten['originale'].split(',')
        zahlart = daten['zahlung']
        if zahlart == 'ec':
            vorgang.setPayedEC(True)
        elif zahlart == 'ueberweisung':
            vorgang.setBanktransfer(True)
        
        vorgang.setManuelleLiterzahl( daten['manuelle_liter'] )
        
        self.db.execute("SELECT id,preislisten_id,anzahl,beschreibung,einzelpreis,liter_pro_einheit,einheit,steuersatz,datum FROM posten WHERE vorgang=?", (daten['id'],))
        while True:
            item = self.db.fetchone()
            if not item:
                break 
            vorgang.newItem(anzahl = item['anzahl'], 
                      preislistenID = item['preislisten_id'], 
                      beschreibung = item['beschreibung'], 
                      einzelpreis = item['einzelpreis'], 
                      liter_pro_einheit = item['liter_pro_einheit'], 
                      einheit = item['einheit'],
                      steuersatz = item['steuersatz'],
                      datum = item['datum'], 
                      autoupdate = mitpreisliste)
        if mitpreisliste and round(vorgang.getSumme(), 2) != round(float(daten['summe']), 2):
            print ('%s: %.2f != %.2f, lade neu mit festen Preisen!' % (handle, vorgang.getSumme(), float(daten['summe'])))
            vorgang = self.ladeVorgang(handle, mitpreisliste = False)
            #print ('Abweichende Summe: %.2f != %.2f' % (round(vorgang.getSumme(), 2), round(float(xml.find('invoice').attrib['summe']), 2)))
        #if mitpreisliste and vorgang.getLiterzahl() != float(xml.find('invoice').attrib['liter']):
        #    print ('Abweichende Literzahl!')
        
        zahlungen = self.getZahlungen(vorgang)
        for z in zahlungen:
            vorgang.zahlungen.append(z)
        
        vorgang.changed = False
        return vorgang
        

    def speichereVorgang(self, vorgang, user=None, timestamp=None):
        if vorgang.ID and not vorgang.changed:
            print('Speichern nicht nötig!')
            return
        username = self.__currentuser['name']
        if user:
            username = user
        if not timestamp:
            timestamp = datetime.datetime.now()
        if not vorgang.ID:
            vorgang.ID = self.makeid()
        handle = vorgang.ID 
        vorgang.setVersion(vorgang.getVersion() + 1)
        if not vorgang.getZeitpunkt():
            vorgang.setZeitpunkt(datetime.datetime.now())
        zahlung = 'bar'
        if vorgang.getZahlart() == 'ec':
            zahlung = 'ec'
        elif vorgang.getBanktransfer():
            zahlung = 'ueberweisung'
        kontrollstelle = None
        lieferant = None
        lieferschein = None
        bio = vorgang.getBio()
        if type(bio) != bool:
            kontrollstelle = str(bio)
            lieferant = vorgang.getBioLieferant()
            lieferschein = vorgang.getBioLieferschein()
        kunde = None
        if vorgang.kunde and vorgang.kunde.ID():
            kunde = vorgang.kunde.ID()
        originale = None
        if vorgang.originale:
            originale = ','.join(vorgang.originale)
            
        self.db.execute("INSERT INTO vorgang (handle,version,currentversion,user,originale,zeitpunkt,kunde,name,adresse,abholung,telefon,paletten,timestamp,zahlung,bezahlt,summe,liter,manuelle_liter,rechnungsnummer,rechnungsdatum,bio,bio_kontrollstelle,bio_lieferant,bio_lieferschein,status) "
                        "VALUES              (?,     ?,      1,             ?,   ?,        ?,        ?,    ?,   ?,      ?,       ?,      ?,       ?,        ?,      ?,      ?,    ?,    ?,             ?,              ?,             ?,  ?,                 ?,            ?,               ?)",
                        (handle, vorgang.getVersion(), username, originale, vorgang.getZeitpunkt(), kunde, vorgang.getKundenname(), vorgang.kunde.getAdresse(), vorgang.getAbholung(),
                         vorgang.getTelefon(),str(vorgang.getPaletten()), timestamp, zahlung, vorgang.getPayed(), vorgang.getSumme(), 
                         str(vorgang.getLiterzahl()), vorgang.getManuelleLiterzahl(), vorgang.rechnungsDaten['nummer'], vorgang.rechnungsDaten['datum'], vorgang.isBio(), 
                         kontrollstelle, lieferant, lieferschein, vorgang.getStatus()))
        vorgang_id = self.db.lastrowid

        self.db.execute("UPDATE vorgang SET currentversion=0 WHERE handle=? AND version != ?", [handle, vorgang.getVersion()])
        
        for item in vorgang.getEntries():
            preislisten_id = None
            if item.preislistenID:
                preislisten_id = item.preislistenID
            datum = item.getDatum()
            if datum:
                datum = datum.isoformat()
            self.db.execute("INSERT INTO posten (vorgang,preislisten_id,anzahl,beschreibung,einzelpreis,liter_pro_einheit,einheit,steuersatz,datum) "
                            "VALUES             (?,    ?,             ?,     ?,           ?,          ?,                ?,      ?,         ?)",
                            (vorgang_id, preislisten_id, item.getStueckzahl(), item.getBeschreibung(), item.getPreis(), item.getLiterProEinheit(),
                             item.getEinheit(),item.getSteuersatz(),datum))


        self.dbconn.commit()
        vorgang.changed = False


    def speichereAnruf(self, rechnung, ergebnis, bemerkung):
        handle = rechnung.ID
        self.db.execute("INSERT INTO anruf (vorgang, nummer, ergebnis, bemerkung) VALUES (?,?,?,?)",
                                            (handle, rechnung.getTelefon(), ergebnis, bemerkung))
        self.dbconn.commit()
    
    def getAnrufe(self, rechnung):
        handle = rechnung.ID
        self.db.execute("SELECT timestamp,ergebnis,bemerkung FROM anruf WHERE vorgang=?", (handle,))
        rows = self.db.fetchall()
        return rows

    def loescheVorgang(self, rechnung):
        if not rechnung.ID:
            return False
        handle = rechnung.ID
        rechnung.setStatus('deleted')
        self.speichereVorgang(rechnung)
        self.db.execute("UPDATE vorgang SET currentversion=0 WHERE handle=?", (handle,))

    def speichereZahlung(self, vorgang, zahlart, betrag, gegeben = None, zurueck = None, bemerkung = None):
        handle = vorgang.ID
        if not handle:
            # Vorgang ist noch gar nicht gespeichert!
            self.speichereVorgang(vorgang)
            handle = vorgang.ID
        timestamp = datetime.datetime.now()
        self.db.execute("INSERT INTO zahlung (vorgang, timestamp, zahlart, betrag, gegeben, zurueck, tse_trxnum, bemerkung) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)",
                        (handle, timestamp, zahlart, betrag, gegeben, zurueck, bemerkung))
        self.dbconn.commit()

    def updateZahlung(self, zahlung, tse_trxnum):
        self.db.execute("UPDATE zahlung SET tse_trxnum=? WHERE id=? AND tse_trxnum IS NULL", (tse_trxnum, zahlung,))

    def getZahlungen(self, vorgang):
        handle = vorgang.ID
        self.db.execute("SELECT id, timestamp, vorgang, zahlart, betrag, gegeben, zurueck, tse_trxnum, bemerkung FROM zahlung WHERE vorgang=?", (handle,))
        result = self.db.fetchall()
        return result

    def loescheZahlung(self, zahlung):
        self.db.execute("DELETE FROM zahlung WHERE id=?", (zahlung,))
        self.dbconn.commit()


    def listAlleZahlungen(self):
        self.db.execute("SELECT id, timestamp, vorgang, zahlart, betrag, gegeben, zurueck, tse_trxnum, bemerkung FROM zahlung")
        result = self.db.fetchall()
        return result

    def listZahlungenTagesjournal(self, datum=None):
        if not datum:
            return {}
        if type(datum) != type(' ') or len(datum) != 10:
            raise ValueError('Date format does not match')
        self.db.execute("SELECT z.timestamp, vorgang, zahlart, z.betrag, (SELECT b.name FROM vorgang AS b WHERE handle=z.vorgang) AS name FROM zahlung AS z WHERE DATE(z.timestamp) == ? ORDER BY z.timestamp;", (datum,))
        result = self.db.fetchall()
        return result

    def speichereKassenbeleg(self, k):
        def convert(obj):
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            else:
                return str(obj)
            
        k['json_kunde'] = json.dumps(k['kunde'], default=convert)
        k['json_posten'] = json.dumps(k['posten'], default=convert)
        k['json_summen'] = json.dumps(k['summen'], default=convert)
        k['json_zahlungen'] = json.dumps(k['zahlungen'], default=convert)
        
        if k['id']:
            self.db.execute("UPDATE kassenbeleg SET vorgang=?, vorgang_version=?, redatum=?, renr=?, type=?, tse_processtype=?, "
                            "tse_processdata=?, tse_time_start=?, tse_time_end=?, tse_trxnum=?, tse_serial=?, tse_sigcounter=?, "
                            "tse_signature=?, json_kunde=?, json_posten=?, json_summen=?, json_zahlungen=?, referenz=?, brutto=?, "
                            "kassenbewegung=?, bemerkung=? WHERE id=?", 
                            (k['vorgang'], k['vorgang_version'], k['redatum'], k['renr'], k['type'], k['tse_processtype'],
                             k['tse_processdata'], k['tse_time_start'], k['tse_time_end'], k['tse_trxnum'], k['tse_serial'],
                             k['tse_sigcounter'], k['tse_signature'], k['json_kunde'], k['json_posten'], k['json_summen'], 
                             k['json_zahlungen'], k['referenz'], k['brutto'], k['kassenbewegung'], k['bemerkung'], k['id']))
        else:
            self.db.execute("INSERT INTO kassenbeleg "
                            "(vorgang, vorgang_version, redatum, renr, type, tse_processtype, tse_processdata, tse_time_start, "
                            "tse_time_end, tse_trxnum, tse_serial, tse_sigcounter, tse_signature, json_kunde, json_posten, "
                            "json_summen, json_zahlungen, referenz, brutto, kassenbewegung, bemerkung) VALUES "
                            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (k['vorgang'], k['vorgang_version'], k['redatum'], k['renr'], k['type'], k['tse_processtype'],
                             k['tse_processdata'], k['tse_time_start'], k['tse_time_end'], k['tse_trxnum'], k['tse_serial'],
                             k['tse_sigcounter'], k['tse_signature'], k['json_kunde'], k['json_posten'], k['json_summen'], 
                             k['json_zahlungen'], k['referenz'], k['brutto'], k['kassenbewegung'], k['bemerkung']))
            k['id'] = self.db.lastrowid
        self.dbconn.commit()
        return k['id']
       
    def getKassenbeleg(self, id=None, renr=None):
        if id:
            self.db.execute("SELECT id, timestamp, vorgang, vorgang_version, redatum, renr, type, tse_processtype, tse_processdata, tse_time_start, "
                            "tse_time_end, tse_trxnum, tse_serial, tse_sigcounter, tse_signature, json_kunde, json_posten, "
                            "json_summen, json_zahlungen, referenz, brutto, kassenbewegung, bemerkung FROM kassenbeleg WHERE id=?", (id,))
        else:
            self.db.execute("SELECT id, timestamp, vorgang, vorgang_version, redatum, renr, type, tse_processtype, tse_processdata, tse_time_start, "
                            "tse_time_end, tse_trxnum, tse_serial, tse_sigcounter, tse_signature, json_kunde, json_posten, "
                            "json_summen, json_zahlungen, referenz, brutto, kassenbewegung, bemerkung FROM kassenbeleg WHERE renr=?", (renr,))
        b = dict(self.db.fetchone())
        b['summen'] = json.loads(b['json_summen'])
        b['kunde'] = json.loads(b['json_kunde'])
        b['posten'] = json.loads(b['json_posten'])
        b['zahlungen'] = json.loads(b['json_zahlungen'])
        return b
    
    
    def listKassenbelege(self, erster=None, letzter=None):
        if not erster and not letzter:
            # alle!
            self.db.execute("SELECT id FROM kassenbeleg")
        if erster and not letzter:
            self.db.execute("SELECT id FROM kassenbeleg WHERE id >= ?", (erster,))
        if erster and letzter:
            self.db.execute("SELECT id FROM kassenbeleg WHERE id >= ? AND id <= ?", (erster, letzter))
        ret = []
        for line in self.db.fetchall():
            ret.append(self.getKassenbeleg(line['id']))
        return ret
       
    def getAbschluss(self, from_date=None, to_date=None):
        self.db.execute("SELECT id, timestamp, ersterbeleg, letzterbeleg, summe_brutto, summe_netto, summe_mwst, summe_bar, summe_transit, kassenstand, bemerkung "
                        "FROM abschluss WHERE timestamp > ? AND timestamp < ?", (from_date, to_date))
        res = self.db.fetchall()
        return res
    
    def getLetzterAbschluss(self):
        self.db.execute("SELECT id, timestamp, ersterbeleg, letzterbeleg, summe_brutto, summe_netto, summe_mwst, summe_bar, summe_transit, kassenstand, bemerkung "
                        "FROM abschluss ORDER BY timestamp DESC LIMIT 1")
        res = self.db.fetchone()
        return res
    
    def speichereAbschluss(self, a):
        self.db.execute("INSERT INTO abschluss (ersterbeleg, letzterbeleg, summe_brutto, summe_netto, summe_mwst, summe_bar, summe_transit, kassenstand, bemerkung) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (a['ersterbeleg'], a['letzterbeleg'], a['summe_brutto'], a['summe_netto'], a['summe_mwst'], a['summe_bar'],
                         a['summe_transit'], a['kassenstand'], a['bemerkung']))
        self.dbconn.commit()
    
    def getAlteBioKunden(self):
        liste = []
        try:
            if os.path.exists(ALTE_BIOKUNDEN):
                f = open(ALTE_BIOKUNDEN, 'r')
                for line in f.readlines():
                    fields = line.split('\t')
                    entry = {'name': fields[0],
                             'adresse': fields[1].replace(',', '\n'),
                             'kontrollstelle': fields[3],
                             }
                    liste.append(entry)
            else:
                print ('Datei mit alten Bio-Kunden nicht gefunden.')
        except:
            print ('Fehler beim Einlesen der alten Bio-Kunden!')
        return liste
        

    def getBioKunden(self):
        self.db.execute("SELECT DISTINCT adresse, kontrollstelle FROM bio_lieferschein WHERE kontrollstelle IS NOT NULL")
        kunden = self.db.fetchall()
        altekunden = self.getAlteBioKunden()
        return kunden + altekunden

    def ladeBioLieferschein(self, id):
        self.db.execute("SELECT id, kunde, adresse, kontrollstelle, menge, obstart, anlieferdatum, produktionsdatum, abholdatum FROM bio_lieferschein WHERE id=?", (id,))
        ret = dict(self.db.fetchone())
        obstart = ret['obstart'].split(',')
        ret['obstart'] = {}
        for obst in obstart:
            ret['obstart'][obst] = True
        return ret
        
        
    def speichereBioLieferschein(self, data):
        obstart = []
        for key in data['obstart'].keys():
            if data['obstart'][key]:
                obstart.append(key)
        if not 'anlieferdatum' in data.keys():
            data['anlieferdatum'] = datetime.date.today()
        if not 'produktionsdatum' in data.keys():
            data['produktionsdatum'] = None
        if not 'abholdatum' in data.keys():
            data['abholdatum'] = None
        if 'id' in data:
            self.db.execute("UPDATE bio_lieferschein SET kunde=?, adresse=?, kontrollstelle=?, menge=?, "
                            "obstart=?, anlieferdatum=?, produktionsdatum=?, abholdatum=? WHERE id=?",
                            (data['kunde'], data['adresse'], data['kontrollstelle'], data['menge'],','.join(obstart), 
                             data['anlieferdatum'], data['produktionsdatum'], data['abholdatum'], data['id']))
        else:
            self.db.execute("INSERT INTO bio_lieferschein (kunde, adresse, kontrollstelle, menge, obstart, anlieferdatum) VALUES (?, ?, ?, ?, ?, ?)",
                    (data['kunde'], data['adresse'], data['kontrollstelle'], data['menge'],','.join(obstart), data['anlieferdatum']))
        self.dbconn.commit()
        
    def getBioLieferscheine(self, kunde=None, fertige=False):
        if kunde:
            if type(kunde) != int:
                kunde = kunde.ID()
            self.db.execute("SELECT id, kunde, adresse, kontrollstelle, menge, obstart, anlieferdatum, produktionsdatum, abholdatum FROM bio_lieferschein WHERE kunde=?", (kunde,))
        else:
            self.db.execute("SELECT id, kunde, adresse, kontrollstelle, menge, obstart, anlieferdatum, produktionsdatum, abholdatum FROM bio_lieferschein")
        data = self.db.fetchall()
        ret = []
        for item in data:
            retitem = dict(item)
            if item['produktionsdatum'] and not fertige:
                continue
            obstart = item['obstart'].split(',')
            retitem['obstart'] = {}
            for obst in obstart:
                retitem['obstart'][obst] = True
            ret.append(retitem)
        return ret

    def speichereKunde(self, kunde):
        if not kunde:
            print ('Kundendaten sind leer, diesen Kunde speichern wir nicht!')
            return
        data, kontakt = kunde.getRAW()
        if data['id'] is None:
            self.db_kunden.execute("INSERT INTO kunde (angelegt, firma, vorname, nachname, strasse, plz, ort, bio, bio_kontrollstelle, notizen) VALUES "+
                            "(DATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                            (data['firma'], data['vorname'], data['nachname'], data['strasse'], data['plz'], data['ort'], int(data['bio']), data['bio_kontrollstelle'], data['notizen']))
            data['id'] = self.db_kunden.lastrowid
            kunde.setRAW({'id': data['id']})
        else:
            self.db_kunden.execute("UPDATE kunde SET firma=?, vorname=?, nachname=?, strasse=?, plz=?, ort=?, bio=?, bio_kontrollstelle=?, notizen=? WHERE id=?",
                            (data['firma'], data['vorname'], data['nachname'], data['strasse'], data['plz'], data['ort'], int(data['bio']), data['bio_kontrollstelle'], data['notizen'], data['id']))
        for k in kontakt:
            if k['id'] is None:
                self.db_kunden.execute("INSERT INTO kunde_kontakt (kunde, typ, wert, notiz) VALUES "+
                                "(?, ?, ?, ?)", (data['id'], k['typ'], k['wert'], k['notiz']))
                k['id'] = self.db_kunden.lastrowid
            else:
                self.db_kunden.execute("UPDATE kunde_kontakt SET typ=?, wert=?, notiz=? WHERE id=?",
                                (k['typ'], k['wert'], k['notiz'], k['id']))
        # entferne gelösche Kontaktdaten
        kontaktids = [k['id'] for k in kontakt]
        self.db_kunden.execute("SELECT id FROM kunde_kontakt WHERE kunde=?", (data['id'],))
        result = self.db_kunden.fetchall()
        for row in result:
            if row['id'] not in kontaktids:
                self.db_kunden.execute("DELETE FROM kunde_kontakt WHERE id=?", (row['id'],))
        
        self.dbconn_kunden.commit()
        return data['id']

    def ladeKunde(self, nr):
        self.db_kunden.execute("SELECT id,angelegt, firma, vorname, nachname, strasse, plz, ort, bio, bio_kontrollstelle, notizen FROM kunde WHERE id=?", (nr,))
        data = self.db_kunden.fetchone()
        if not data:
            raise ValueError('Kunde #%s nicht gefunden' % nr)
        kunde = Kunde()
        kunde.setRAW(data)
        self.db_kunden.execute("SELECT id, typ, wert, notiz FROM kunde_kontakt WHERE kunde=?", (nr,))
        data = self.db_kunden.fetchall()
        for row in data:
            kunde.addKontaktRAW(row['typ'], row['wert'], row['notiz'], row['id'])
        return kunde


    def sucheKundeTelefon(self, such):
        ret = set()
        st = '%'+such+'%'
        self.db_kunden.execute("SELECT kunde FROM kunde_kontakt WHERE wert LIKE ?", (st,))
        data = self.db_kunden.fetchall()
        for row in data:
            ret.add(row['kunde'])
            
        return [self.ladeKunde(nr) for nr in ret]
        

    def sucheKunde(self, such):
        ret = set()
        nummersuch = '%'+such+'%'
        for x in '+- /.()':
            nummersuch = nummersuch.replace(x, '')
        st = '%'+such+'%'
        self.db_kunden.execute("SELECT id FROM kunde WHERE firma LIKE ? or vorname LIKE ? or nachname LIKE ? or strasse LIKE ? or ort LIKE ? or notizen LIKE ?", 
                         (st, st, st, st, st, st))
        data = self.db_kunden.fetchall()
        for row in data:
            ret.add(row['id'])
        
        self.db_kunden.execute("SELECT kunde FROM kunde_kontakt WHERE wert LIKE ? or wert LIKE ? or notiz LIKE ?", (st, nummersuch, st))
        data = self.db_kunden.fetchall()
        for row in data:
            ret.add(row['kunde'])
            
        return [self.ladeKunde(nr) for nr in ret]


    def speichereAuftrag(self, auftrag):
        if not auftrag:
            return 
        auftrag.version += 1
        if not auftrag.kunde.ID():
            self.speichereKunde(auftrag.kunde)
        
        self.db.execute('''INSERT INTO "auftrag" (handle, version, currentversion, timestamp, user, kunde, erledigt, 
            abholung, quelle, obst, obstmenge, obstart, angeliefert, lieferart, gbcount, kennz, gebrauchte, neue, 
            neue3er, neue5er, neue10er, sonstiges, frischsaft, telefon, zeitpunkt, status, anmerkungen, bio, 
            bio_lieferschein) VALUES 
            (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (auftrag.ID, auftrag.version, datetime.datetime.now(), self.__currentuser['name'], auftrag.kunde.ID(), 
             int(auftrag.erledigt), auftrag.abholung, auftrag.quelle, auftrag.obst, auftrag.obstmenge, auftrag.obstart, 
             int(auftrag.angeliefert), auftrag.lieferart, auftrag.gbcount, auftrag.kennz, auftrag.gebrauchte, 
             auftrag.neue, auftrag.neue3er, auftrag.neue5er, auftrag.neue10er, auftrag.sonstiges, auftrag.frischsaft, 
             auftrag.telefon, auftrag.zeitpunkt, auftrag.status, auftrag.anmerkungen, int(auftrag.bio), 
             auftrag.bio_lieferschein)
            );
        self.db.execute('UPDATE "auftrag" SET currentversion=0 WHERE handle=? AND version != ?',
                      (auftrag.ID, auftrag.version))
        self.dbconn.commit()
        
    def ladeAuftrag(self, handle = None, version = None, sqlresult = None):
        if handle:
            if version:
                self.db.execute('''SELECT %s FROM "auftrag" WHERE handle=? AND 
                    version=?''' % (AUFTRAG_FIELDLIST,), (handle, version))
            else:
                self.db.execute('''SELECT %s FROM "auftrag" WHERE handle=? AND 
                    currentversion=1''' % (AUFTRAG_FIELDLIST,), (handle,))
            sqlresult = self.db.fetchone()

        if not sqlresult:
            raise ValueError('Datenbank inkonsistent für Auftrag #%s, version %s' % (handle, version))
        r = sqlresult
        
        a = Auftrag()
        a.ID = r['handle']
        a.version = r['version']
        a.kunde = self.ladeKunde(r['kunde'])
        a.erledigt = bool(r['erledigt'])
        a.abholung = r['abholung']
        a.quelle = r['quelle']
        a.obst = r['obst']
        a.obstmenge = r['obstmenge']
        a.obstart = r['obstart']
        a.angeliefert = bool(r['angeliefert'])
        a.lieferart = r['lieferart']
        a.gbcount = r['gbcount']
        a.kennz = r['kennz']
        a.gebrauchte = r['gebrauchte']
        a.neue = r['neue']
        a.neue3er = r['neue3er']
        a.neue5er = r['neue5er']
        a.neue10er = r['neue10er']
        a.sonstiges = r['sonstiges']
        a.frischsaft = r['frischsaft']
        a.telefon = r['telefon']
        a.zeitpunkt = datetime.datetime.strptime(r['zeitpunkt'], "%Y-%m-%d %H:%M:%S.%f")
        a.status = r['status']
        a.anmerkungen = r['anmerkungen']
        a.bio = bool(r['bio'])
        a.bio_lieferschein = r['bio_lieferschein']
        
        return a
    
    def getAuftragVersionen(self, handle):
        ret = {}
        self.db.execute('SELECT version,zeitpunkt,quelle,status FROM auftrag WHERE handle=?', (handle,))
        while True:
            one = self.db.fetchone()
            if not one:
                break
            ret[int(one['version'])] = {'quelle': one['quelle'], 
                                        'zeitpunkt': one['zeitpunkt'],
                                        'status': one['status'],
                                        }
        return ret
    
    def listAuftraege(self):
        ret = []
        self.db.execute("SELECT %s FROM auftrag WHERE currentversion=1 ORDER BY zeitpunkt" % (AUFTRAG_FIELDLIST,))
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret

    def listAuftraegeByDateDesc(self):
        ret = []
        self.db.execute("SELECT %s FROM auftrag WHERE currentversion=1 ORDER BY zeitpunkt DESC" % (AUFTRAG_FIELDLIST,))        
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret

    
    def listAuftraegeByDateAsc(self):
        ret = []
        self.db.execute("SELECT %s FROM auftrag WHERE currentversion=1 ORDER BY zeitpunkt ASC" % (AUFTRAG_FIELDLIST,))        
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret

    
    def listAuftraegeByKunde(self, kunde):
        ret = []
        self.db.execute("SELECT %s FROM auftrag WHERE kunde=? AND currentversion=1 ORDER BY zeitpunkt ASC" % (AUFTRAG_FIELDLIST,), (kunde,))        
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret

    
    def listAuftraegeByName(self):
        ret = []
        self.db.execute("SELECT %s,(SELECT COALESCE(firma,nachname,vorname) AS name FROM kunden WHERE kunden.id=auftrag.kunde) FROM auftrag WHERE currentversion=1 ORDER BY name" % (AUFTRAG_FIELDLIST,))        
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret

    
    def listOffeneAuftraege(self):
        ret = []
        self.db.execute("SELECT %s FROM auftrag WHERE currentversion=1 AND status=? ORDER BY zeitpunkt" % (AUFTRAG_FIELDLIST,), (StatusOffen,))
        result = self.db.fetchall()
        for item in result: 
            ret.append(self.ladeAuftrag(sqlresult = item))
        return ret
    
    
