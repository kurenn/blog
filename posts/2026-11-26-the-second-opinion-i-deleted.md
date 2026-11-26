---
title: The second opinion I deleted
date: 2026-11-26
summary: I added a second reviewer to my dev loop, then measured what it caught and took it out.
---

[dev-loop](https://github.com/kurenn/dev-loop) is the loop I use to ship changes with Claude Code: plan, implement, run the gate, get an adversarial review, rate the result. For a while the rating step had a backup. When a verdict landed close to the line, a second rater looked at it again.

It felt responsible.

Then I checked what the second opinion could actually change. The gate already sends both kinds of serious finding, BLOCKING and MAJOR, to the same fix round. So the second rating only mattered in one narrow case: a real defect that got mislabelled and would otherwise have been waived. I had never measured that case. Every PR already lists its waivers in the description, so if it happened I would see it there.

What I had measured was how often the second rating would run. A correct change still drew a MAJOR on 10 out of 10 runs, so the "close call" path would have fired on almost every loop. That's a lot of extra tokens and minutes for a case I couldn't point to.

While I was at it, I tried to fix the inconsistency with more thinking instead. 180 rater calls across medium, high and extra-high effort. The verdict on an endpoint with its tests removed stayed inconsistent at every level: 3 out of 10, 0 out of 10, 3 out of 10. More effort didn't make it steadier. The rater was following the brief, and the brief calls that a MAJOR.

So I deleted the second rating and pinned nothing.

I keep relearning this one. An extra check isn't free just because it sounds careful. Before adding one, I now write down the case it would catch and go look for a real example. If I can't find one, the check doesn't go in.
