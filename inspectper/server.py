import asyncio
import aiohttp
from aiohttp import web
from collections import namedtuple
import json
import os
import argparse


script_dir = os.path.dirname(os.path.abspath(__file__))



Command = namedtuple("Command", ["gen_process", "help"])

def subprocess_shell(cmd):
    async def main():
        return await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    return main

# Global dictionary to store process objects by command string
process_dict = {}

commands = {
    "uptime": Command(
        subprocess_shell("uptime"),
        """
# uptime

indicate the number of tasks (processes) wanting to run.
On Linux systems,these numbers include processes wanting
to run on CPU, as well as processes blocked in uninterruptible I/O
(usually disk I/O).
        """.strip()
    ),
    "dmesg-tail": Command(
        subprocess_shell("dmesg | tail -n20"),
        """
# tail -n20

This views the last system messages, if there are any.
Look for errors that can cause performance issues.
The example above includes the oom-killer, and TCP dropping a request.
        """.strip()
    ),
    "vmstat1": Command(
        subprocess_shell("vmstat 1 3"),
        """
# vmstat 1 10

It prints a summary of key server statistics on each line.

vmstat was run with an argument of 1, to print one second summaries.
The first line of output (in this version of vmstat) has some columns
that show the average since boot, instead of the previous second. 
For now, skip the first line, unless you want to learn and remember which column is which.

* r: Number of processes running on CPU and waiting for a turn. 
This provides a better signal than load averages for determining CPU saturation,
as it does not include I/O. To interpret: an “r” value greater than 
the CPU count is saturation.

free: Free memory in kilobytes. If there are too many digits to count,
you have enough free memory. The “free -m” command, included as command 7,
better explains the state of free memory.

si, so: Swap-ins and swap-outs. If these are non-zero, you’re out of memory.

us, sy, id, wa, st: These are breakdowns of CPU time, on average across
all CPUs. They are user time, system time (kernel), idle, wait I/O,
and stolen time (by other guests, or with Xen, the guest’s own isolated driver domain).


        """.strip()
    ),
    "mpstat": Command(
        subprocess_shell("mpstat -P ALL 1 3"),
        """
# mpstat -P ALL 1 10

This command prints CPU time breakdowns per CPU, which can be used to check for an imbalance.
A single hot CPU can be evidence of a single-threaded application.
        """.strip()
    ),
    "pidstat": Command(
        subprocess_shell("pidstat 1 3"),
        """
# pidstat 1 10

Pidstat is a little like top’s per-process summary,
but prints a rolling summary instead of clearing the screen.
This can be useful for watching patterns over time, and also
recording what you saw (copy-n-paste) into a record of your investigation.
        """.strip()
    ),
    "iostat": Command(
        subprocess_shell("iostat -xz 1 3"),
        """
# iostat -xz 1 3

This is a great tool for understanding block devices (disks), 
both the workload applied and the resulting performance. Look for:

* r/s, w/s, rkB/s, wkB/s: These are the delivered reads, writes, read Kbytes,
and write Kbytes per second to the device. Use these for workload characterization.
A performance problem may simply be due to an excessive load applied.

* await: The average time for the I/O in milliseconds.
This is the time that the application suffers, as it includes both time queued and
time being serviced. Larger than expected average times can be an indicator of device saturation,
or device problems.

* avgqu-sz: The average number of requests issued to the device.
Values greater than 1 can be evidence of saturation (although devices 
can typically operate on requests in parallel, especially virtual devices
which front multiple back-end disks.)

* %util: Device utilization. This is really a busy percent,
showing the time each second that the device was doing work.
Values greater than 60% typically lead to poor performance
(which should be seen in await), although it depends on the device.
Values close to 100% usually indicate saturation.

If the storage device is a logical disk device fronting many back-end disks,
then 100% utilization may just mean that some I/O is being processed 100% of
the time, however, the back-end disks may be far from saturated,
and may be able to handle much more work.

Bear in mind that poor performing disk I/O isn’t necessarily an application issue.
Many techniques are typically used to perform I/O asynchronously,
so that the application doesn’t block and suffer the latency directly
(e.g., read-ahead for reads, and buffering for writes).
        """.strip()
    ),
    "free": Command(
        subprocess_shell("free -m"),
        """
# mpstat -P ALL 1 10

The right two columns show:

* buffers: For the buffer cache, used for block device I/O.

* cached: For the page cache, used by file systems.

We just want to check that these aren’t near-zero in size,
which can lead to higher disk I/O (confirm using iostat),
and worse performance. The above example looks fine, with many Mbytes in each.

The “-/+ buffers/cache” provides less confusing values for used and free memory.
Linux uses free memory for the caches, but can reclaim it quickly if applications need it.
So in a way the cached memory should be included in the free memory column,
which this line does. There’s even a website, linuxatemyram, about this confusion.

It can be additionally confusing if ZFS on Linux is used, as we do for some services,
as ZFS has its own file system cache that isn’t reflected properly by the free -m columns.
It can appear that the system is low on free memory, when that memory is in fact available
for use from the ZFS cache as needed.
        """.strip()
    ),
    "sar": Command(
        subprocess_shell("sar -n DEV 1 3"),
        """
# sar -n DEV 1 3

Use this tool to check network interface throughput:
rxkB/s and txkB/s, as a measure of workload, and also to check
if any limit has been reached. In the above example, eth0 receive
is reaching 22 Mbytes/s, which is 176 Mbits/sec (well under, say, a 1 Gbit/sec limit).
        """.strip()
    ),
    "sar-tcp": Command(
        subprocess_shell("sar -n TCP,ETCP 1 3"),
        """
# sar -n TCP,ETCP 1 3

This is a summarized view of some key TCP metrics. These include:

* active/s: Number of locally-initiated TCP connections per second (e.g., via connect()).

* passive/s: Number of remotely-initiated TCP connections per second (e.g., via accept()).

* retrans/s: Number of TCP retransmits per second.

The active and passive counts are often useful as a rough measure of server load:
number of new accepted connections (passive), and number of downstream connections (active).
It might help to think of active as outbound, and passive as inbound, 
but this isn’t strictly true (e.g., consider a localhost to localhost connection).

Retransmits are a sign of a network or server issue;
it may be an unreliable network (e.g., the public Internet),
or it may be due a server being overloaded and dropping packets.
The example above shows just one new TCP connection per-second.
        """.strip()
    ),
}

