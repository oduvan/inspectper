import asyncio

from collections import namedtuple


Command = namedtuple("Command", ["gen_process", "short", "help"])

def subprocess_shell(cmd):
    async def main():
        return await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    return main

commands = {
    "uptime": Command(
        subprocess_shell("uptime"),
        short="show how long system has been running",
        help="# uptime"
    ),
    "who": Command(
        subprocess_shell("who -a"),
        short="display who is on the system",
        help="# who -a",
    ),
    "dmesg-tail": Command(
        subprocess_shell("dmesg | tail -n100"),
        short="This views the last system messages",
        help="""
# dmesg | tail -n100
        """
    ),
    "vmstat": Command(
        subprocess_shell("vmstat"),
        short="system statistics",
        help="""
# vmstat

* r: The number of processes waiting for CPU time.

* b: The number of processes blocked waiting for I/O.

* free: Free memory in kilobytes. If there are too many digits to count,
you have enough free memory. The “free -m” command, included as command 7,
better explains the state of free memory.

* in: This column shows the number of interrupts per second. 

* cs: This column shows the number of context switches per second. 

* si, so: Swap-ins and swap-outs. If these are non-zero, you’re out of memory.

* us, sy, id, wa, st: These are breakdowns of CPU time, on average across
all CPUs. They are user time, system time (kernel), idle, wait I/O,
and stolen time (by other guests, or with Xen, the guest’s own isolated driver domain).
        """
    ),
    "mpstat": Command(
        subprocess_shell("mpstat -P ALL"),
        short="CPU time breakdowns per CPU",
        help="""
# mpstat -P ALL

* %usr: the percentage of time the CPU in user mode, executing user processes.

* %nice: the percentage of time the CPU was executing processes with a "nice" value greater than zero. The "nice" value is a priority setting for processes, with higher values indicating lower priority.

* %sys: the percentage of time the CPU was in system mode, executing system processes.

* %iowait: the percentage of time the CPU was waiting for I/O operations to complete.

* %irq: the percentage of time the CPU was handling interrupts from hardware devices.

* %soft: the percentage of time the CPU was handling "soft" interrupts,
which are software-generated interrupts used by the operating system.

* %steal: the percentage of time the CPU was "stolen" by a virtual machine hypervisor for use by another virtual machine.

* %guest: This column shows the percentage of time the CPU or processor core was executing code on behalf
of a virtual machine.

* %gnice: This column shows the percentage of time the CPU or processor core was executing processes
with a "nice" value of -20, which indicates a high-priority process.

* %idle: This column shows the percentage of time the CPU or processor core was idle and not executing any processes.
        """
    ),
    "pidstat-cpu": Command(
        subprocess_shell("pidstat --human -u"),
        short="CPU utilization of individual processes",
        help="""
# pidstat -u

* %usr: Percentage of CPU used by the task while executing at the user level (application),
with or without nice priority. Note that this field does NOT include  time  spent 
running  a virtual processor.

* %system: Percentage of CPU used by the task while executing at the system level (kernel).

* %guest: Percentage of CPU spent by the task in virtual machine (running a virtual processor).

* %wait: Percentage of CPU spent by the task while waiting to run.

* %CPU: Total percentage of CPU time used by the task. In an SMP environment,
the task's CPU usage will be divided by the total number of CPU's 
if option -I has been entered on the command line.
        """
    ),
    "pidstat-io": Command(
        subprocess_shell("pidstat --human -d"),
        short="Report I/O statistics of individual processes",
        help="""
# pidstat --human -d

* kB_rd/s: Number of kilobytes the task has caused to be read from disk per second.

* kB_wr/s: Number of kilobytes the task has caused, or shall cause to be written to disk per second.

* kB_ccwr/s: Number of kilobytes whose writing to disk has been cancelled by the task.
This may occur when the task truncates some dirty pagecache. In this case,
some IO which  another  task has been accounted for will not be happening.

* iodelay: Block  I/O  delay of the task being monitored, measured in clock ticks.
This metric includes the delays spent waiting for sync block I/O completion
and for swapin block I/O completion.
        """
    ),
    "pidstat-mem": Command(
        subprocess_shell("pidstat --human -r"),
        short="page faults and memory utilization of individual processes",
        help="""
# pidstat --human -r

* minflt/s: Total number of minor faults the task has made per second,
those which have not required loading a memory page from disk.

* majflt/s: Total number of major faults the task has made per second,
those which have required loading a memory page from disk.

* VSZ: Virtual Size: The virtual memory usage of entire task in kilobytes.

* RSS: Resident Set Size: The non-swapped physical memory used by the task in kilobytes.

* %MEM: The tasks's currently used share of available physical memory.
        """
    ),
    "pidstat-desc": Command(
        subprocess_shell("pidstat --human -v"),
        short="page faults and memory utilization of individual processes",
        help="""
# pidstat --human -v

* threads: Number of threads associated with current task.

* fd-nr: Number of file descriptors associated with current task.
        """
    ),
    "pidstat-switch": Command(
        subprocess_shell("pidstat --human -w"),
        short="task switching activity of individual processes",
        help="""
# pidstat --human -w

* cswch/s: Total number of voluntary context switches the task made per second. 
A voluntary context switch occurs when a task blocks because it requires a resource that is unavailable.

* nvcswch/s: Total  number  of  non voluntary context switches the task made per second.
A involuntary context switch takes place when a task executes for the duration
of its time slice and then is forced to relinquish the processor.
        """
    ),
    "iostat": Command(
        subprocess_shell("iostat -xz"),
        short="CPU and IO statistics for devices and partitions",
        help="""
# iostat -xz

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
        """
    ),
    "free": Command(
        subprocess_shell("free -m"),
        short="free and used memory",
        help="""
# free -m

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
        """
    ),
    "sar": Command(
        subprocess_shell("sar -n DEV"),
        short="check network interface",
        help="""
# sar -n DEV

rxkB/s and txkB/s, as a measure of workload, and also to check
if any limit has been reached. In the above example, eth0 receive
is reaching 22 Mbytes/s, which is 176 Mbits/sec (well under, say, a 1 Gbit/sec limit).
        """
    ),
    "sar-tcp": Command(
        subprocess_shell("sar -n TCP,ETCP"),
        short="TCP metrics",
        help="""
# sar -n TCP,ETCP

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
        """
    ),
}

for _name, _com in (
            ("vmstat", "vmstat 1"),
            ("mpstat", "mpstat -P ALL 1"),
            ("pidstat-cpu", "pidstat --human -u 1"),
            ("pidstat-io", "pidstat --human -d 1"),
            ("pidstat-mem", "pidstat --human -r 1"),
            ("pidstat-desc", "pidstat --human -v 1"),
            ("pidstat-switch", "pidstat --human -w 1"),
            ("iostat", "iostat -xz 1"),
            ("sar", "sar -n DEV 1"),
            ("sar-tcp", "sar -n TCP,ETCP 1")
        ):
    commands[_name + '-nonstop'] = Command(
        subprocess_shell(_com), commands[_name].short + ' (once per sec)', commands[_name].help
    )