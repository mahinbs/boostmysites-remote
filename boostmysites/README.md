# BOOSTMYSITES Remote

This is [RustDesk](https://github.com/rustdesk/rustdesk) built under the BOOSTMYSITES name. RustDesk is free software
under the AGPL-3.0 licence; this fork is public so that anyone who receives our build can get the exact source it was made from.

The upstream sources are kept as they are. Everything we change is in this folder:

| File | What it does |
| --- | --- |
| `apply.py` | The whole modification, applied to a clean checkout before the build: the app name, our server address and public key as the built-in default, the macOS bundle identifier and link scheme, the Windows program details, the icons. |
| `icons/` | The BOOSTMYSITES icons `apply.py` copies in. |
| `gen-workflow.py` | Writes `.github/workflows/boostmysites.yml` from RustDesk's own build recipe (fewer steps, nothing added but `apply.py`). |

What is **not** changed: the person at the computer still sees the tray / menu-bar icon and the window that shows who is
connected, can end a session and can remove the app at any time. There is no hidden mode. The About page still credits RustDesk.

## Building

Push a tag `bms-<rustdesk version>-<n>` on the branch `boostmysites-<rustdesk version>` (or run the workflow by hand).
The run leaves three artifacts: the unsigned macOS app for Apple silicon and for Intel, and the Windows 64-bit installer.
The macOS apps are signed afterwards with our Developer ID and published under Releases.

## Moving to a new RustDesk version

1. Branch from the new upstream tag and bring this folder over.
2. `python3 boostmysites/gen-workflow.py .` and commit the result.
3. Push a tag. If upstream moved a line `apply.py` relies on, the build stops there and says which one.
