# -* coding: utf-8 *-

doctype = '''<!DOCTYPE html>
'''

html_head = '''<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>%s</title>
    <script src="/static/jquery.js"></script>
    <script src="/static/jquery-ui/jquery-ui.min.js"></script>
    <link href="/static/jquery-ui/jquery-ui.min.css" rel="stylesheet">
    <script src="/static/fontawesome/svg-with-js/js/fontawesome-all.min.js"></script>
    <link href="/static/fontawesome/svg-with-js/css/fa-svg-with-js.css" rel="stylesheet">
    <script src="/static/bootstrap/js/bootstrap.min.js"></script>
    <link href="/static/bootstrap/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/style.css" rel="stylesheet">
    <script src="/static/script.js"></script> 
%s
</head>
'''
import web

def page(title=None, content=None, header_lines = ''):
    web.header('Content-Type','text/html; charset=utf-8', unique=True) 
    return doctype + html_head % (title, header_lines) + '<body>\n' + \
        '<p class="logout"><a class="btn btn-danger" href="/auth/logout">Sperren</a></p>\n' + content + '\n</body>'


def loginpage():
    session = web.config._session
    error = ''
    if session.get('errormessage', None):
        error = '<p class="error">%s</p>\n' % session.get('errormessage')
        del(session.errormessage)
    content = error + '''
<form method="post" action="/auth">
<p>Gesperrt: Bitte Code eingeben</p>
<p><label for="code">Code: </label><input type="number" name="code" id="code" /> <input type="submit" value="Anmelden" /></p>
</form>'''
    return page('Anmeldung', content, '<script>setTimeout(function () { $("#code").focus();}, 100);</script>')


