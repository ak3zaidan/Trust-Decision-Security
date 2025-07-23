from curl_cffi import requests
from javascript import require
import urllib.parse
import requests_go
import subprocess
import tls_client
import hashlib
import random
import base64
import mmh3
import json
import math
import time

VERSION_USE = "4.1.3"
USE_CHARLES_PROXY = False
USE_CIFI = False
USE_TLS_CLIENT = False
USE_GO_CLIENT = True

# Recalculate key and sign for the new endpoint and path

def Calculate(tokenId, ua, path, endpoint, webGl, region, endpointNoQuery, fingerprint):
    try:
        asyncFun = require(jsFileForRegion(region))
    except Exception as e:
        print(f"Failed to init js: {e}")
        return "", ""

    body = makeBody(ua, endpoint, webGl)

    try:
        fingerprint = json.loads(fingerprint)
    except Exception as e:
        print(f"Failed to init fp: {e}")
        return "", ""
    
    if VERSION_USE == "4.0.7":
        fingerprint['b']['b'][17] = urlEscape(endpointNoQuery)
    
    regionData = get_popmart_country_data(region)

    result = asyncFun['asyncSign'](tokenId, path, body, fingerprint, regionData["appkey"], regionData["fpRegion"])
    
    return result['td-session-sign'], result['td-session-key']

# For a new session call this

class Solver:
    def __init__(self, proxy, path, endpoint, ua, secChUa, chromeFullVersion, region, ip, endpointNoQuery):

        self.proxy_url = None
        self.proxy = None
        
        if USE_CHARLES_PROXY:
            self.proxy_url = "http://localhost:8888"

            self.proxy = {
                "http": self.proxy_url,
                "https": self.proxy_url
            }
        elif proxy:
            host, port, username, password = parse_proxy(proxy)
            self.proxy_url = f"http://{username}:{password}@{host}:{port}"

            self.proxy = {
                "http": self.proxy_url,
                "https": self.proxy_url
            }            
        
        self.path = path
        self.endpoint = endpoint
        self.ua = ua
        self.secChUa = secChUa
        self.chromeFullVersion = chromeFullVersion

        self.webGl = random.choice(webgls)
        self.region = region.lower()
        self.endpointNoQuery = endpointNoQuery

        regionData = get_popmart_country_data(region)

        self.namespace = regionData["namespace"]
        self.clientKey = regionData["clientKey"]
        self.country = regionData["country"]
        self.projectId = regionData["projectId"]
        self.lang = regionData["lang"]
        self.appkey = regionData["appkey"]
        self.timezone = regionData["timezone"]
        self.acceptLang = regionData["acceptLang"]
        self.fpRegion = regionData["fpRegion"]

        if VERSION_USE == "4.1.3":
            self.fingerprint = fingerprint_US_413(self.appkey, endpoint, ua, self.acceptLang, chromeFullVersion, self.timezone, self.webGl, ip, endpointNoQuery, self.fpRegion)
        elif VERSION_USE == "4.1.1":
            self.fingerprint = fingerprint_US_411(self.appkey, endpoint, ua, self.acceptLang, chromeFullVersion, self.timezone, self.webGl, ip, endpointNoQuery)
        elif VERSION_USE == "4.0.7":
            self.fingerprint = fingerprint_US_407(self.appkey, endpoint, ua, self.acceptLang, chromeFullVersion, self.timezone, self.webGl, ip, endpointNoQuery)
        elif VERSION_USE == "4.0.6":
            self.fingerprint = fingerprint_US_406(self.appkey, endpoint, ua, self.acceptLang, chromeFullVersion, self.timezone, self.webGl, ip, endpointNoQuery)
        
        try:
            self.asyncFun = require(jsFileForRegion(region))
        except Exception as e:
            raise Exception(f"Failed to init js: {str(e)}")

    # Depreciated
    def getDid(self):
        TDKey = self.asyncFun['asyncSessionKey'](self.fingerprint, self.appkey, self.fpRegion)

        path = '/shop/v1/home/loginRegistrationLandingPage'

        body = makeBody(self.ua, f'https://www.popmart.com/{self.region}', self.webGl)

        params = { "did" : "" }

        client_data = self.asyncFun['asyncSignDid']("", path, body, params, 'post', self.fingerprint, self.clientKey, self.appkey, self.fpRegion)

        url = 'https://prod-global-api.popmart.com/customer/v1/customer/app'

        params.update({"s": client_data['s']['s'], "t": int(client_data['s']['t'])})

        headers = {
            "content-length": f'{len(json.dumps(params))}',
            "language": self.lang,
            "sec-ch-ua-platform": "\"Windows\"",
            "x-project-id": self.projectId,
            "x-device-os-type": "web",
            "sec-ch-ua": self.secChUa,
            "td-session-sign": client_data['td-session-sign'],
            "sec-ch-ua-mobile": "?0",
            "grey-secret": "null",
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "td-session-query": "",
            "x-client-country": self.country,
            "td-session-key": TDKey,
            "tz": self.timezone,
            "td-session-path": "/customer/v1/customer/app",
            "country": self.country,
            "did": "",
            "x-sign": client_data['x-sign'],
            "clientkey": self.clientKey,
            "user-agent": self.ua,
            "x-client-namespace": self.namespace,
            "origin": "https://www.popmart.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.popmart.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": self.acceptLang,
            "priority": "u=1, i"
        }

        if self.proxy:
            response = requests_go.post(url, headers=headers, json=params, proxies=self.proxy)
        else:
            response = requests_go.post(url, headers=headers, json=params, proxies=self.proxy)

        if USE_CHARLES_PROXY:
            print(f'\nGet DID response: {response.status_code}')

        if response.status_code == 200:
            return response.json()['data']['did']
        else:
            return None

    def postFingerprint(self):
        domain = f'{self.fpRegion}-ppfp.apitd.net'

        if self.fpRegion != "us":
            domain = f'{self.fpRegion}-fp.apitd.net'

        url = f'https://{domain}/web/v2?partner=popmart&appKey={self.appkey}'

        data = {
            'data': self.asyncFun['asyncData'](
                self.fingerprint, 
                self.appkey,
                self.fpRegion
            )
        }

        if USE_GO_CLIENT:
            headers = {
                "Host": domain,
                "Connection": "keep-alive",
                "sec-ch-ua-platform": "\"Windows\"",
                "User-Agent": self.ua,
                "sec-ch-ua": self.secChUa,
                "Content-Type": "application/x-www-form-urlencoded",
                "sec-ch-ua-mobile": "?0",
                "Accept": "*/*",
                "Origin": "https://www.popmart.com",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.popmart.com/",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9"
            }
        else:
            headers = {
                "Host": domain,
                "Connection": "keep-alive",
                "Content-Length": f'{len(json.dumps(data))}',
                "sec-ch-ua-platform": "\"Windows\"",
                "User-Agent": self.ua,
                "sec-ch-ua": self.secChUa,
                "Content-Type": "application/x-www-form-urlencoded",
                "sec-ch-ua-mobile": "?0",
                "Accept": "*/*",
                "Origin": "https://www.popmart.com",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.popmart.com/",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9"
            }

        header_order = [
            "Host",
            "Connection",
            "Content-Length",
            "sec-ch-ua-platform",
            "User-Agent",
            "sec-ch-ua",
            "Content-Type",
            "sec-ch-ua-mobile",
            "Accept",
            "Origin",
            "Sec-Fetch-Site",
            "Sec-Fetch-Mode",
            "Sec-Fetch-Dest",
            "Referer",
            "Accept-Encoding",
            "Accept-Language"
        ]


        if USE_GO_CLIENT:
            input_data = {
                "url": url,
                "data": urllib.parse.urlencode(data),
                "headers": headers,
                "header_order": header_order,
                "proxy_url": self.proxy_url
            }

            result = subprocess.run(
                ["go", "run", "goreq.go"],
                input=json.dumps(input_data).encode(),
                capture_output=True
            )

            if result.returncode != 0:
                return None, f"Go client error: {result.stderr.decode()}"
                        
            response = json.loads(result.stdout.decode())

            return self.asyncFun['asyncDecData'](response, self.appkey, self.fpRegion), ""
        elif USE_TLS_CLIENT:
            session = tls_client.Session(
                client_identifier="chrome_120",
                header_order=header_order,
                random_tls_extension_order=True
            )

            response = session.post(
                url,
                headers=headers,
                data=data,
                proxy=self.proxy_url
            )
        elif USE_CIFI:
            session = requests.Session(impersonate="chrome133a", proxies=self.proxy)

            response = session.post(
                url,
                headers=headers,
                data=data,
                default_headers=False,
            )
        else:
            tls = requests_go.tls_config.TLSConfig()

            tls.random_ja3 = True

            tls.headers_order = header_order

            if self.proxy:
                if USE_CHARLES_PROXY:
                    response = requests_go.post(url, headers=headers, data=data, proxies=self.proxy, verify=False, tls_config=tls)
                else:
                    response = requests_go.post(url, headers=headers, data=data, proxies=self.proxy, tls_config=tls)
            else:
                response = requests_go.post(url, headers=headers, data=data, tls_config=tls)


        if USE_CHARLES_PROXY:   
            print(f'\nPost FP response: {response.status_code}')

        if response.status_code == 200:
            return self.asyncFun['asyncDecData'](response.json(), self.appkey, self.fpRegion), ""
        else:
            return None, f'Error posting fp with status {response.status_code}'

    def makeSession(self, retry):
        try:
            data, postErr = self.postFingerprint()

            if data is None or data['tokenId'] is None:
                if retry:
                    print(postErr)
                    return self.makeSession(False)
                else:
                    print(postErr)
                    return "", "", None, "", "", ""
                        
            tokenId = data['tokenId']

            body = makeBody(self.ua, self.endpoint, self.webGl)

            client_data = self.asyncFun['asyncSign'](tokenId, self.path, body, self.fingerprint, self.appkey, self.fpRegion)

            return "", tokenId, json.dumps(self.fingerprint), client_data["td-session-key"], client_data["td-session-sign"], self.webGl

        except Exception as e:
            if retry:
                return self.makeSession(False)
            else:
                print(f'Failed with err: {str(e)}')
                return "", "", None, "", "", ""

