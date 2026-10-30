# PuffPAI Store policy

Nothing leaves your computer without your consent. Every package in the store keeps that promise.

1. **Open source.** The package has an open source license from the store's list (`scripts/store.py`, `LICENSES`). Everything in the store is free.
2. **Every host is declared.** Each outside address the package talks to is in `needs.hosts`. The Bridge refuses everything else, and `puffpai check` fails a package that tries.
3. **No personal data in the package.** No names, emails, addresses, keys or tokens in its files.
4. **No faces of real people.** Avatars are drawings or shapes, not likenesses.
5. **Changes are declared.** A tool that changes data, spends money, sends messages or touches devices is listed in `abilities.changes`.
6. **Says what it does.** The description and README match what the package actually does.
7. **No tricks.** No hidden downloads, no code fetched at run time that `puffpai check` did not see, no getting around the Bridge or Drawbridge.

## Tiers

- **Community:** passes `puffpai check` Level 1 or higher. PuffPAI has not read it, and the Yes card says so.
- **Verified:** passes Level 3, and PuffPAI read its code, its network calls and where it keeps data at that exact commit. A new commit needs a new review.

## Pulling a package

PuffPAI may refuse or pull any package that breaks these rules. A pulled version goes in `yanked.json` with the reason. Bots warn their owner and offer to remove it. Nothing is removed from anyone's computer without their Yes.

To report a package, open an issue.
