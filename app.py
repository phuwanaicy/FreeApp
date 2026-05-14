import re
import json
import subprocess
from flask import Flask, jsonify, request
from urllib.parse import quote

app = Flask(__name__)

class PremiumPortalBot:
    def __init__(self, cf_clearance):
        self.cf_clearance = cf_clearance
        self.access_token = None
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'

    def _parse_nextjs_payload(self, text):
 
        lines = text.strip().split('\n')
        for line in lines:

            match = re.search(r'^[0-9]+:(\{.*\})$', line)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if 'success' in data or 'data' in data:
                        return data
                except: continue
        try: return json.loads(text)
        except: return {"raw_response": text}

    def _request(self, url, method='GET', payload=None, custom_headers=None):

        headers = {
            'accept': 'application/json, text/plain, */*' if 'consumer-api' in url else 'text/x-component',
            'accept-language': 'th,pt;q=0.9,id;q=0.8',
            'user-agent': self.user_agent,
            'origin': 'https://premiumportal.id'
        }

        cookies = f"cf_clearance={self.cf_clearance}"
        if self.access_token:
            headers['authorization'] = f'Bearer {self.access_token}'
            cookies += f"; accessToken={self.access_token}"
        if custom_headers: headers.update(custom_headers)

        cmd = f"curl -s -k -L -X {method} '{url}'"
        for k, v in headers.items(): cmd += f" -H '{k}: {v}'"
        cmd += f" -b '{cookies}'"

        if method == 'POST' and payload is not None:
            if not isinstance(payload, str): payload = json.dumps(payload)
            cmd += f" -H 'content-type: text/plain;charset=UTF-8' --data-raw '{payload}'"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return json.dumps({"error": "cURL engine failed", "details": str(e)})

    def login(self, email, password, next_hash):
        url = 'https://premiumportal.id/auth/login'
        payload = f'[{{"email":"{email}","password":"{password}"}}]'
        res = self._request(url, 'POST', payload, {'next-action': next_hash})
        data = self._parse_nextjs_payload(res)
        try:
            d = data.get('data', {})
            self.access_token = d.get('data', {}).get('accessToken') or d.get('accessToken')
            return True if self.access_token else False
        except: return False

    def get_downloader(self, slug, next_hash):
        safe_slug = quote(slug)
        url = f'https://premiumportal.id/downloader/{safe_slug}'

        payload = f'["{slug}",1,10]'
        custom_headers = {
            'next-action': next_hash,
            'referer': url
        }
        return self._parse_nextjs_payload(self._request(url, 'POST', payload, custom_headers))

    def get_list_account(self, slug, next_hash):
        safe_slug = quote(slug)
        url = f'https://premiumportal.id/list-account/{safe_slug}'
        payload = f'[{{"type":"{slug}"}}]'
        router_state = f'%5B%22%22%2C%7B%22children%22%3A%5B%22list-account%22%2C%7B%22children%22%3A%5B%5B%22name%22%2C%22{safe_slug}%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D'
        custom_headers = {'next-action': next_hash, 'next-router-state-tree': router_state, 'referer': url}
        return self._parse_nextjs_payload(self._request(url, 'POST', payload, custom_headers))

    def get_categories(self):
        return json.loads(self._request('https://consumer-api.premiumportal.id/types/active/category'))

    def get_items(self, cat_id):
        return json.loads(self._request(f'https://consumer-api.premiumportal.id/extensions/get-items/{cat_id}'))

    def get_cookies(self, item_id):
        return json.loads(self._request(f'https://consumer-api.premiumportal.id/extensions/get-cookies/{item_id}'))

CF_CLEARANCE = "k3ISyFz9Ei.YKsmnOElygwkXOWKQ5yq.M8hSIUdj5kk-1778698130-1.2.1.1-7L14nJ9Bhdg21yfTEALdlV40YJLkE1jIGH3KFx_5F8l_OGHfTxh7NrtShb145xegtfIkpN9oHdPHLL0ZMSnfJGWtKSHvb_x1Jesces9jfAcVVadB1pTPTDF84CGt6rQHPKUDYyUCv_9tCF_at6H03r_BvfUIq0_ZbKwwSFoaFMUMcMMu5MHj7LlPO5JvyLYwSWZlCzgDhdKTNVeSy3BKlVU7AMypQzhb7ifsVUTwParmwpuoWE02_RUnEI9vXxqLPg1dlviweDTZakglYtXXC49DTsZNI4qLOBBzJx.RHG3brnw7Xze6_OIuR0lpcLUDz2QzK25gi9BNO.ANwZsmeZZMeAc2MVlXbBuix4fPlf9Ozp7NjIzFeOVHhGn1dD3NznWnDuRGcXa6Kj__wv51eI68nacttXppQxDJRZlLHro"
EMAIL = "bizdevsg2024@gmail.com"
PASSWORD = "Garlicbo1#"

LOGIN_H = "7fe69c1a910dd07bf185b9c0d37ced45a48951185f"
LIST_H = "40d135b94e00735b0aedce889674a599ffd38c2f79"
DOWNLOADER_H = "7f4639d6f71dc2a58eff43baab9ecbdba5206e07de"
bot = PremiumPortalBot(CF_CLEARANCE)

@app.before_request
def auto_login():
    if request.path != '/' and not bot.access_token:
        bot.login(EMAIL, PASSWORD, LOGIN_H)

@app.route('/')
def home(): return jsonify({"status": "Online", "endpoints": ["/api/category", "/api/list-account/<slug>", "/api/downloader/<slug>", "/api/get-items/<id>", "/api/get-cookies/<id>"]})

@app.route('/api/category')
def category(): return jsonify(bot.get_categories())

@app.route('/api/get-items/<cat_id>')
def items(cat_id): return jsonify(bot.get_items(cat_id))

@app.route('/api/get-cookies/<item_id>')
def cookies(item_id): return jsonify(bot.get_cookies(item_id))

@app.route('/api/list-account/<slug>')
def list_acc(slug): return jsonify(bot.get_list_account(slug, LIST_H))

@app.route('/api/downloader/<slug>')
def dl(slug): return jsonify(bot.get_downloader(slug, DOWNLOADER_HASH if 'DOWNLOADER_HASH' in locals() else DOWNLOADER_H))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