# Fingerprints

def fingerprint_US_413(appKey, endpoint, ua, acceptLang, chromeFullVersion, timezone, webGl, ip, endpointNoQuery, fpRegion):
    timestamp = int(time.time() * 1000)
    timestampString = str(timestamp)

    timeZoneOffeset = -tzOffset(timezone)

    multiples_of_10 = list(range(1300, 1551, 10))
    screenWidth = random.choice(multiples_of_10)

    innerHeight = random_int(850, 950)
    innerWidth = random_int(1850, 1950)

    deviceMemory = random.choice([2, 4, 8, 16])
    hardwareConcurrency = random.choice([16, 24, 28, 32])

    shortChromeVersion = chromeVersion(chromeFullVersion)
    shortLang = lang(acceptLang)
    
    ua_cleaned = ua.replace("Mozilla/", "")
    userAgentHash = MurmurHash(ua_cleaned)

    fonts = detect_fonts()
    plugs = MurmurHash(generate_random_pdf_viewers())
    pdf = MurmurHash(generate_random_mime_pdf_types())
    canvas1 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAACACAYAAADktbcKAAAAAXNSR0IArs4c6QAACidJREFUeF7tnU1oXUUUx2cSgiiIiAgWv8AiXVSoCEXEhS+IiCgoiIgoKAi6qKAgKOKit4IuCioIuiioIOiioIKgi4LmIeiigaQ0tS1pTWpaa6nSSlvbWkueuUlf+/L63su9d2bunJn5dePCe+fj/z/nlzln3ku04h8KoECyCuhkd87GUQAFFAAgCFAgYQUAQMLms3UUAADEAAokrAAASNh8to4CAIAYQIGEFQAACZvP1lEAABADKJCwAgAgYfPZOgoAAGIABRJWAAAkbD5bRwEAQAygQMIKAICEzWfrKAAAiAEUSFgBAJCw+WwdBQAAMYACCSsAABI2P996q6U2aq02JS5DstsHAMlav5j8DaXUmFJqVGvVTFiKZLcOAJK1Xqn5lhrTahECTa" + get_random_string(20) + "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")
    canvas2 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAAAAXNSR0IArs4c6QAAEwBJREFUeF7tm3tYVWW+x39rc9kKbEBFDc0biijuJxUQuQR5w+voKJahp5kK5WI92mM1OZOZx7HGZ5ysxprDzfDYlJcYrSGVAa+ZpiJqgkoHC0FEDARFlNve7HXOu/Ze+2w2mJexGV7fL//oYu+91u/3+fJ+eN93LSRZlmVJkiTCFwiAAAh0cAIQVQcP6OcoT44n+ec4b0c/p5RK+Hnv6CHdoT4EyHmA91M+hHU/1PCZjkAAwuoIKfyLa4Cw/sXAcbkHRgDCemAo+TkRhMVPVqi0NYH/F1ZiUm8yaQ6TJL9MKYnb24Ayv55FGtMCSl6YS/bH90M29iMdObRsIYeWlco5bY9l6VGSpW3KaSV5OaUkvnXXl2DncTTuIqLHiaiUNKZwSl5Yftefv5" + get_random_string(20) + "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")
    current_time_hash = hashlib.md5(str(int(time.time() * 1000)).encode()).hexdigest()

    fingerprint = {
        "bb": {"v": "4.1.3", "os": 3, "p": "popmart"},
        "pageInfo": {},
        "q": {"partner": "popmart", "appKey": appKey},
        "b": {
            "a": [
                timestampString, "Win32", innerHeight, innerWidth,
                canvas2, 0, timeZoneOffeset,
                urlEscape(endpoint),
                innerWidth, shortLang, "1", innerWidth, 1, "true_0_1_Infinity", "-",
                "functiongetParameter(){[nativecode]}", chromeFullVersion, "Google Chrome", "-",
                pdf, "-", ""
            ],
            "b": [
                shortLang, "-", "-",
                MurmurHash(fonts[0]) + "|" + fonts[1],
                1080, 1032, "-", "-",
                fullGl(webGl),
                "[object Window]", "5,5,5,5", "-", "-",
                "0_Windows_Not)A;Brand_8_Chromium_138_Google Chrome_138", "-",
                shortLang + "|" + timezone,
                "0|131|3|1|5|" + MurmurHash(get_random_string(20)) + "|" + fpRegion + "/" + appKey,
                ""
            ],
            "c": [
                "-", plugs, 0, "0",
                "Netscape", "11110", "301023", "-", 1032, hardwareConcurrency,
                generate_random_audio_context_string(), "0", "-", "162",
                chromeFullVersion, "-", "19.0.0", 12442, "-", ""
            ],
            "d": [
                "-", innerWidth,
                ua,
                userAgentHash, "-", innerHeight, "-", 1905, "Mozilla",
                canvas1 + "|2a1e5eb90a4f6a3425748083d32a15bc",
                "Webkit-Chrome", "functiongetoffsetHeight(){[nativecode]}",
                MurmurHash(get_random_string(20)), "UTF-8", "-", "-", "-",
                random_ip() + "|", ""
            ],
            "g": [
                "-", "",
                "functiontoDataURL(){[nativecode]}", "functionRTCPeerConnection(){[nativecode]}",
                "1", hardwareConcurrency, deviceMemory, "functiontoString(){[nativecode]}", deviceMemory, 33,
                "functionenumerateDevices(){[nativecode]}", hardwareConcurrency, "1", "[objectPluginArray]",
                "functioncreateAnalyser(){[nativecode]}", "-", "1696.5823364257812", "2188489447__",
                "-", "-", "-", "627_54_749_0", ""
            ],
            "f": "1^^1^^0^^0^^0^^0",
            "e": ""
        },
        "wb": ""
    }
    
    return fingerprint

