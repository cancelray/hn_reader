from __future__ import annotations

import json
import random
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = '127.0.0.1'
PORT = 8000
SEED = 2026

rng = random.Random(SEED)
now = int(time.time())

TITLES = [
    'Show HN: A tiny tool that makes local development less painful',
    'Ask HN: What are you building this weekend?',
    'SQLite is not just for prototypes',
    'A practical guide to debugging distributed systems',
    'The unreasonable effectiveness of plain text',
    'How we reduced our build times by 40%',
    'A new approach to browser automation',
    'Why I still enjoy writing small programs',
    'Open-source project: terminal-first notes',
    'Lessons learned from migrating a large codebase',
    'The hidden costs of abstractions',
    'A visual explanation of DNS',
    'Rust for the tools I use every day',
    'Making a fast search engine on a laptop',
    'The state of self-hosted software in 2026',
    'An experiment in offline-first web applications',
    'Designing APIs that are pleasant to use',
    'What happens when you remove your dependencies?',
]

DOMAINS = [
    'example.com',
    'blog.example.org',
    'dev.example.net',
    'engineering.example.com',
    'news.example.org',
]

TEXT = [
    'Spent the last few evenings experimenting with a tiny script that organizes files by date.\nIt started as a quick fix and somehow became the tool I use every morning.\nFunny how the smallest projects tend to stick around.',
    'I found an old laptop in a drawer and decided to install Linux on it.\nThe machine is slower than anything I normally use, but it feels surprisingly refreshing.\nThere is something nice about making old hardware useful again.',
    'Yesterday I rewrote a small part of my application without adding a single dependency.\nThe result is not particularly impressive, but the code is easier to read and maintain.\nSometimes doing less is actually the best solution.',
    'Been thinking about how much software we use every day without really noticing it.\nMost of it quietly does its job in the background and never asks for attention.\nMaybe that is what good software should feel like.',
]

COMMENT_TEXTS = [
    'This is a useful perspective. I ran into something similar last year.',
    'The trade-off here is worth calling out; it depends a lot on the workload.',
    'I would love to see a follow-up with more benchmarks.',
    'Thanks for sharing this. The examples made it much easier to understand.',
    'One thing that worked well for us was keeping the first version very small.',
    'Interesting idea. Have you tried this with a larger dataset?',
    'The documentation is surprisingly clear for a project this new.',
    'I think the biggest benefit is how easy it is to maintain over time.',
    'A small correction: the behavior differs on older versions.',
    'This reminds me of a similar discussion from a few years ago.',
    'Good write-up. I bookmarked this for later.',
    'We adopted a similar approach and it made debugging easier.',
]

users = [
    'bytewanderer',
    'mira_dev',
    'plain_text_fan',
    'synthwave42',
    'code_craftsman',
    'greenfield',
    'kernelpanic',
    'littlecompiler',
    'octetcat',
    'curious_builder',
    'shipitdaily',
    'slowisfast',
    'packet_panda',
    'stackwalker',
    'turingcoffee',
    'northernbyte',
]

items: dict[int, dict] = {}
story_ids: list[int] = []
top_ids: list[int] = []
new_ids: list[int] = []
best_ids: list[int] = []


def text_in_story() -> str:
    rand = random.random()
    if rand < 0.3:
        return rng.choice(TEXT)

    return ''


for i, title in enumerate(TITLES):
    story_id = 41000000 + i
    story_ids.append(story_id)
    author = rng.choice(users)
    text = text_in_story()
    score = rng.randint(15, 950)
    story_time = now - rng.randint(300, 60 * 60 * 24 * 14)
    comment_count = rng.randint(3, 7)

    if len(text) > 0:
        story = {
            'id': story_id,
            'by': author,
            'title': title,
            'text': text,
            'score': score,
            'time': story_time,
            'type': 'story',
            'kids': [],
            'descendants': comment_count,
        }
    else:
        story = {
            'id': story_id,
            'by': author,
            'title': title,
            'url': f'https://{rng.choice(DOMAINS)}/articles/{i + 1}',
            'score': score,
            'time': story_time,
            'type': 'story',
            'kids': [],
            'descendants': comment_count,
        }
        
    items[story_id] = story

    comment_ids = [story_id + 1000 + j * 100 for j in range(comment_count)]
    story['kids'] = []

    for j, comment_id in enumerate(comment_ids):
        parent_id = story_id
        if j >= 2 and j % 3 == 2:
            parent_id = comment_ids[j - 1]
            items[parent_id]['kids'].append(comment_id)
        else:
            story['kids'].append(comment_id)

        comment = {
            'id': comment_id,
            'by': rng.choice(users),
            'text': rng.choice(COMMENT_TEXTS),
            'time': story_time + rng.randint(60, 60 * 60 * 24),
            'type': 'comment',
            'parent': parent_id,
            'kids': [],
        }
        items[comment_id] = comment

    top_ids.append(story_id)
    new_ids.append(story_id)
    best_ids.append(story_id)

top_ids = sorted(top_ids, key=lambda sid: items[sid]['score'], reverse=True)[:12]
new_ids = sorted(new_ids, key=lambda sid: items[sid]['time'], reverse=True)[:12]
best_ids = sorted(
    best_ids,
    key=lambda sid: items[sid]['score'] + items[sid]['descendants'] * 4,
    reverse=True,
)[:12]

LIST_ENDPOINTS = {
    '/topstories.json': top_ids,
    '/newstories.json': new_ids,
    '/beststories.json': best_ids,
}


class HNMockHandler(BaseHTTPRequestHandler):
    server_version = 'HNMock/1.0'

    def send_json(self, payload, status=200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith('/v0/'):
            path = path[3:]

        if path in LIST_ENDPOINTS:
            self.send_json(LIST_ENDPOINTS[path])
            return

        if path.startswith('/item/') and path.endswith('.json'):
            raw_id = path[len('/item/') : -len('.json')]
            try:
                item_id = int(raw_id)
            except ValueError:
                self.send_json({'error': 'item id must be an integer'}, status=400)
                return

            item = items.get(item_id)
            self.send_json(item if item is not None else None, status=200)
            return

        self.send_json({'error': 'not found', 'path': path}, status=404)


def start_demo_server_in_background(host: str = HOST, port: int = PORT) -> bool:
    thread = threading.Thread(target=main, daemon=True)
    thread.start()

    deadline = time.time() + 3.0
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.05)

    raise RuntimeError(f'Не удалось запустить демо-сервер на {host}:{port}')


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), HNMockHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\\nStopping server...')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
