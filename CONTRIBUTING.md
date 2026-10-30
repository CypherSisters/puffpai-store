# Add your package to the PuffPAI Store

Anyone can add a package. It goes on the Community shelf, and owners see that PuffPAI has not read it.

## 1. Make it

Start from a package of the same kind in [puffpai-packages](https://github.com/CypherSisters/puffpai-packages): copy its folder, then change the `id`, name and contents. (`puffpai new <kind> <id>` will make a starter folder; it is not built yet.)

Kinds: `app`, `tool`, `skill`, `page`, `ui`, `avatar`, `look`, `agent`, `knowledge`, `bundle`, `provider`. The package contract is in BuildBotv2 `docs/02_PACKAGE_CONTRACT.md`, and the walkthrough is in `docs/04_DEVELOPERS.md`.

Put it in your own public GitHub repo. One package per repo, or one folder per package.

## 2. Check it

```
puffpai check <folder>
```

Fix it until it passes **Level 3**. Level 1 is the minimum to install; Level 3 is the store's bar, and the store check below refuses anything under Level 1.

## 3. Add one file here

Fork this repo and add `index/<id>.json`:

```json
{
  "id": "my-app",
  "kind": "app",
  "repo": "https://github.com/you/my-app",
  "path": "",
  "commit": "<the full 40-character commit id>",
  "tier": "community"
}
```

- `path` is the folder inside your repo that holds `puffpai.json` (empty for the repo root).
- `commit` pins one exact commit. Owners install exactly that commit, never a branch.
- `tier` is always `community`. Only PuffPAI sets `verified`.
- Name, description, version, license and icon come from your `puffpai.json`, so they are not repeated here.

Then open a pull request. The store check fetches your commit, compares it with the row, and runs `puffpai check`. It posts what passed and what did not. A maintainer reads it, runs `puffpai check` on it too, and merges. (For now the online check compares the row only; `puffpai check` runs on the maintainer's computer.)

## 4. Updates

Change `commit` in your row and open a new pull request. Owners are offered the update, and nothing updates without their Yes.

## Rules

Read [POLICY.md](POLICY.md) before you submit. Anything that breaks it is refused or pulled.
