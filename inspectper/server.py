import asyncio
from collections import namedtuple
import json
import os
import argparse

import psutil
import aiohttp
from aiohttp import web

from .commands import commands


script_dir = os.path.dirname(os.path.abspath(__file__))

# Global dictionary to store process objects by command string
process_dict = {}

async def handle(request):
    cmd = commands[request.query.get("cmd")]
    process = await cmd.gen_process()
    
    async def stream_output():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line

        process_dict[request.query.get('rand')] = None

    process_dict[request.query.get('rand')] = process

    # Return the streaming response
    return web.Response(body=stream_output(), headers={
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
        'X-Content-Type-Options': 'nosniff',
    })

async def handle_err(request):
    
    async def stream_output():
        while True:
            try:
                process = process_dict[request.query.get('rand')]
            except KeyError:
                await asyncio.sleep(0.5)
            else:
                break;

        if process:
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                yield line

    # Return the streaming response
    return web.Response(body=stream_output(), headers={
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
        'X-Content-Type-Options': 'nosniff',
    })

async def handle_kill(request):
    rand = request.query.get('rand')
    process = process_dict.pop(rand, None)
    if process:
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.kill()

        try:
            process.kill()
        except Exception:
            pass

    return web.Response(text='Process killed\n')


async def index(request):
    with open(os.path.join(script_dir,'index.html')) as fh:
        data = fh.read()
        data = data.replace('!!!DATA-HELP!!!', json.dumps({k: v.help.strip() for k,v in commands.items()}))
        data = data.replace('!!!DATA-SHORT!!!', json.dumps({k: v.short.strip() for k,v in commands.items()}))
        return web.Response(body=data, content_type='text/html')

app = web.Application()

app.add_routes([
    web.get('/', index),
    web.get('/run/', handle),
    web.get('/err/', handle_err),
    web.get('/kill/', handle_kill),
])

parser = argparse.ArgumentParser(description='standalone web server for performance investigation')
parser.add_argument('--port', type=int, default=8080, help='port for the server')

def main():
    args = parser.parse_args()
    web.run_app(app, host='127.0.0.1', port=args.port)

if __name__ == 'main':
    main()