def fingerprint_US_411(appKey, endpoint, ua, acceptLang, chromeFullVersion, timezone, webGl, ip, endpointNoQuery):
    timestamp = int(time.time() * 1000)
    timestampString = str(timestamp)

    timeZoneOffeset = -tzOffset(timezone)

    multiples_of_10 = list(range(1300, 1551, 10))
    screenWidth = random.choice(multiples_of_10)

    innerHeight = random_int(850, 950)
    innerWidth = random_int(1850, 1950)

    deviceMemory = random.choice([2, 4, 8, 16])
    hardwareConcurrency = random.choice([16, 24, 28, 32])

    shortChromeVersion = chromeVersion(chromeFullVersion)
    shortLang = lang(acceptLang)
    
    ua_cleaned = ua.replace("Mozilla/", "")
    userAgentHash = MurmurHash(ua_cleaned)

    fonts = detect_fonts()
    plugs = MurmurHash(generate_random_pdf_viewers())
    pdf = MurmurHash(generate_random_mime_pdf_types())
    canvas1 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAACACAYAAADktbcKAAAAAXNSR0IArs4c6QAACidJREFUeF7tnU1oXUUUx2cSgiiIiAgWv8AiXVSoCEXEhS+IiCgoiIgoKAi6qKAgKOKit4IuCioIuiioIOiioIKgi4LmIeiigaQ0tS1pTWpaa6nSSlvbWkueuUlf+/L63su9d2bunJn5dePCe+fj/z/nlzln3ku04h8KoECyCuhkd87GUQAFFAAgCFAgYQUAQMLms3UUAADEAAokrAAASNh8to4CAIAYQIGEFQAACZvP1lEAABADKJCwAgAgYfPZOgoAAGIABRJWAAAkbD5bRwEAQAygQMIKAICEzWfrKAAAiAEUSFgBAJCw+WwdBQAAMYACCSsAABI2P996q6U2aq02JS5DstsHAMlav5j8DaXUmFJqVGvVTFiKZLcOAJK1Xqn5lhrTahECTa" + get_random_string(20) + "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")
    canvas2 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAAAAXNSR0IArs4c6QAAEwBJREFUeF7tm3tYVWW+x39rc9kKbEBFDc0biijuJxUQuQR5w+voKJahp5kK5WI92mM1OZOZx7HGZ5ysxprDzfDYlJcYrSGVAa+ZpiJqgkoHC0FEDARFlNve7HXOu/Ze+2w2mJexGV7fL//oYu+91u/3+fJ+eN93LSRZlmVJkiTCFwiAAAh0cAIQVQcP6OcoT44n+ec4b0c/p5RK+Hnv6CHdoT4EyHmA91M+hHU/1PCZjkAAwuoIKfyLa4Cw/sXAcbkHRgDCemAo+TkRhMVPVqi0NYH/F1ZiUm8yaQ6TJL9MKYnb24Ayv55FGtMCSl6YS/bH90M29iMdObRsIYeWlco5bY9l6VGSpW3KaSV5OaUkvnXXl2DncTTuIqLHiaiUNKZwSl5Yftefv5" + get_random_string(20) + "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")
    current_time_hash = hashlib.md5(str(int(time.time() * 1000)).encode()).hexdigest()

    fingerprint = {
        'bb': {
            'v': '4.1.1',
            'os': 3,
            'p': 'popmart'
        },
        'pageInfo': {},
        'q': {
            'partner': 'popmart',
            'appKey': appKey
        },
        'b': {
            'a': [
                shortLang,
                MurmurHash(fonts[0]) + "|" + fonts[1],
                innerWidth,
                '-',
                ua,
                1,
                innerHeight,
                shortLang,
                1905,
                innerWidth,
                '-',
                'Webkit-Chrome',
                'functiongetParameter(){[nativecode]}',
                chromeFullVersion,
                '5,5,5,5,5,5,5,5',
                '-',
                '19.0.0',
                12431,
                '-',
                "" # Timestamp set in JS
            ],
            'b': [
                '-',
                'Win32',
                innerHeight,
                '0',
                plugs,
                '-',
                timeZoneOffeset,
                hardwareConcurrency,
                urlEscape(endpoint),
                userAgentHash,
                timestampString, # Timestamp updated in JS
                '1',
                '0',
                '[object Window]',
                'functiongetoffsetHeight(){[nativecode]}',
                '-',
                'Google Chrome',
                'UTF-8',
                '-',
                '-',
                "" # Timestamp set in JS
            ],
            'c': [
                '-',
                innerWidth,
                canvas2,
                '-',
                '300109',
                '11110',
                1032,
                generate_random_audio_context_string(),
                innerWidth,
                1032,
                '-',
                'Mozilla',
                1080,
                canvas1 + "|" + generate_x_sign(current_time_hash),
                '1880389533__',
                '82e4ba81d38ec2241248f7be82f44fc0',
                '-',
                '-',
                '348_53_1828_1',
                '-',
                "" # Timestamp set in JS
            ],
            'd': [
                'true_0_1_Infinity',
                0,
                'Netscape',
                0,
                '-',
                '-',
                '-',
                fullGl(webGl),
                'functioncreateAnalyser(){[nativecode]}',
                '-',
                '1144',
                '-',
                pdf,
                "0_Windows_Google Chrome_137_Chromium_137_Not/A)Brand_24",
                '-',
                shortLang + "|" + timezone,
                '-',
                '0|3||1|',
                "" # Timestamp set in JS
            ],
            'g': [
                '1',
                deviceMemory,
                'functiontoString(){[nativecode]}',
                'functiontoDataURL(){[nativecode]}',
                '',  # Set in JS Client Key
                '[objectPluginArray]',
                33,
                '-',
                hardwareConcurrency,
                'functionRTCPeerConnection(){[nativecode]}',
                deviceMemory,
                'functionenumerateDevices(){[nativecode]}',
                '1',
                hardwareConcurrency,
                '-',
                '-',
                '1696.5823364257812',
                chromeFullVersion,
                '-',
                '-',
                "" # Timestamp set in JS
            ],
            'f': '1^^1^^0^^0^^0^^0',
            'e': ""
        },
        'wb': ''
    }
    
    return fingerprint

