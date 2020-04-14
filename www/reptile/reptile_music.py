import requests
from bs4 import BeautifulSoup
from models import *
import asyncio

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
}

def test():
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
    }
    url = 'http://www.kugou.com/yy/rank/home/1-8888.html?from=rank'
    wb_data = requests.get(url, headers=headers)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    ranks = soup.select('.pc_temp_num')
    titles = soup.select('.pc_temp_songlist > ul > li > a')
    song_times = soup.select('.pc_temp_time')
    total = [];
    for rank, title, song_time in zip(ranks, titles, song_times):
        data = {
            'num': rank.get_text().strip(),
            'artist': title.get_text().split('-')[0].strip(),
            'name': title.get_text().split('-')[1].strip(),
            'size': song_time.get_text().strip(),
        }
        total.append(data)

def test2():
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
    }
    url = 'http://www.kugou.com/song/pm0w9e7.html'
    wb_data = requests.get(url, headers=headers)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    ranks = soup.select('.music')
    print(wb_data, ranks)

async def repileTop500Song(url):
    # url = 'http://www.kugou.com/yy/rank/home/1-8888.html?from=rank'
    wb_data = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    ranks = soup.select('.pc_temp_num')
    titles = soup.select('.pc_temp_songlist > ul > li > a')
    song_times = soup.select('.pc_temp_time')

    total = [];
    for rank, title, song_time in zip(ranks, titles, song_times):
        # data = {
        #     'num': rank.get_text().strip(),
        #     'artist': title.get_text().split('-')[0].strip(),
        #     'name': title.get_text().split('-')[1].strip(),
        #     'size': song_time.get_text().strip(),
        # }
        name = title.get_text().split('-')[1].strip()
        size=song_time.get_text().strip()
        num=rank.get_text().strip()
        details_url = title.get('href')
        print('details_url', details_url)
        song = Song(id=next_id(), name=name, size=size, num=num)
        # total.append(song)
        old = await Song.findAll('name=?', [name])
        if old is None or len(old) == 0:
            await song.save()

async def repileTop500SongFor24Page():
    urls = ['http://www.kugou.com/yy/rank/home/{}-8888.html?from=rank'.format(str(i)) for i in range(1, 2)]
    for url in urls:
        await repileTop500Song(url)
        time.sleep(100)

async def repileSong():
    url = 'http://www.kugou.com/yy/index.php?r=play/getdata&hash=BACB59D38E3F7E9DFD280F6B57FAAE61&album_id=&_=1505738969338'
    wb_data = requests.get(url, headers=HEADERS)
    # if wb_data.status == 1:
    #     hash_code = wb_data.data.hash_code
    #     old = await Song.findAll('hash_code=?', [hash_code])
    #     if old is not None and len(old) > 0:
    #         old.ma3_url = wb_data.data.play_url
    #         old.update()
    #     else:
    #         song = Song(id=next_id(), name=name, size=size, num=num)



if __name__ == '__main__':
    repileSong()


