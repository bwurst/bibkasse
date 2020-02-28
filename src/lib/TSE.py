from lib.Config import config
from threading import Timer, Thread, Lock, Event
conf = config("tse")

import sys
import time
import logging
sys.path.insert(0, conf['library'])
import worm

TSEException = worm.WormException
log = logging.getLogger('bib.TSE')

class TSE():
    _tse = None
    _thread = None
    _stop = None
    _lock = None
    
    def __init__(self):
        self.master = False
        if not self.__class__._tse:
            log.info('start new TSE controller thread!')
            self.__class__._tse = worm.Worm(clientid=conf['clientid'], time_admin_pin=conf['timeadminpin'])
            self.__class__._lock = Lock()
            self.__class__._stop = Event()
            self.__class__._thread = Thread(target=self.worker)
            self.__class__._thread.start()
            self.master = True

    def worker(self):
        log.debug('this is the new TSE worker thread!')
        while not self.__class__._stop.is_set():
            log.debug('TSE: keep alive!')
            self.keepalive()
            try:
                timeout = 1500
                if not self.__class__._tse.info:
                    # Wenn die TSE nicht da ist, alle Minute prüfen
                    timeout = 60
                self.__class__._stop.wait(timeout)
            except TimeoutError:
                # 25 Minuten vorüber
                pass
        log.debug('TSE worker fertig.')
            
    def keepalive(self):
        with self.__class__._lock:
            try:
                if not self.__class__._tse or not self.__class__._tse.info:
                    log.debug('TSE war nicht korrekt initialisiert')
                    # TSE beim Start nicht vorhanden gewesen!
                    self.__class__._tse = worm.Worm(clientid=conf['clientid'], time_admin_pin=conf['timeadminpin'])
                    self.tse_prepare(adminpuk=conf['adminpuk'], adminpin=conf['adminpin'])
                if not self.info.hasPassedSelfTest or self.info.timeUntilNextSelfTest < 1500:
                    log.debug('TSE-Selbsttest ist jetzt nötig')
                    self.tse_runSelfTest()
                self.tse_updateTime()
            except TSEException as e:
                if e.errno == 2: # TSE nicht verfügbar
                    log.info('Keine TSE vorhanden')
                    pass
                elif e.errno == 0x1011: # client not registered
                    log.info('Die TSE meldet, dass diese Client-ID bisher nicht registriert ist')
                    self.tse_prepare(adminpuk=conf['adminpuk'], adminpin=conf['adminpin'])
        
            
    def __del__(self):
        if self.master:
            self.stop()
        else:
            log.debug('TSE: Beende nicht-master-objekt')

    def stop(self):
        log.debug('TSE: Signalisiere beenden')
        self.__class__._stop.set()

            
    def __getattr__(self, name):
        log.debug('TSE attribute fetched: %s' % (name,))
        return getattr(self.__class__._tse, name)


if __name__ == '__main__':
    tse = TSE()
    print('Signaturzähler: %s' % tse.info.createdSignatures)
    tse2 = TSE()
    print('Signaturzähler: %s' % tse2.info.createdSignatures)
    del(tse)
    del(tse2)