def fingerprint_US_407(appKey, endpoint, ua, acceptLang, chromeFullVersion, timezone, webGl, ip, endpointNoQuery):
    timestamp = int(time.time() * 1000)
    timestampString = str(timestamp)

    customTime = int(time.time() * 1000)
    timeZoneOffeset = -tzOffset(timezone)

    screenWidth = random_int(1800, 1950)
    innerHeight = random_int(850, 950)

    deviceMemory = random.choice([2, 4, 8, 16])
    hardwareConcurrency = random.choice([4, 6, 8, 12, 16, 32]) 

    shortChromeVersion = chromeVersion(chromeFullVersion)
    shortLang = lang(acceptLang)
    
    ua_cleaned = ua.replace("Mozilla/", "")
    userAgentHash = MurmurHash(ua_cleaned)

    fingerprint = {
        "bb": {
            "v": "4.0.7",
            "os": 3
        },
        "pageInfo": {},
        "q": {
            "partner": "popmart",
            "appKey": appKey
        },
        "b": {
            "a": [
                innerHeight,
                random_int(1900, 1920),
                "11110",
                1080,
                screenWidth,
                1026,
                userAgentHash,  # O0Q0o["hash128"](oOoQo) oOoQo='5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
                shortLang,
                1,
                fullGl(webGl),
                "functiongetoffsetHeight(){[nativecode]}",
                "5e146044c25118d19ae72af44784f4f1",
                "-",
                "UTF-8",
                "-",
                f'0_Windows_Google Chrome_{shortChromeVersion}_Not-A.Brand_8_Chromium_{shortChromeVersion}',
                "-",
                shortLang + "|" + timezone,
                to_base32(customTime - 98)
            ],
            "b": [
                MurmurHash(generate_random_pdf_viewers()), # O0Q0o["hash128"](oOoQo) oOoQo='5,ChromePDFViewerPortableDocumentFormatinternal-pdf-viewer2,ChromiumPDFViewerPortableDocumentFormatinternal-pdf-viewer2,MicrosoftEdgePDFViewerPortableDocumentFormatinternal-pdf-viewer2,PDFViewerPortableDocumentFormatinternal-pdf-viewer2,WebKitbuilt-inPDFPortableDocumentFormatinternal-pdf-viewer2'
                3,
                MurmurHash(longImage + base64.b64encode(get_random_string(200).encode('utf-8')).decode('utf-8')), # O0Q0o["hash128"](oOoQo) oOoQo='data:image/png;base64,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'
                innerHeight,
                "-",
                "-",
                1905,
                generate_random_audio_context_string(),
                "-",
                # 4243a3083db2b12a9eed215c0602a5c3=O0Q0o["hash128"](QOO00) QOO00='data:image/png;base64,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'
                # 2a1e5eb90a4f6a3425748083d32a15bc=O0Q0o["hash128"](QOO00)  QOO00='000000000....'
                MurmurHash(longImage2 + base64.b64encode(get_random_string(200).encode('utf-8')).decode('utf-8')) + "|2a1e5eb90a4f6a3425748083d32a15bc",
                "[object Window]",
                "functioncreateAnalyser(){[nativecode]}",
                "5,5",
                "-",
                "-",
                "-",
                "638_50_266_0",
                urlEscape(endpointNoQuery), # Example: "%2Fus%2Fuser%2Flogin"
                ip + "|",
                to_base32(customTime - 98)
            ],
            "c": [
                "-",
                "-",
                "570580",
                "-",
                1032,
                hardwareConcurrency,
                timestampString,
                screenWidth,
                "true_0_1_Infinity",
                "0",
                "Webkit-Chrome",
                "functiongetParameter(){[nativecode]}",
                chromeFullVersion,
                "208",
                "-",
                MurmurHash(generate_random_mime_pdf_types()), # 1f2d82cb67327772481ce484582d66e4=O0Q0o["hash128"](oOoQo) '2,application/pdfpdfPortableDocumentFormat,text/pdfpdfPortableDocumentFormat'
                "-",
                "0|2||1||33d033e74496731ca605",
                to_base32(customTime - 98)
            ],
            "d": [
                "Win32",
                shortLang,
                "-",
                screenWidth,
                "0",
                MurmurHash(generate_fake_fonts()) + "|01100100011111111011111011011111011111011011110001111111111011111", # 63e9e04dc73e254e8ec26ccfae604c64=O0Q0o["hash128"](Q0oQQ) Q0oQQ='[Arial, Arial Black, Arial Narrow, Book Antiqua, Bookman Old Style, Calibri, Cambria, Cambria Math, Century, Century Gothic, Century Schoolbook, Comic Sans MS, Consolas, Courier, Courier New, Garamond, Georgia, Helvetica, Impact, Lucida Bright, Lucida Calligraphy, Lucida Console, Lucida Fax, Lucida Handwriting, Lucida Sans, Lucida Sans Typewriter, Lucida Sans Unicode, Microsoft Sans Serif, Monotype Corsiva, MS Gothic, MS PGothic, MS Reference Sans Serif, MS Sans Serif, MS Serif, Palatino Linotype, Segoe Print, Segoe Script, Segoe UI, Segoe UI Light, Segoe UI Semibold, Segoe UI Symbol, Tahoma, Times, Times New Roman, Trebuchet MS, Verdana, Wingdings, Wingdings 2, Wingdings 3]'
                "Netscape",
                "-",
                3,
                timeZoneOffeset,
                urlEscape(endpoint),
                ua,
                "1",
                "-",
                "Mozilla",
                "-",
                "2032066493__",
                chromeFullVersion,
                "-",
                "19.0.0",
                "-",
                to_base32(customTime - 98)
            ],
            "g": [
                33,
                "functiontoString(){[nativecode]}",
                deviceMemory,
                "functionenumerateDevices(){[nativecode]}",
                "1",
                hardwareConcurrency,
                "[objectPluginArray]",
                "", # ClientIDKey set in JS
                "-",
                deviceMemory,
                "functiontoDataURL(){[nativecode]}",
                hardwareConcurrency,
                "functionRTCPeerConnection(){[nativecode]}",
                "1",
                "-",
                "-",
                "1696.5823364257812",
                "Google Chrome",
                "-",
                12437,
                "-",
                to_base32(customTime - 98)
            ],
            "f": "1^^0^^1^^0^^0^^0",
            "e": ""
        },
        "wb": ""
    }

    return fingerprint

