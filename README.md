# PuffPAI Store

Apps, looks, avatars, tools and skills for your PuffPAI. Browse them at [puffpai.com/store](https://puffpai.com/store).

This repo is the store's index. Each file in `index/` points at one package in its own repo and pins one exact commit. `index.json` is the whole list in one file; the store check rebuilds it on every change.

| Tier | What it means |
|---|---|
| **Verified** | PuffPAI read it at that exact commit, and it passes `puffpai check` Level 3 |
| **Community** | Anyone can add it. It passes `puffpai check`, but PuffPAI has not read it |

**Add yours:** [CONTRIBUTING.md](CONTRIBUTING.md). **The rules:** [POLICY.md](POLICY.md). **Pulled versions:** `yanked.json`.

**Run your own store:** fork this repo and point your bot at your fork's `index.json`. Only PuffPAI's own store can mark a package Verified.

**Check locally:**

```
python scripts/store.py check            # every row
python scripts/store.py check my-app     # one row
python scripts/store.py build            # every row, then write index.json
```

It needs `git` and the `puffpai` command from a PuffPAI install.

Cypher Sisters. puff puff pass.
