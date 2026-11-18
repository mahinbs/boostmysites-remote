#!/usr/bin/env python3
"""BOOSTMYSITES Remote: every change we make to RustDesk's source, applied before the build.

RustDesk is AGPL-3.0. This repository is a public fork; the upstream sources stay untouched in git
and this script is the whole of our modification, so anyone can see exactly what differs:

  1. the app is named BOOSTMYSITES (app bundle, program file, service names, settings folder);
  2. it talks to the BOOSTMYSITES server (address and public key) when no other server is set;
  3. the icons are the BOOSTMYSITES mark;
  4. on macOS it has its own bundle identifier and link scheme, so it never collides with a
     stock RustDesk on the same computer.

Nothing is hidden or removed: the person at the computer still sees the tray icon and the
window that says who is connected, and the About page still credits RustDesk.

Run from anywhere:  python3 boostmysites/apply.py   (once, on a clean checkout with submodules)
Every replacement must match, or the script stops: a new upstream version that moved a line
fails the build loudly instead of shipping a half-renamed app.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ROOT / "boostmysites" / "icons"

NAME = "BOOSTMYSITES"
BUNDLE_ID = "com.boostmysites.remote"
SCHEME = "boostmysites"
SERVER = "187.126.120.55"
SERVER_KEY = "P2q4bXyznQL1BIgsCHJdpUPXUrPLvFWiizlaYUlNwXM="


def sub(path: str, old: str, new: str, count: int | None = None) -> None:
    """Replace `old` with `new` in a file, byte for byte (line endings are kept as they are)."""
    p = ROOT / path
    data = p.read_bytes()
    found = data.count(old.encode())
    if found == 0 or (count is not None and found != count):
        sys.exit(f"boostmysites/apply.py: {path}: expected {count or 'at least 1'} of {old!r}, found {found}")
    p.write_bytes(data.replace(old.encode(), new.encode()))
    print(f"  {path}: {found} x {old!r}")


def icon(src: str, dst: str) -> None:
    target = ROOT / dst
    if not target.parent.is_dir():
        sys.exit(f"boostmysites/apply.py: {dst}: the folder is gone")
    shutil.copyfile(ICONS / src, target)
    print(f"  {dst} <- icons/{src}")


marker = ROOT / "boostmysites" / ".applied"
if marker.exists():
    print("BOOSTMYSITES changes are already applied.")
    sys.exit(0)

print("1. Name and server")
sub("libs/hbb_common/src/config.rs", 'RwLock::new("RustDesk".to_owned())', f'RwLock::new("{NAME}".to_owned())', 1)
sub("libs/hbb_common/src/config.rs", '&["rs-ny.rustdesk.com"]', f'&["{SERVER}"]', 1)
sub("libs/hbb_common/src/config.rs", '"OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="', f'"{SERVER_KEY}"', 1)

print("2. macOS app")
# The Swift module keeps its name, so nothing compiled against it (the menu file, the plugin registrar) changes.
sub("flutter/macos/Runner/Configs/AppInfo.xcconfig", "PRODUCT_NAME = RustDesk", f"PRODUCT_NAME = {NAME}\nPRODUCT_MODULE_NAME = RustDesk", 1)
sub("flutter/macos/Runner.xcodeproj/project.pbxproj", "RustDesk.app", f"{NAME}.app", 4)
sub("flutter/macos/Runner.xcodeproj/project.pbxproj", "PRODUCT_BUNDLE_IDENTIFIER = com.carriez.rustdesk;", f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE_ID};", 3)
sub("flutter/macos/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme", "RustDesk.app", f"{NAME}.app", 4)
sub("flutter/macos/Runner/Info.plist", "<string>com.carriez.rustdesk</string>", f"<string>{BUNDLE_ID}</string>", 1)
sub("flutter/macos/Runner/Info.plist", "<string>rustdesk</string>", f"<string>{SCHEME}</string>", 1)
sub("build.py", "RustDesk.app", f"{NAME}.app")

print("3. Windows program details")
sub("flutter/windows/runner/Runner.rc", '"FileDescription", "RustDesk Remote Desktop"', f'"FileDescription", "{NAME} Remote Desktop"', 1)
sub("flutter/windows/runner/Runner.rc", '"InternalName", "rustdesk"', f'"InternalName", "{NAME}"', 1)
sub("flutter/windows/runner/Runner.rc", '"OriginalFilename", "rustdesk.exe"', f'"OriginalFilename", "{NAME}.exe"', 1)
sub("flutter/windows/runner/Runner.rc", '"ProductName", "RustDesk"', f'"ProductName", "{NAME}"', 1)

print("4. Icons")
icon("AppIcon.icns", "flutter/macos/Runner/AppIcon.icns")
icon("icon.ico", "flutter/windows/runner/resources/app_icon.ico")
icon("icon.ico", "res/icon.ico")
icon("tray-32.ico", "res/tray-icon.ico")
icon("icon-1024.png", "res/icon.png")
icon("icon-1024.png", "res/mac-icon.png")
icon("icon-32.png", "res/32x32.png")
icon("icon-64.png", "res/64x64.png")
icon("icon-128.png", "res/128x128.png")
icon("icon-256.png", "res/128x128@2x.png")
icon("mark-64.png", "res/mac-tray-dark-x2.png")
icon("mark-64.png", "res/mac-tray-light-x2.png")
# The app reads assets/icon.png first, for its own window and for the tray / menu-bar icon.
icon("mark-256.png", "flutter/assets/icon.png")

marker.write_text("applied\n")
print("BOOSTMYSITES changes applied.")
