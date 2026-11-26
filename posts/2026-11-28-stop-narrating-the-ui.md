---
title: Stop narrating the UI
date: 2026-11-28
summary: My prototyping skill kept writing screens that described themselves, so I gave it copy rules and a sweep.
---

[claude-prototype](https://github.com/kurenn/claude-prototype) is a Claude Code skill that builds web app prototypes with no build step. In October I ran eleven A/B builds and read every screen. The layouts were fine. The words were not.

The screens kept explaining themselves. "The price updates as you go" showed up four times. "No guilt trip" showed up four times too. Six builds had a pair of rhetorical questions sitting above a form. Some screens had a line about the prototype itself, which no real product would ever say.

None of it was wrong, exactly. It just read like a narrator standing next to the app, describing the controls you can already see. Real interfaces don't do that. A price field that updates live doesn't need a sentence saying so; you watch it change.

The fix had two parts.

First, a copy reference the skill reads before it draws the first screen: ten rules, each with a bad and a good example. It also says when explaining is the right call, because sometimes it is: errors, empty states, irreversible actions, constraints and terms. "This deletes the project for everyone" earns its place. "Here you can manage your settings" doesn't.

Second, a sweep at the end of every build. A grep for the known patterns, plus one read through the copy. It flags all eleven October builds and nothing in the starter scaffold, which is the result I wanted: it catches the habit without nagging about clean screens.

The rule in the skill now fits on one line: never lorem ipsum, never narrate the UI.

If your generated screens feel slightly off and you can't say why, try reading only the text out loud. In my builds, that's where the problem was almost every time.