async def handle(request):
    cmd = commands[request.query.get("cmd")]
    process = await cmd.gen_process()
    
    async def stream_output():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line

    process_dict[request.query.get('rand')] = process

    # Return the streaming response
    return web.Response(body=stream_output(), headers={
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
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

        # Stream the output of the command
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            yield line

    # Set up the response headers for streaming
    headers = {
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
    }

    # Return the streaming response
    return web.Response(body=stream_output(), headers=headers)

async def handle_kill(request):
    rand = request.query.get('rand')
    process = process_dict.pop(rand, None)
    if process:
        process.kill()

    return web.Response(text='Process killed\n')


async def index(request):
    with open(os.path.join(script_dir,'index.html')) as fh:
        data = fh.read()
        data = data.replace('!!!DATA!!!', json.dumps({k: v.help for k,v in commands.items()}))
        return web.Response(body=data, content_type='text/html')

app = web.Application()

app.add_routes([
    web.get('/', index),
    web.get('/run/', handle),
    web.get('/err/', handle_err),
    web.get('/kill/', handle_kill),
])

parser = argparse.ArgumentParser(description='standalone web server for investigating performance')
parser.add_argument('--port', type=int, default=8080, help='port for the server')

def main():
    args = parser.parse_args()
    web.run_app(app, host='127.0.0.1', port=args.port)
