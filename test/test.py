import orm, asyncio
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop=loop, user='root', password='3344', db='python')
    u = User(name='zhangsan', email='test1@example.com', passwd='1234567890', image='about:blank')
    await u.save()

# loop = asyncio.get_event_loop()
# for x in test(loop):
#     pass
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test(loop))
# loop.run_forever()
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([test(loop)]))
loop.run_forever()