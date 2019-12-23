# -* coding: utf-8 *-

from lib.Speicher import Speicher


def get_authtoken():
    import web
    session = web.config._session
    return session.get("authtoken", None)


def check_authenticated(redirect = True):
    import web 
    session = web.config._session
    authtoken = session.get('authtoken', None)
    if not authtoken:
        if redirect:
            session.redirect_after_login = web.ctx.path
            raise web.seeother('/auth')
        else:
            return False
    s = Speicher(authtoken=authtoken)
    username = session.get('username', None)
    if s.is_unlocked() and username:
        return True
    elif redirect:
        session.redirect_after_login = web.ctx.path
        raise web.seeother('/auth')
    return False



def start_webinterface():
    import threading
    
    start_web = False
    try:
        import web 
        start_web = True
    except:
        print ('web.py not installed! (python-webpy)')
    
    urls = (
        '/', 'lib.webinterface.index.index',
        '/auth', 'lib.webinterface.auth.auth',
        '/auth/logout', 'lib.webinterface.auth.logout',
        '/bio/lieferschein', 'lib.webinterface.bio.bio_lieferschein',
        '/open', 'lib.webinterface.currently_open.currently_open',
        '/open/([0-9]+)', 'lib.webinterface.currently_open.display_beleg',
        '/buchhaltung', 'lib.webinterface.daily_journal.daily_journal',
        '/buchhaltung/([0-9-]+)', 'lib.webinterface.daily_journal.daily_journal',
    )
    # static-Files werden hart über "/static" ausgeliefert. Das ist ein Ordner (oder Symlink) im Root
    # Wir legen das hier als symlink an, falls es nicht existiert.
    import os
    if not os.path.lexists('static') and os.path.isdir('ressource/web'):
        os.symlink('ressource/web', 'static')
    if not os.path.lexists('static/icons') and os.path.isdir('ressource/icons'):
        os.symlink('../icons', 'static/icons')
        
    
    if start_web:
        print ('starting web interface...')
        app = web.application(urls, globals())
        
        # Session-Workaround für Session-Nutzung im Debug-Modus
        if web.config.get('_session') is None:
            session = web.session.Session(app, web.session.DiskStore('sessions'), {})
            web.config._session = session
        else:
            session = web.config._session

        t = threading.Thread(target=app.run)
        t.setDaemon(True) # So the server dies with the main thread
        t.setName('webinterface')
        t.start()  
        print ('...done!')

