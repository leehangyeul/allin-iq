import asyncio,json,threading,http.server,functools,os
from playwright.async_api import async_playwright
import os
T=os.path.dirname(os.path.abspath(__file__))+'/'
WEB=os.environ.get('SITE',os.path.dirname(os.path.dirname(T.rstrip('/'))))
ADMIN='owner@example.com'
store={}
def start_server(port=8765):
    h=functools.partial(http.server.SimpleHTTPRequestHandler,directory=WEB)
    class Q(h.func):
        def log_message(self,*a):pass
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory=WEB));threading.Thread(target=srv.serve_forever,daemon=True).start();return srv
import re
accounts={};fails={}
def is_admin(u):return bool(u and u.get('emailVerified') and u.get('email')==ADMIN)
def is_player(u):return bool(u and isinstance(u.get('email'),str) and re.fullmatch(r'p[0-9a-f]{32}@players[.]allin-iq[.]app',u['email']))
def secret_code():return (store.get('secret/access') or {}).get('code')
def valid_name(n):return isinstance(n,str) and 1<=len(n)<=12 and '/' not in n
def owns(n,uid):return valid_name(n) and ('names/'+n.lower()) in store and store['names/'+n.lower()].get('uid')==uid
def is_member(uid):
    m=store.get('members/'+uid);return bool(m and 'secret/access' in store and m.get('code')==secret_code())
def blocked(uid):return uid in ((store.get('meta/block') or {}).get('ids') or {})
def num(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=1000000
def valid_score(d):
    try:return isinstance(d.get('name'),str) and 1<=len(d['name'])<=12 and all(num(d.get(k)) for k in ['hands','sum','best','dn','dsum','dbest']) and d['sum']<=d['hands']*100 and d['dsum']<=d['dn']*100
    except Exception:return False
def can_read(path,u):
    if not u:return False
    col,_,id=path.partition('/')
    if col=='secret':return is_admin(u)
    if col=='members':return u['uid']==id or is_admin(u)
    return col in ('meta','scores','names')
def can_write(path,d,u,delete=False):
    if not u:return False
    col,_,id=path.partition('/')
    if col in('meta','secret'):return is_admin(u)
    if col=='names':
        if delete:return is_admin(u)
        old=store.get(path)
        if old is None:
            return (is_player(u) or is_admin(u)) and set(d)<={'uid','name','gen','at'} and d.get('uid')==u['uid'] and d.get('gen')==0 and valid_name(d.get('name')) and d['name'].lower()==id
        if is_admin(u):return True
        rs=store.get('secret/rs_'+id)
        return is_player(u) and old.get('reset')==True and not blocked(old.get('uid')) and set(d)<={'uid','name','gen','at','prev','claim'} and d.get('uid')==u['uid'] and d.get('name')==old.get('name') and d.get('gen')==(old.get('gen') or 0)+1 and d.get('prev')==old.get('uid') and rs is not None and d.get('claim')==rs.get('t')
    if col=='members':
        if delete:return is_admin(u)
        return is_player(u) and u['uid']==id and set(d.keys())<= {'code','name','at'} and 'secret/access' in store and d.get('code')==secret_code() and owns(d.get('name'),id)
    if col=='scores':
        if delete:
            if is_admin(u):return True
            old=store.get(path) or {};n=old.get('name')
            return is_player(u) and valid_name(n) and ('names/'+n.lower()) in store and store['names/'+n.lower()].get('uid')==u['uid'] and store['names/'+n.lower()].get('prev')==id
        return is_admin(u) or (is_player(u) and u['uid']==id and is_member(id) and not blocked(id) and valid_score(d) and d.get('name')==store['members/'+id].get('name') and owns(d.get('name'),id))
    return False
pages=[];denied=[]
async def broadcast():
    for q in pages:
        try:await q.evaluate("(a)=>{window.__cache=JSON.parse(a);window.__notify&&window.__notify()}",json.dumps(store))
        except Exception:pass
async def mkpage(b,ident,vp=(390,900),delay=0,storage=None):
    ctx=await b.new_context(viewport={'width':vp[0],'height':vp[1]},storage_state=storage)
    pg=await ctx.new_page();pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    pg.on('console',lambda m:pg.errs.append('console:'+m.text) if m.type=='error' else None)
    for name,f in [('firebase-app','mock-app.js'),('firebase-auth','mock-auth2.js'),('firebase-firestore','mock-fs2.js')]:
        body=open(T+f,encoding='utf8').read()
        def mk(body):
            async def h(r):await r.fulfill(body=body,content_type='application/javascript',headers={'access-control-allow-origin':'*'})
            return h
        await pg.route(f'**/firebasejs/*/{name}.js',mk(body))
    await pg.route('**/*fonts.g*/**',lambda r:r.abort())
    cfgbody=open(T+'config.test.js',encoding='utf8').read()
    async def cfgh(r):await r.fulfill(body=cfgbody,content_type='application/javascript')
    await pg.route('**/config.js',cfgh)
    async def setf(path,d,u):
        d=json.loads(d);u=json.loads(u)
        if not can_write(path,d,u):denied.append(('set',path,u and u['uid']));return json.dumps({'ok':False})
        store[path]=d;asyncio.ensure_future(broadcast());return json.dumps({'ok':True})
    async def delf(path,u):
        u=json.loads(u)
        if not can_write(path,{},u,delete=True):denied.append(('del',path,u and u['uid']));return json.dumps({'ok':False})
        store.pop(path,None);asyncio.ensure_future(broadcast());return json.dumps({'ok':True})
    async def acct(op,email,pw,uid):
        if op=='create':
            if email in accounts:return json.dumps({'err':'auth/email-already-in-use'})
            accounts[email]={'pw':pw,'uid':uid};return json.dumps({'uid':uid})
        if op=='login':
            a=accounts.get(email)
            if fails.get(email,0)>=8:return json.dumps({'err':'auth/too-many-requests'})
            if not a or a['pw']!=pw:fails[email]=fails.get(email,0)+1;return json.dumps({'err':'auth/invalid-credential'})
            return json.dumps({'uid':a['uid']})
        if op=='delete':accounts.pop(email,None);return '{}'
    await pg.expose_function('__acct',acct)
    async def syncf():return json.dumps(store)
    await pg.expose_function('__sync',syncf)
    async def readf(path,u):return json.dumps(can_read(path,json.loads(u)))
    await pg.expose_function('__set',setf);await pg.expose_function('__del',delf);await pg.expose_function('__canRead',readf)
    await pg.add_init_script("window.__cache="+json.dumps(store)+";window.__ID="+json.dumps(ident)+";window.__delay="+str(delay)+";")
    pages.append(pg);await pg.goto('http://127.0.0.1:8765/index.html');await asyncio.sleep(.8);await broadcast();await asyncio.sleep(.3)
    return pg
