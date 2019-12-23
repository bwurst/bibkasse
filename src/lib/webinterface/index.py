# -* coding: utf-8 *-

import web

class index:
    def GET(self):
        web.seeother('/open')
