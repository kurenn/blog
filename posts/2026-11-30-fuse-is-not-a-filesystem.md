---
title: "fuse" is not a filesystem type
date: 2026-11-30
summary: A NAS on Linux slipped past my network-share check because the kernel only said "fuse".
---

[Trove](https://github.com/kurenn/trove) is a desktop library for 3D print files. It watches your folders for changes, except on network shares. Watching a NAS produces phantom events, and phantom events trigger rescans that never stop. Version 2.0.7 added a guard against that.

On macOS. On every other platform, the check was a stub that returned false. So a NAS indexed on Linux was stored as an ordinary local folder with watching turned on, which brought back the exact rescan loop the guard was written for. I found it by mounting a real SMB share on a Linux desktop and looking at the row in the database.

The obvious fix is `statfs`: ask the kernel for the filesystem type and compare it against CIFS and NFS. I didn't use it, on purpose. When you connect to a server from the Files app, the normal desktop way, GVFS mounts it through FUSE, and `statfs` just says "fuse". A magic-number check would miss the most common real setup entirely.

`/proc/self/mountinfo` has the real name: `fuse.gvfsd-fuse`. Trove now reads that. Plain `fuse` and `fuseblk` stay watchable, because local FUSE mounts like AppImages, phones over MTP or NTFS drives still deserve live updates.

Two details I'm glad the tests pin down. Mount points match by path component, so `/mnt/nasty` is not inside `/mnt/nas`. And mount points with spaces arrive octal-escaped, so they get unescaped before comparing.

Libraries that were already stored wrong fix themselves on the next launch, since the startup migration always called the check. It just never fired on Linux before.

Windows still assumes everything is local. That's the next one.
