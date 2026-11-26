---
title: Slow is not gone
date: 2026-12-02
summary: My sync app was killing healthy jobs because it treated a share that paused for a few seconds as dead.
---

[Trawl](https://github.com/kurenn/trawl) syncs Google Drive and pCloud folders into a local library, which in my case lives on an SMB share. Every 30 seconds it checks that the destination still answers. If the check takes longer than 10 seconds, Trawl decides the destination is unreachable and stops the sync.

One afternoon it stopped three syncs at once. The share was fine. The kernel log showed SMB stalling for a few seconds, then carrying on as if nothing had happened. Those few seconds were enough to push the check past 10, and Trawl reported that the destination had stopped responding.

The timeout was answering the wrong question. I wanted to know whether the share was gone. What it measured was whether the share was fast, and a network share is allowed to be slow for a moment.

The check now waits 45 seconds. A share that's really gone still gets caught, just a little later. I'll take that trade: waiting a bit longer to notice a dead share is cheap, and a sync killed for no reason means restarting it by hand and trusting the app a little less.

The same stall had a second symptom. Some commands, like listing folders, checking that a path exists or saving the folder mappings, ran on the main thread. When the share hung, the whole window froze with it. Those commands are async now, so a slow share makes one action wait instead of locking the app.

What I took from it: before setting a timeout, figure out what a healthy system looks like on its worst minute, and put the limit above that. Mine was set to the average minute, so normal behaviour looked like a failure.
