# -* coding: utf-8 *-

import web

from lib.Speicher import Speicher
from lib.webinterface import check_authenticated


def random_string(num):
    import random, string
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(num))


class auth:
    def GET(self):
        if check_authenticated(False):
            raise web.seeother('/')
        from . import html
        return html.loginpage()
        
    def POST(self):
        i = web.input(code="")
        session = web.config._session
        if i.code:
            session.authtoken = random_string(20)
            s = Speicher(authtoken=session.authtoken)
            if s.check_password(i.code):
                session.username = s.get_current_user()['name']
                target = session.get('redirect_after_login', None)
                if not target:
                    target = '/'
                raise web.seeother(target)
            else:
                session.errormessage = 'Falscher Code'
                raise web.seeother('/auth')
        else:
            raise web.seeother('/auth')


class logout:
    def GET(self):
        session = web.config._session
        session.kill()
        raise web.seeother('/auth')