def fingerprint_US_406(appKey, endpoint, ua, acceptLang, chromeFullVersion, timezone, webGl, ip, endpointNoQuery):
    timestamp = int(time.time() * 1000)
    timestampString = str(timestamp)

    timeZoneOffeset = -tzOffset(timezone)

    multiples_of_10 = list(range(1300, 1551, 10))
    screenWidth = random.choice(multiples_of_10)

    innerHeight = random_int(850, 950)
    innerWidth = random_int(1850, 1950)

    deviceMemory = random.choice([2, 4, 8, 16])
    hardwareConcurrency = random.choice([16, 24, 28, 32])

    shortChromeVersion = chromeVersion(chromeFullVersion)
    shortLang = lang(acceptLang)
    
    ua_cleaned = ua.replace("Mozilla/", "")
    userAgentHash = MurmurHash(ua_cleaned)

    fonts = detect_fonts()
    plugs = MurmurHash(generate_random_pdf_viewers())
    pdf = MurmurHash(generate_random_mime_pdf_types())
    canvas1 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAACACAYAAADktbcKAAAAAXNSR0IArs4c6QAACidJREFUeF7tnU1oXUUUx2cSgiiIiAgWv8AiXVSoCEXEhS+IiCgoiIgoKAi6qKAgKOKit4IuCioIuiioIOiioIKgi4LmIeiigaQ0tS1pTWpaa6nSSlvbWkueuUlf+/L63su9d2bunJn5dePCe+fj/z/nlzln3ku04h8KoECyCuhkd87GUQAFFAAgCFAgYQUAQMLms3UUAADEAAokrAAASNh8to4CAIAYQIGEFQAACZvP1lEAABADKJCwAgAgYfPZOgoAAGIABRJWAAAkbD5bRwEAQAygQMIKAICEzWfrKAAAiAEUSFgBAJCw+WwdBQAAMYACCSsAABI2P996q6U2aq02JS5DstsHAMlav5j8DaXUmFJqVGvVTFiKZLcOAJK1Xqn5lhrTahECTa" + get_random_string(20) + "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")
    canvas2 = MurmurHash("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAAAAXNSR0IArs4c6QAAEwBJREFUeF7tm3tYVWW+x39rc9kKbEBFDc0biijuJxUQuQR5w+voKJahp5kK5WI92mM1OZOZx7HGZ5ysxprDzfDYlJcYrSGVAa+ZpiJqgkoHC0FEDARFlNve7HXOu/Ze+2w2mJexGV7fL//oYu+91u/3+fJ+eN93LSRZlmVJkiTCFwiAAAh0cAIQVQcP6OcoT44n+ec4b0c/p5RK+Hnv6CHdoT4EyHmA91M+hHU/1PCZjkAAwuoIKfyLa4Cw/sXAcbkHRgDCemAo+TkRhMVPVqi0NYH/F1ZiUm8yaQ6TJL9MKYnb24Ayv55FGtMCSl6YS/bH90M29iMdObRsIYeWlco5bY9l6VGSpW3KaSV5OaUkvnXXl2DncTTuIqLHiaiUNKZwSl5Yftefv5" + get_random_string(20) + "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")
    current_time_hash = hashlib.md5(str(int(time.time() * 1000)).encode()).hexdigest()

    fingerprint = {
        "bb": "",
        "pageInfo": {},
        "q": {
            "partner": "popmart",
            "appKey": appKey
        },
        "b": {
            "i": [
                "1",
                MurmurHash(fonts[0]) + "|" + fonts[1],
                "Netscape",
                generate_random_audio_context_string(),
                hardwareConcurrency,
                ua,
                screenWidth, # Width
                1032,
                1,
                screenWidth,
                "-",
                1080,
                "true_0_1_Infinity",
                canvas1 + "|" + generate_x_sign(current_time_hash),
                "functioncreateAnalyser(){[nativecode]}",
                chromeFullVersion,
                chromeFullVersion,
                "-",
                pdf,
                12440,
                "-",
                ""
            ],
            "j": [
                "Win32",
                "-",
                "11110",
                "576780",
                "-",
                screenWidth,
                1032,
                urlEscape(endpoint),
                innerHeight, # innerHeight
                "-",
                "Webkit-Chrome",
                "-",
                "-",
                "5,5,5,5,5",
                "-",
                "-",
                "-",
                ""
            ],
            "k": [
                plugs,
                "-",
                0,
                canvas2,
                0,
                innerHeight,
                screenWidth,
                timeZoneOffeset,
                shortLang,
                "0",
                timestampString,
                "-",
                innerWidth,
                fullGl(webGl),
                "functiongetParameter(){[nativecode]}",
                "Google Chrome",
                "2103626074__",
                "UTF-8",
                "-",
                "637_49_784_0",
                ""
            ],
            "l": [
                "-",
                shortLang,
                userAgentHash,
                "Mozilla",
                "-",
                "-",
                "0",
                "functiongetoffsetHeight(){[nativecode]}",
                "-",
                "1381",
                "-",
                "19.0.0",
                "0_Windows_Chromium_" + shortChromeVersion + "_Google Chrome_" + shortChromeVersion + "_Not.A/Brand_99",
                "-",
                shortLang + "|" + timezone,
                ip + "|",
                "0|36||1|4",
                ""
            ],
            "o": [
                "-",
                "functiontoDataURL(){[nativecode]}",
                "1",
                "functionRTCPeerConnection(){[nativecode]}",
                "1",
                "[objectPluginArray]",
                "functionenumerateDevices(){[nativecode]}",
                33,
                "functiontoString(){[nativecode]}",
                deviceMemory,
                hardwareConcurrency,
                deviceMemory,
                hardwareConcurrency,
                "clientIdKey", # Set in JS
                "-",
                "[object Window]",
                "-",
                "1696.5823364257812",
                "-",
                "-",
                "-",
                "-",
                ""
            ],
            "f": "1^^0^^0^^0^^0^^0",
            "e": ""
        },
        "wb": ""
    }

    return fingerprint

# Helpers

def jsFileForRegion(region) -> str:

    if VERSION_USE == "4.1.3":
        return "./vm413.js"

    if VERSION_USE == "4.1.1":
        return "./vm411.js"
    
    if VERSION_USE == "4.0.7":
        return "./vm407.js"
    
    if VERSION_USE == "4.0.6":
        return "./vm406.js"
    
    return "./vm411.js"

def generate_x_sign(t):
    n = int(str(int(time.time() * 1000))[:10])
    o = f"{n},{t}"
    md5_hash = hashlib.md5(o.encode()).hexdigest()
    return f"{md5_hash},{n}"

def random_ip():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def detect_fonts():
    font_list = [
        "Andale Mono",
        "Arial",
        "Arial Black",
        "Arial Hebrew",
        "Arial MT",
        "Arial Narrow",
        "Arial Rounded MT Bold",
        "Arial Unicode MS",
        "Bitstream Vera Sans Mono",
        "Book Antiqua",
        "Bookman Old Style",
        "Calibri",
        "Cambria",
        "Cambria Math",
        "Century",
        "Century Gothic",
        "Century Schoolbook",
        "Comic Sans",
        "Comic Sans MS",
        "Consolas",
        "Courier",
        "Courier New",
        "Garamond",
        "Geneva",
        "Georgia",
        "Helvetica",
        "Helvetica Neue",
        "Impact",
        "Lucida Bright",
        "Lucida Calligraphy",
        "Lucida Console",
        "Lucida Fax",
        "LUCIDA GRANDE",
        "Lucida Handwriting",
        "Lucida Sans",
        "Lucida Sans Typewriter",
        "Lucida Sans Unicode",
        "Microsoft Sans Serif",
        "Monaco",
        "Monotype Corsiva",
        "MS Gothic",
        "MS Outlook",
        "MS PGothic",
        "MS Reference Sans Serif",
        "MS Sans Serif",
        "MS Serif",
        "MYRIAD",
        "MYRIAD PRO",
        "Palatino",
        "Palatino Linotype",
        "Segoe Print",
        "Segoe Script",
        "Segoe UI",
        "Segoe UI Light",
        "Segoe UI Semibold",
        "Segoe UI Symbol",
        "Tahoma",
        "Times",
        "Times New Roman",
        "Times New Roman PS",
        "Trebuchet MS",
        "Verdana",
        "Wingdings",
        "Wingdings 2",
        "Wingdings 3"
    ]
    
    QoQoQ_fonts = []
    OQOO0_bloean = []

    for font in font_list:
        if random.random() > 0.5:
            QoQoQ_fonts.append(font)
            OQOO0_bloean.append(1)
        else:
            OQOO0_bloean.append(0)

    QoQoQ_fonts_str = "[" + ", ".join(QoQoQ_fonts) + "]"

    return [QoQoQ_fonts_str, "".join(map(str, OQOO0_bloean))]

