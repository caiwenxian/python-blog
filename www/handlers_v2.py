
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

    return {
        '__template__': 'v2/index.html',
        '__user__': request.__user__
    }

@get('/article')
async def article(request):

    return {
        '__template__': 'v2/article_list.html',
        '__user__': request.__user__
    }

@get('/photo')
async def photo(request):

    return {
        '__template__': 'v2/photo_list.html',
        '__user__': request.__user__
    }
