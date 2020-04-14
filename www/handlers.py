
import re, time, json, logging, hashlib, base64, asyncio

from webco import get, post

from models import User, Comment, Blog, next_id
from apis import Page

import util, apis

from aiohttp import web

from config import configs


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise apis.APIPermissionError()

#测试
@get('/test')
async def test(request):
    return {
        '__template__': 'test.html',
        '__user__': request.__user__
    }

#主页
@get('/')
async def index(request):
    blogs = await Blog.findAll()

    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        '__user__': request.__user__
    }

#获取用户
@get('/api/users')
async def api_get_users(*, page=1):
    # page_index = util.get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, int(page))
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='create_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.password = '******'
    return dict(page=p, users=users)

#注册页面
@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

#登记页面
@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

#编写日志页面
@get('/manage/blog/create')
def blog_add():
    return {
        '__template__': 'manage_blog_edit.html',
        'action': '/api/blogs'
    }

#编辑
@get('/manage/blogs/edit')
def blog_edit(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'action': '/api/manage/blog/edit',
        'id': id
    }

#管理日志页面
@get('/manage/blogs')
def manage_blogs(*, page=1):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': page
    }

#博客详细内容页面
@get('/blog/{id}')
async def blog_details(*, id):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'id miss')
    blog = await Blog.find(id)
    comments = await Comment.findAll('blog_id=?', [id])
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

#用户管理
@get('/manage/users')
def manage_users(*, page=1):
    return {
        '__template__': 'manage_users.html',
        'page_index': page
    }

#评论管理
@get('/manage/comments')
def manage_comments(*, page=1):
    return {
        '__template__': 'manage_comments.html',
        'page_index': page
    }

#用户注册接口
@post('/api/users')
async def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise apis.APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise apis.APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise apis.APIValueError('password')
    users = await User.findAll('email=?', [email])
    if users is not None:
        if len(users) > 0:
            raise apis.APIError('email is already register')
    uid = next_id()
    sha1_password = '%s:%s' % (uid, password)
    user = User(
        id = uid,
        name = name,
        email = email,
        password = hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(),
        image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest()
    )
    await user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#用户登录验证接口
@post('/api/authenticate')
async def authenticate(*, email, password):
    if not email:
        raise apis.APIValueError('email')
    if not password:
        raise apis.APIValueError('password')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise apis.APIValueError('email', 'email not found')
    user = users[0]
    password = '%s:%s' % (user.id, password)
    sha1 = hashlib.sha1()
    sha1.update(password.encode('utf-8'))
    old_password = sha1.hexdigest()
    if user.password != old_password:
        raise apis.APIValueError('password', 'error password')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=84000, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#退出登录
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

@asyncio.coroutine
async def auth_factory(app, handler):
    @asyncio.coroutine
    def auth(request):
        logging.info('check user: %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = yield from cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        return (yield from handler(request))
    return auth

# 解密cookie:
@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

#添加博客
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    # check_admin(request)
    if not name or not name.strip():
        raise apis.APIValueError('name')
    if not summary or not summary.strip():
        raise apis.APIValueError('summary')
    if not content or not summary.strip():
        raise apis.APIValueError('content')
    blog = Blog(
        user_id=request.__user__.id,
        user_name=request.__user__.name,
        user_image=request.__user__.image,
        name=name.strip(),
        summary=summary.strip(),
        content=content.strip()
    )
    await blog.save()
    return blog

#获取博客列表
@get('/api/blogs')
async def api_get_blogs(*, page=1):
    # page_index = util.get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, int(page))
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='create_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

#博客详细内容
@get('/api/blog/{id}')
async def blog(*, id):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'id miss')
    blog = await Blog.find(id)
    return blog

#删除博客
@post('/api/blogs/{id}/delete')
async def api_delete_blogs(*, id):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'miss id')
    await Blog.remove(Blog(id=id))
    return dict(success=True)

#编辑博客
@post('/api/manage/blog/edit')
async def api_edit_blogs(*, id, name, summary, content):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'miss id')
    blog = await Blog.find(id)
    if blog is None:
        raise apis.APIResourceNotFoundError('blog not found')
    blog.name = name
    blog.summary = summary
    blog.content = content
    await blog.update()
    return blog

#评论
@post('/api/blogs/{id}/comments')
async def api_add_blog_comment(request, *, id, content):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'miss id')
    if not content or not content.strip():
        raise apis.APIValueError('content', 'miss content')
    user = request.__user__
    if user is None:
        raise apis.APIPermissionError('user not login')
    blog = Blog.find(id)
    if blog is None:
        raise apis.APIResourceNotFoundError('blog not found')
    comment = Comment(id=next_id(), blog_id=id, user_id=user.id, user_name=user.name, user_image=user.image, content=content)
    await comment.save()
    return comment

#评论列表
@get('/api/comments')
async def api_list_comments(*, page=1):
    num = await Comment.findNumber('count(id)')
    p = Page(num, int(page))
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='create_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

#删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(*, id):
    if not id or not id.strip():
        raise apis.APIValueError('id', 'miss id')
    await Comment.remove(Comment(id=id))
    return dict(success=True)