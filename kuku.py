import argparse
import json
import os
import re
import requests
from mutagen.mp4 import MP4, MP4Cover
from urllib.parse import urlparse
import yt_dlp
from http.cookiejar import MozillaCookieJar


TITLE = "\r\n /$$   /$$           /$$                               /$$ /$$\r\n| $$  /$$/          | $$                              | $$| $$\r\n| $$ /$$/  /$$   /$$| $$   /$$ /$$   /$$          /$$$$$$$| $$\r\n| $$$$$/  | $$  | $$| $$  /$$/| $$  | $$ /$$$$$$ /$$__  $$| $$\r\n| $$  $$  | $$  | $$| $$$$$$/ | $$  | $$|______/| $$  | $$| $$\r\n| $$\\  $$ | $$  | $$| $$_  $$ | $$  | $$        | $$  | $$| $$\r\n| $$ \\  $$|  $$$$$$/| $$ \\  $$|  $$$$$$/        |  $$$$$$$| $$\r\n|__/  \\__/ \\______/ |__/  \\__/ \\______/          \\_______/|__/\r\n                      --by @bunnykek"

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,it-IT;q=0.7,it;q=0.6',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
}


class KuKu:
    def __init__(self, url: str) -> None:
        """
        __init__()

        initializes a session to be used to recieve API data from KukuFM/KukuTV.
        """
        parsed_url = urlparse(url)
        self.api_base = f"https://{parsed_url.netloc}" if parsed_url.netloc else "https://kukutv.app"
        self.showID = parsed_url.path.split('/')[-1]
        self.session = requests.Session()
        
        # Load and sanitize cookies, extracting JWT
        self.jwt = None
        temp_cookie_path = self.prepare_cookies()
        
        cookie_jar = MozillaCookieJar(temp_cookie_path)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        self.session.headers.update({
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'origin': 'https://kukutv.app',
            'referer': 'https://kukutv.app/',
            'package-name': 'com.vlv.web.reels',
            'preferred-lang': 'hindi',
            'x-source-service': 'nodejs-web',
        })
        self.session.cookies.update(cookie_jar)

        # Clean up the temporary cookie file
        if os.path.exists(temp_cookie_path):
            try:
                os.unlink(temp_cookie_path)
            except:
                pass

        if self.jwt:
            self.session.headers['Authorization'] = f'jwt {self.jwt}'
            # Also ensure jwtToken is set explicitly in cookies for safety
            self.session.cookies.set('jwtToken', self.jwt, domain='.kukutv.app')

        response = self.session.get(
            f"{self.api_base}/api/v2.3/channels/{self.showID}/episodes/?page=1")
        data = response.json()

        show: dict = data['show']
        # print(show)
        self.metadata = {
            'title': KuKu.sanitiseName(show['title'].strip()),
            'image': show['original_image'],
            'date': show['published_on'],
            'fictional': show['is_fictional'],
            'nEpisodes': show['n_episodes'],
            'author': show['author']['name'].strip(),
            'lang': show['language'].capitalize().strip(),
            'type': ' '.join(show['content_type']['slug'].strip().split('-')).capitalize(),
            'ageRating': show.get('meta_data', {}).get('age_rating', None),
            'credits': {},
            'hasVideoEps': "video_thumbnail" in show["other_images"]
        }

        album_info = F"""Album info:
                Name       : {self.metadata['title']}                  
                Author     : {self.metadata['author']}
                Language   : {self.metadata['lang']}
                Date       : {self.metadata['date']}
                Age rating : {self.metadata['ageRating']}
                Episodes   : {self.metadata['nEpisodes']}
                Video Eps  : {self.metadata['hasVideoEps']}
        """

        print(album_info)

        for credit in show['credits'].keys():
            self.metadata['credits'][credit] = ', '.join(
                [person['full_name'] for person in show['credits'][credit]])

    @staticmethod
    def sanitiseName(name) -> str:
        return re.sub(r'[:]', ' - ', re.sub(r'[\\/*?"<>|$]', '', re.sub(r'[ \t]+$', '', str(name).rstrip())))

    def prepare_cookies(self) -> str:
        """Reads cookies.txt, extracts JWT, duplicates domain cookies for CDNs, and returns path to temporary cookie file."""
        import tempfile
        cookie_file = 'cookies.txt'
        if not os.path.exists(cookie_file):
            # Create an empty temporary cookie file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
                return tmp.name
                
        with open(cookie_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        new_lines = []
        target_domains = [
            '.kukutv.app',
            '.kukufm.com',
            '.cloudfront.net',
            'd1l07mcd18xic4.cloudfront.net',
            'media.cdn.kukufm.com'
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                domain = parts[0]
                flag = parts[1].upper()
                name = parts[5]
                value = parts[6]
                
                if name == 'jwtToken':
                    self.jwt = value.strip()
                
                # Duplicate this cookie for all target domains to prevent CloudFront 403 errors
                for target in target_domains:
                    new_parts = list(parts)
                    new_parts[0] = target
                    new_parts[1] = 'TRUE' if target.startswith('.') else 'FALSE'
                    new_lines.append('\t'.join(new_parts) + '\n')
            else:
                new_lines.append(line)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.writelines(new_lines)
            return tmp.name

    def downloadAndTag(self, episodeMetadata: dict, path: str, srtPath: str, coverPath: str) -> None:
        """
        downloadAndTag()

        Method to download and tag locally using the KukuFM API and FFMPEG

        @param episodeMetadata: dict object that includes the track metadata.
        @param path: str which sets a path to be downloaded to.
        @param srtPath: str which sets the subtitle file path.
        @param coverPath: str path which locates where cover art is, so it'll be embeded within the file.
        """
        print('Downloading', episodeMetadata['title'], flush=True)
        if os.path.exists(path):
            print(episodeMetadata['title'], 'already exists!', flush=True)
            return

        temp_cookie_path = self.prepare_cookies()

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': path,
            'http_headers': HEADERS,
            'quiet': False,
            'no_warnings': False,
            'cookiefile': temp_cookie_path,
            'hls_prefer_native': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([episodeMetadata['url']])

        if os.path.exists(temp_cookie_path):
            try:
                os.unlink(temp_cookie_path)
            except:
                pass

        hasLyrics: bool = len(episodeMetadata['srt'])

        if hasLyrics:
            srt_response = self.session.get(episodeMetadata['srt'])
            with open(srtPath, 'w', encoding='utf-8') as f:
                f.write(srt_response.text)

        tag = MP4(path)

        # if hasLyrics:
        #     tag['\xa9lyr'] = [KuKu.srt_to_custom_format(srt_response.text)]
        tag['\xa9alb'] = [self.metadata['title']]
        tag['\xa9ART'] = [self.metadata['author']]
        tag['aART'] = [self.metadata['author']]
        tag['\xa9day'] = [episodeMetadata['date'][0:10]]
        tag['trkn'] = [(int(episodeMetadata['epNo']),
                        int(self.metadata['nEpisodes']))]
        tag['stik'] = [2]
        tag['\xa9nam'] = [episodeMetadata['title']]
        tag.pop("©too")

        tag['----:com.apple.iTunes:Fictional'] = bytes(
            str(self.metadata["fictional"]), 'UTF-8')
        tag['----:com.apple.iTunes:Author'] = bytes(
            str(self.metadata["author"]), 'UTF-8')
        tag['----:com.apple.iTunes:Language'] = bytes(
            str(self.metadata["lang"]), 'UTF-8')
        tag['----:com.apple.iTunes:Type'] = bytes(
            str(self.metadata["type"]), 'UTF-8')
        tag['----:com.apple.iTunes:Season'] = bytes(
            str(episodeMetadata["seasonNo"]), 'UTF-8')
        if self.metadata["ageRating"]:
            tag['----:com.apple.iTunes:Age rating'] = bytes(
                str(self.metadata["ageRating"]), 'UTF-8')

        for cat in self.metadata['credits'].keys():
            credit = cat.replace('_', ' ').capitalize()
            tag[f'----:com.apple.iTunes:{credit}'] = bytes(
                str(self.metadata['credits'][cat]), 'UTF-8')
        with open(coverPath, 'rb') as f:
            pic = MP4Cover(f.read())
            tag['covr'] = [pic]
        tag.save()

    def downAlbum(self) -> None:
        """
        downAlbum()

        Method where it'll prepare a storyID to be stored onto locally.
        """
        folderName = f"{self.metadata['title']} "
        folderName += f"({self.metadata['date'][:4]}) " if self.metadata.get(
            'date') else ''
        folderName += f"[{self.metadata['lang']}]"

        albumPath = os.path.join(
            os.getcwd(), 'Downloads', self.metadata['lang'], self.metadata['type'], self.sanitiseName(folderName))

        if not os.path.exists(albumPath):
            os.makedirs(albumPath)

        with open(os.path.join(albumPath, 'cover.png'), 'wb') as f:
            f.write(self.session.get(self.metadata['image']).content)

        episodes = []
        page = 1

        while True:
            response = self.session.get(
                f'{self.api_base}/api/v2.3/channels/{self.showID}/episodes/?page={page}')
            data = response.json()
            episodes.extend(data["episodes"])
            page += 1

            if not data["has_more"]:
                break

        for ep in episodes:
            hls_url = ep['content'].get('hls_url', '').strip()
            audio_url = ep['content'].get('premium_audio_url', '').strip()
            stream_url = hls_url or audio_url

            print(f"  Ep {ep['index']:02d}: hls_url={'YES' if hls_url else 'EMPTY'} | audio_url={'YES' if audio_url else 'EMPTY'} | locked={ep.get('is_play_locked')}")

            if not stream_url:
                print(f"  [SKIP] No stream URL available for episode {ep['index']}")
                continue

            epMeta = {
                'title': KuKu.sanitiseName(ep["title"].strip()),
                'url': stream_url,
                'srt': ep['content'].get('subtitle_url', "").strip(),
                'epNo': ep['index'],
                'seasonNo': ep['season_no'],
                'date': str(ep.get('published_on')).strip(),
            }

            trackPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.{'mp4' if self.metadata['hasVideoEps'] else 'm4a'}")
            srtPath = os.path.join(
                albumPath, f"{str(ep['index']).zfill(2)}. {epMeta['title']}.srt")
            self.downloadAndTag(epMeta, trackPath, srtPath,
                                os.path.join(albumPath, 'cover.png'))


if __name__ == '__main__':
    print(TITLE)
    parser = argparse.ArgumentParser(
        prog='kuku-dl',
        description='KuKu FM Downloader!',
    )
    parser.add_argument('url', help="Show Url")
    args = parser.parse_args()
    KuKu(args.url).downAlbum()
