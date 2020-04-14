import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 100), uuid.uuid4().hex)

class User(Model):
    __table__  = 'users'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    create_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    create_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    create_at = FloatField(default=time.time)

class Song(Model):
    __table__ = 't_song'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    song_id = StringField(ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    size = StringField(ddl='varchar(50)')
    artist_id = StringField(ddl='varchar(50)')
    lyric_id = StringField(ddl='varchar(50)')
    mp3_url = StringField(ddl='varchar(200)')
    origin = StringField(ddl='varchar(50)')
    num = IntegerField()
    hash_code = StringField(ddl='varchar(32)')

class artist(Model):
    __table__ = 't_artist'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    origin = StringField(ddl='varchar(50)')