def tzOffset(tz):
    if tz == "America/New_York":
        return 300  # UTC -5 hours (Eastern Standard Time)
    elif tz == "America/Chicago":
        return 360  # UTC -6 hours (Central Standard Time)
    elif tz == "America/Denver":
        return 420  # UTC -7 hours (Mountain Standard Time)
    elif tz == "America/Los_Angeles":
        return 480  # UTC -8 hours (Pacific Standard Time)
    elif tz == "Europe/London":
        return 0    # UTC (Greenwich Mean Time)
    elif tz == "Europe/Paris":
        return -60   # UTC +1 hour (Central European Time)
    elif tz == "Asia/Tokyo":
        return -540  # UTC +9 hours (Japan Standard Time)
    elif tz == "Asia/Shanghai":
        return -480  # UTC +8 hours (China Standard Time)
    elif tz == "Australia/Sydney":
        return -600  # UTC +10 hours (Australian Eastern Standard Time)

    return 300

def makeBody(userAgent, fullPath, webGl) -> str:

    body = [userAgent, fullPath, webGlType(webGl) + '-&-' + webGl, '', '', '0']

    return "|".join(body)

def fullGl(webGl) -> str:
    return f"{webGlType(webGl)}-&-{webGl}"

def webGlType(webGl):
    if "NVIDIA" in webGl:
        return 'Google Inc. (NVIDIA)'
    elif "Intel" in webGl:
        return 'Google Inc. (Intel)'
    else:
        return 'Google Inc. (AMD)'

def chromeVersion(version):
    return version[:3]

def lang(acceptLang):
    return acceptLang[:5]

def parse_proxy(proxy_string):
    try:
        host, port, username, password = proxy_string.split(':')
        return host, port, username, password
    except:
        return "", "", "", ""

def urlEscape(url):
    return urllib.parse.quote(url, safe='')

def random_int(min_val, max_val):
    min_val = math.ceil(min_val)
    max_val = math.floor(max_val)
    return math.floor(random.random() * (max_val - min_val + 1)) + min_val

def generate_random_audio_context_string():
    sample_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 192000]
    channels = [1, 2, 4, 5, 6, 8]
    states = [0, 1, 2]
    modes = ["implicit", "explicit"]
    types = ["speakers", "headphones", "balanced", "earpiece", "line_out", "hdmi"]
    
    rate = random.choice(sample_rates)
    front = random.choice(channels)
    center = random.choice(states)
    lfe = random.choice(states)
    surround = random.choice(states)
    mode = random.choice(modes)
    type_ = random.choice(types)
    
    return f"{rate}_{front}_{center}_{lfe}_{surround}_{mode}_{type_}"

def to_base32(num):
    digits = "0123456789abcdefghijklmnopqrstuv"  # Base 32 digits
    if num == 0:
        return "0"
    
    result = ""
    is_negative = num < 0
    if is_negative:
        num = -num
    
    while num > 0:
        result = digits[num % 32] + result
        num //= 32
    
    if is_negative:
        result = "-" + result
    
    return result

def MurmurHash(input_string):
    t = mmh3.hash64(input_string, seed=0, x64arch=True, signed=False)
    hash1 = f"{hex(t[0])}"
    hash2 = f"{hex(t[1])}"

    hash1 = hash1[2:]
    hash2 = hash2[2:]

    final = hash1 + hash2

    return final

def get_random_string(A):
    chars = "abacdefghjklmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(A))

def generate_random_pdf_viewers():
    A = random.randint(1, 5)
    o = ["ChromePDFViewer", "ChromiumPDFViewer", "MicrosoftEdgePDFViewer", "PDFViewer", "WebKitbuilt-inPDF"]
    viewers = [o[i % len(o)] + "PortableDocumentFormatinternal-pdf-viewer2" for i in range(A)]
    return f"{A}," + ",".join(viewers)

def generate_random_mime_pdf_types():
    A = random.randint(1, 5)
    Q = ["application/pdf", "text/pdf", "application/x-pdf", "application/acrobat", "applications/vnd.pdf"]
    mimes = [random.choice(Q) + "pdfPortableDocumentFormat" for _ in range(A)]
    return f"{A}," + ",".join(mimes)

def generate_fake_fonts(A=51):
    Q = ["Neo", "Ultra", "Meta", "Mono", "Hyper", "Quantum", "Giga", "Lucida", "Seri", "Sans",
         "Nova", "Omega", "Digital", "Classic", "Modern", "Cyber", "Pixel", "Proto", "Fusion", "Orbit"]
    o = ["Sans", "Serif", "Gothic", "Script", "Display", "Grotesk", "Slab", "Mono", "Print", "Handwriting",
         "Brush", "Black", "Bold", "Italic", "Light", "Regular", "UI", "Math", "Text", "Code"]
    I = ["", " Pro", " Std", " Light", " Medium", " Semibold", " Condensed", " Extended", " Alt", " Italic"]
    g = set()

    while len(g) < A:
        e = (random.choice(Q) + " " + random.choice(o) + random.choice(I)).strip()
        g.add(e)
    
    return ",".join(g)

def get_popmart_country_data(site):
    result = {}
    
    # Default values (same as US)
    result["namespace"] = "america"
    result["clientKey"] = "nw3b089qrgw9m7b7i"
    result["country"] = "US"
    result["projectId"] = "naus"
    result["lang"] = "en"
    
    result["timezone"] = "America/New_York"
    result["acceptLang"] = "en-US,en;q=0.9"
    
    if "US" in site:  # United States
        result["namespace"] = "america"
        result["clientKey"] = "nw3b089qrgw9m7b7i"
        result["country"] = "US"
        result["projectId"] = "naus"
        result["lang"] = "en"

        result["fpRegion"] = "us"
        result["appkey"] = "e8e328d27d9866dcf49ed2e0bb7411c4"

    elif "CA" in site:  # Canada
        result["namespace"] = "america"
        result["clientKey"] = "nw3b089qrgw9m7b7i"
        result["country"] = "CA"
        result["projectId"] = "naus"
        result["lang"] = "en"

        result["fpRegion"] = "us"
        result["appkey"] = "e8e328d27d9866dcf49ed2e0bb7411c4"

    elif "BR" in site:  # Brazil
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "BR"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "AU" in site:  # Australia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "AU"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "NZ" in site:  # New Zealand
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "NZ"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "AT" in site:  # Austria
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "AT"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "BE" in site:  # Belgium
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "BE"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "HR" in site:  # Croatia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "HR"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "CZ" in site:  # Czech Republic
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "CZ"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "DK" in site:  # Denmark
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "DK"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "EE" in site:  # Estonia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "EE"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "FI" in site:  # Finland
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "FI"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "FR" in site:  # France
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "FR"
        result["projectId"] = "eude"
        result["lang"] = "fr"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "DE" in site:  # Germany
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "DE"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "GR" in site:  # Greece
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "GR"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "HU" in site:  # Hungary
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "HU"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "IE" in site:  # Ireland
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "IE"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "IT" in site:  # Italy
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "IT"
        result["projectId"] = "eude"
        result["lang"] = "en"
        
        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "LV" in site:  # Latvia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "LV"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "LT" in site:  # Lithuania
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "LT"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "LU" in site:  # Luxembourg
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "LU"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "NL" in site:  # Netherlands
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "NL"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "PL" in site:  # Poland
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "PL"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "PT" in site:  # Portugal
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "PT"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "SK" in site:  # Slovakia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "SK"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "SI" in site:  # Slovenia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "SI"
        result["projectId"] = "eude"
        result["lang"] = "en"
        
        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "ES" in site:  # Spain
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "ES"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "SE" in site:  # Sweden
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "SE"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "CH" in site:  # Switzerland
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "CH"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "GB" in site:  # United Kingdom
        result["namespace"] = "eurasianuk"
        result["clientKey"] = "xzriem686i2i2dkwo"
        result["country"] = "GB"
        result["projectId"] = "uk"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "HK" in site:  # Hong Kong
        result["namespace"] = "hk"
        result["clientKey"] = "xzriem686i2i2dkwo"
        result["country"] = "HK"
        result["projectId"] = "hk"
        result["lang"] = "zh-hant"
        
        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"
        
    elif "ID" in site:  # Indonesia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "ID"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "JP" in site:  # Japan
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "JP"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "MO" in site:  # Macao
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "MO"
        result["projectId"] = "eude"
        result["lang"] = "zh-hant"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "MY" in site:  # Malaysia
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "MY"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "PH" in site:  # Philippines
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "PH"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "SG" in site:  # Singapore
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "SG"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "KR" in site:  # South Korea
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "KR"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "TW" in site:  # Taiwan
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "TW"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "TH" in site:  # Thailand
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "TH"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"

    elif "VN" in site:  # Vietnam
        result["namespace"] = "eurasian"
        result["clientKey"] = "rmdxjisjk7gwykcix"
        result["country"] = "VN"
        result["projectId"] = "eude"
        result["lang"] = "en"

        result["fpRegion"] = "de"
        result["appkey"] = "e6058883d38c943d575ef00c0bc08768"
        
    return result

webgls = [
    'ANGLE (NVIDIA, NVIDIA GeForce GT 330M (0x00000A2B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 320M (0x00000A2C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 505 (0x00000A30) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 415 (0x00000A32) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 320M (0x000008A5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 220 (0x00000A20) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 330M (0x00000A21) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 315 (0x00000A22) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 210 (0x00000A23) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 405 (0x00000A26) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 405 (0x00000A27) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 405 (0x00000A24) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400 (0x0000087A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 320M (0x0000087D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 320M (0x000008A2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 320M (0x000008A3) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 320M (0x000008A4) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9100M G (0x0000086E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8200M G (0x0000086F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400M (0x00000870) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9200 (0x00000871) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce G102M (0x00000872) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce G102M (0x00000873) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400M / ION (0x00000874) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400M G (0x00000866) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400 (0x00000867) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400 (0x00000868) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400 (0x0000086A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9300 / nForce 730i (0x0000086C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9200 (0x0000086D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8100 / nForce 720a (0x0000084D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9300 (0x00000860) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400 (0x00000861) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400M G (0x00000862) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9400M (0x00000863) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9300 (0x00000864) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9300 / ION (0x00000865) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8200M G (0x00000845) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9200 (0x00000846) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9100 (0x00000847) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8300 (0x00000848) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8200 (0x00000849) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8200 (0x0000084A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 7100 / nForce 620i (0x0000084C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 8200M (0x000007F0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 9100M G (0x00000844) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 7150 / nForce 630i (0x000007DC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 7100 / nForce 630i (0x000007E1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 7050 / nForce 630i (0x000007E2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce 7050 / nForce 610i (0x000007E3) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x00002484) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001636) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A49) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E92) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002504) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 960 (0x00001401) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Ti Laptop GPU (0x000025A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 (0x00002582) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Laptop GPU (0x000028A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A78B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A720) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002487) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009B41) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Ti (0x00001E04) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001F82) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti (0x00002482) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Arc(TM) Graphics (0x00007D55) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 620 (0x00005916) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Arc(TM) A770 Graphics (0x000056A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6600 (0x000073FF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 5500 XT (0x00007340) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 5700 XT (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 770 (0x00004680) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER (0x000021C4) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 750 Ti (0x00001380) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00009BC8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon 780M Graphics (0x00001900) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F03) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P620 (0x00001CB6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 970 (0x000013C2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 (0x00002684) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 630 (0x0000591B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002882) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 740M (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3090 (0x00002204) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 SUPER (0x00002702) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) Graphics (0x000015E7) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x000046A3) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A7A8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti (0x00001C82) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 650M (0x00000FD5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x00002488) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Pro WX 2100 (0x00006995) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 3GB (0x00001C02) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 (0x00001F02) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009A78) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti (0x000024C9) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti (0x00002414) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 (0x00002704) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon TM Graphics (0x00001900) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 (0x00001BE1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 620 (0x00005917) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB (0x00001C03) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7700 XT (0x0000747E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00002188) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E9B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro RTX 5000 (0x00001EB0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 Laptop GPU (0x000027E0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x0000164C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009A60) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002216) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001638) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F08) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 (0x00001B81) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001681) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 SUPER (0x00001E84) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti (0x00002486) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00008A56) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 960M (0x0000139B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 530 (0x00001912) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 5600 XT (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Laptop GPU (0x000024DC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Laptop GPU (0x000025A2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 580 Series (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009BC4) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 (0x00002507) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti with Max-Q Design (0x00002191) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004628) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3090 Ti (0x00002203) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Ti (0x00002805) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x0000A7A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 4600 (0x00000416) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti (0x00002191) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009BCA) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 570 Series (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Vega 8 Graphics (0x000015D8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x0000A7A1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Graphics (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 Ti (0x00001B82) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Ti (0x00002803) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 5500 XT (0x00007340) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU (0x00002860) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Ti (0x00001B06) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Laptop GPU (0x000028E0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon 780M Graphics (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7800 XT (0x0000747E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 SUPER (0x00002783) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P2000 (0x00001C30) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7900 XT (0x0000744C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001E89) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 SUPER (0x00001F06) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics P630 (0x00009BE6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Ti (0x00001E07) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6900 XT (0x000073BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti (0x00002489) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6400 (0x0000743F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU (0x00002820) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x000024C7) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A68) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x000046D1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Ti (0x00002208) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 520 (0x00001916) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti Laptop GPU (0x000024A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 780 (0x00001004) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Arc(TM) 140V GPU (8GB) (0x000064A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 OEM (0x00002508) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A788) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti Laptop GPU (0x000024E0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 (0x00002184) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) RX Vega 10 Graphics (0x000015D8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro K2000D (0x00000FF9) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A721) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 750 (0x00004C8A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7600 (0x00007480) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Ti (0x00001F95) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 770 (0x0000A780) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7900 XTX (0x0000744C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 710 (0x0000128B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009A68) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 SUPER (0x00002187) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 730 (0x00004692) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti SUPER (0x00002705) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 620 (0x00003EA0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004688) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Laptop GPU (0x0000249D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6750 XT (0x000073DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6650 XT (0x000073EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti (0x00002182) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Laptop GPU (0x00002520) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Laptop GPU (0x000024DD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti (0x00002782) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002206) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 (0x00001E82) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 980M (0x000013D7) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Laptop GPU (0x00002560) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001F99) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX550/550 Series (0x0000699F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001F91) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics Family (0x00000A16) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon Pro 575 (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002503) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R7 200 Series (0x00006613) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x0000164E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6650M (0x000073EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Ti (0x00002788) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Laptop GPU (0x00002757) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A7A9) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6700 XT (0x000073DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4050 Laptop GPU (0x000028E1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics (0x00008A52) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001FDD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 (0x00001E87) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Graphics (0x00007DD5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R7 200 Series (0x00006611) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6600 XT (0x000073FF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 6GB Laptop GPU (0x000025AC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 980 (0x000013C0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics (0x00008A5A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6700 (0x000073DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Graphics (0x00007D45) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x0000220A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F15) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 (0x00001C81) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E91) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F51) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics 640 (0x00005926) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001900) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA T1000 8GB (0x00001FF0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce MX550 (0x00001F9F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Laptop GPU (0x0000249C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046AA) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 770 (0x00004690) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 (0x00001B80) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA RTX A4500 (0x00002232) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 SUPER (0x00001E81) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001506) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Vega 3 Graphics (0x000015D8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x000046B3) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 760M (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6800 (0x000073BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA RTX A4000 (0x000024B0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6800 XT (0x000073BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD RadeonT 780M (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD RadeonT 660M (0x00001681) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 780M (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7600 XT (0x00007480) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 590 Series (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA T1000 (0x00001FB0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002709) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro K2000 (0x00000FFE) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 760 (0x00001187) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 (0x00002584) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 610M (0x0000164E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001F0A) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009A70) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 660 (0x000011C0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) R7 Graphics (0x0000130F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics (0x00008A53) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics P630 (0x00009BF6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 950 (0x00001402) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 1030 (0x00001D01) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 515 (0x0000191E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A40) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 4400 (0x0000041E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6600M (0x000073FF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 580 2048SP (0x00006FDF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro K2200 (0x000013BA) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX Vega (0x0000687F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 750 Ti (0x0000139B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Ti Laptop GPU (0x000025E0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Graphics (0x0000A7AC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 5600 (0x00001612) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 630 (0x00005912) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) R9 390 Series (0x000067B0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 745 (0x00001382) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 560 Series (0x000067EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00009BC5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00009BCC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 4600 (0x00000412) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6950 XT (0x000073A5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics (0x00008A51) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics 655 (0x00003EA5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F11) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7900 GRE (0x0000744C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Pro 5700 XT (0x00007319) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 (0x00001F07) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti (0x00002207) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 650 (0x00000FC6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 5700 (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD  Radeon RX 7800 XT (0x0000747E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Pro 450 (0x000067EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004C8B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Ti Laptop GPU (0x00002420) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 730 (0x00004682) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6900 XT (0x000073AF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 890M Graphics (0x0000150E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 770 (0x00001184) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) RX Vega 11 Graphics (0x000015DD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon HD 7800 Series (0x00006818) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R7 200 Series (0x0000683D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6500 XT (0x0000743F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro M2000 (0x00001430) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX Vega M GH Graphics (0x0000694C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 with Max-Q Design (0x00001ED0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 730 (0x00001287) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 750 (0x00001381) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 with Max-Q Design (0x00001BE0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 (0x00001C60) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 780M (0x00001900) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004626) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 with Max-Q Design (0x00001F14) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 (0x00001ED0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 Laptop GPU (0x000027A0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 730 (0x00004C8B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon (TM) RX 470 Graphics (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX TITAN X (0x000017C2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P2000 (0x00001CBA) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX5600 (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 530 (0x0000191B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Super with Max-Q Design (0x00001ED1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics 645 (0x00003EA6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 6GB Laptop GPU (0x000025EC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Super (0x00001ED1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(TM) Pro Graphics 5200 (0x00000D26) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) RX Vega 11 Graphics (0x000015D8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB (0x00001B83) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 980 Ti (0x000017C8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 600 (0x00003185) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 630 (0x00000FC2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, ASUS Radeon RX 580 Series (0x000067DF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon HD 8570 (0x00006611) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7600S (0x00007480) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R9 200 Series (0x000067B0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Pro Graphics 580 (0x0000193B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics P630 (0x00003E94) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 (0x00001F10) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) Graphics (0x00001681) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Graphics (0x0000A7AD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Vega 3 Graphics (0x000015DD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000468B) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 6700S (0x000073EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti (0x00001C8C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti SUPER (0x00002689) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA RTX A3000 Laptop GPU (0x000024B8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P4200 with Max-Q Design (0x00001BB9) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA TITAN X (Pascal) (0x00001B00) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002808) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon RX 5500M (0x00007340) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 (0x00001C8D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro RTX 4000 (0x00001EB1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Laptop GPU (0x00002717) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P2000 with Max-Q Design (0x00001CBA) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA T600 (0x00001FB1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 (0x00001F55) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Graphics (0x00007D67) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 (0x00001F14) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) 880M Graphics (0x0000150E) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon 760M Graphics (0x00001900) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R9 200 / HD 7900 Series (0x00006798) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) Graphics (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004E61) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) R9 380 Series (0x00006939) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon TM Graphics (0x00001901) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E98) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 (0x00001F9D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 with Max-Q Design (0x00001BE1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 4600 Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 (0x00001C20) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Super (0x00001E91) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 615 (0x0000591C) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 with Max-Q Design (0x00001BA1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 760 Ti OEM (0x00001189) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 640 (0x00000FC1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce MX450 (0x00001F98) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x000046D0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, ASUS Radeon RX Vega (0x0000687F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 610 (0x00003E90) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro RTX 4000 (0x00001EB6) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 (0x00001C91) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon R9 200 Series (0x00006798) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce MX150 (0x00001C90) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Pro VII (0x000066A1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) R9 380 Series (0x00006938) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 with Max-Q Design (0x00001F12) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Pro Graphics (0x00001638) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics 605 (0x00003184) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x000046D2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A60) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro RTX 3000 (0x00001F36) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P600 (0x00001CBC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Graphics 540 (0x00001926) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P2200 (0x00001C31) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002544) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 with Max-Q Design (0x00001F10) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P600 (0x00001CB2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro K420 (0x00000FF3) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 with Max-Q Design (0x00001F9D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) R7 Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 660M (0x00000FE0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) R7 Graphics (0x00001313) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P5000 (0x00001BB0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro RTX 5000 (0x00001EB5) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P1000 (0x00001CB1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro T2000 with Max-Q Design (0x00001FB8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004E71) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Custom GPU 0932 (0x00001435) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 SUPER (0x00001EC7) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 740 (0x00000FC8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (0x00001AB8, Parallels Display Adapter (WDDM) (0x00004005) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA T1200 Laptop GPU (0x00001FBC) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA RTX 2000 Ada Generation (0x000028B0) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Super with Max-Q Design Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Laptop GPU (0x000025E2) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) Iris(R) Plus Graphics 650 (0x00005927) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 5GB (0x00001C04) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics P630 (0x0000591D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4050 Laptop GPU (0x000028A1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics (0x00000402) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x00004E55) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Vega 8 Graphics (0x000015DD) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Ti Laptop GPU (0x00002460) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon HD 7700M Series (0x0000682D) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GT 750M (0x00000FE4) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro P1000 (0x00001CBB) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, ASUS Radeon RX 5700 XT (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7700S (0x00007480) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics (0x000015D8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon (TM) 780M Graphics (0x000015BF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon Graphics (0x000015C8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Super (0x00001E93) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) UHD Graphics (0x0000A780) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 (0x00001BA1) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7600M XT (0x00007480) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 510 (0x00001902) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA Quadro T2000 (0x00001FB8) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, Radeon(TM) RX 460 Graphics (0x000067EF) Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (Intel, Intel(R) HD Graphics 5300 (0x0000161E) Direct3D11 vs_5_0 ps_5_0, D3D11)'
]

longImage = "data:image/png;base64,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"

longImage2 = "data:image/png;base64,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"

# Test

def test():
    print("\n\n\n\n\n\n")
    print(Solver(
        "resi.wealthproxies.com:8000:akzaidan:8z7tgsn1-country-US-session-yk8b8ux0-duration-60", 
        "/customer/v1/verification/send",
        "https://www.popmart.com/us/user/register",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "138.0.7204.97",
        "US",
        "50.54.149.212",
        "/us/user/login"
    ).makeSession(False))
    print("\n\n\n\n\n\n")
