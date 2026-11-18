"""Writes .github/workflows/boostmysites.yml from RustDesk's own flutter-build.yml: the same steps, only fewer of them."""
import pathlib, re, sys
repo = pathlib.Path(sys.argv[1])
up = (repo / ".github/workflows/flutter-build.yml").read_text().split("\n")

def job(name):
    start = next(i for i, l in enumerate(up) if l == f"  {name}:")
    end = next((i for i in range(start + 1, len(up)) if re.match(r"  [A-Za-z#]", up[i])), len(up))
    return up[start:end]

def steps(lines):
    i = next(k for k, l in enumerate(lines) if l == "    steps:")
    out, cur = [], None
    for l in lines[i + 1:]:
        if l.startswith("      - "):
            cur = [l]; out.append(cur)
        elif cur is not None:
            cur.append(l)
    for s in out:
        while s and (not s[-1].strip() or s[-1].lstrip().startswith("#")): s.pop()
    return out

def ident(step):
    for l in step:
        m = re.match(r"\s+(?:- )?name: (.*)", l)
        if m: return m.group(1).strip()
    for l in step:
        m = re.match(r"\s+(?:- )?uses: ([^@\s]+)", l)
        if m: return m.group(1)
    raise SystemExit("step with no name: " + step[0])

def pick(all_steps, names):
    by = {}
    for s in all_steps: by.setdefault(ident(s), s)
    out = []
    for n in names:
        if isinstance(n, list): out.append(n); continue
        if n not in by: raise SystemExit(f"upstream step not found: {n}\n have: {list(by)}")
        out.append(by[n])
    return out

def replace_in(step, old, new):
    text = "\n".join(step)
    assert old in text, old
    return text.replace(old, new).split("\n")

def cut_after(step, marker):
    """Keep a run script up to and including the line that contains `marker`."""
    k = next(i for i, l in enumerate(step) if marker in l)
    return step[:k + 1]

# ---- env: upstream's versions, without its secrets and inputs
e0 = up.index("env:"); e1 = up.index("jobs:")
env = [l for l in up[e0:e1] if not re.search(r"secrets\.|inputs\.|^\s*#signing", l)]
while env and not env[-1].strip(): env.pop()

APPLY = ["      - name: Apply the BOOSTMYSITES changes",
         "        shell: bash",
         "        run: python3 boostmysites/apply.py"]

mac = steps(job("build-for-macOS"))
mac_steps = pick(mac, [
    "Export GitHub Actions cache environment variables", "Checkout source code", APPLY,
    "Install build runtime", "Install NASM", "Install flutter", "Keep CocoaPods for Flutter 3.44 (arm64)", "Patch flutter",
    "Workaround for flutter issue", "Patch RustDesk sources for Flutter 3.44 (arm64)", "Install Rust toolchain", "Swatinem/rust-cache",
    "Restore bridge files", "Setup vcpkg with Github Actions binary cache", "Install vcpkg dependencies",
    "Show version information (Rust, cargo, Clang)", "Build rustdesk",
])
mac_steps += [[
    "      - name: Check the name and pack the app (unsigned)",
    "        run: |",
    "          APP=./flutter/build/macos/Build/Products/Release/BOOSTMYSITES.app",
    "          test -x \"$APP/Contents/MacOS/BOOSTMYSITES\"",
    "          test -x \"$APP/Contents/MacOS/service\"",
    "          test \"$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' \"$APP/Contents/Info.plist\")\" = com.boostmysites.remote",
    "          test \"$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' \"$APP/Contents/Info.plist\")\" = BOOSTMYSITES",
    "          test \"$(\"$APP/Contents/MacOS/BOOSTMYSITES\" --version)\" = \"$VERSION\"",
    "          lipo -archs \"$APP/Contents/MacOS/BOOSTMYSITES\"",
    "          # ditto keeps the links inside the app's frameworks; a plain zip or a folder upload breaks them, and the signature with them",
    "          ditto -c -k --sequesterRsrc --keepParent \"$APP\" boostmysites-remote-${{ env.VERSION }}-${{ matrix.job.arch }}-unsigned.zip",
    "          cp flutter/macos/Runner/Release.entitlements Release.entitlements",
    "          shasum -a 256 boostmysites-remote-*.zip",
], [
    "      - name: Upload the unsigned macOS app",
    "        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1",
    "        with:",
    "          name: boostmysites-remote-macos-${{ matrix.job.arch }}",
    "          path: |",
    "            boostmysites-remote-${{ env.VERSION }}-${{ matrix.job.arch }}-unsigned.zip",
    "            Release.entitlements",
    "          if-no-files-found: error",
]]

win = steps(job("build-for-windows-flutter"))
win_steps = pick(win, [
    "Export GitHub Actions cache environment variables", "Checkout source code", APPLY, "Restore bridge files",
    "Install LLVM and Clang", "Install flutter", "Replace engine with rustdesk custom flutter engine", "Patch flutter",
    "Install Rust toolchain", "Swatinem/rust-cache", "Setup vcpkg with Github Actions binary cache", "Install vcpkg dependencies",
    "Build rustdesk", "find Runner.res",
])
# The build step: only the build itself. The virtual-display driver and the printer driver are left out.
k = next(i for i, s in enumerate(win_steps) if ident(s) == "Build rustdesk")
win_steps[k] = cut_after(win_steps[k], "mv ./flutter/build/windows/") + [
    "          # The program carries our name from the start (the installer would rename it anyway)",
    "          mv ./rustdesk/rustdesk.exe ./rustdesk/BOOSTMYSITES.exe",
]
win_steps += [[
    "      - name: Build the installer (self-extracting, unsigned)",
    "        shell: bash",
    "        run: |",
    "          sed -i '/dpiAware/d' res/manifest.xml",
    "          pushd ./libs/portable",
    "          pip3 install -r requirements.txt",
    "          python3 ./generate.py -f ../../rustdesk/ -o . -e ../../rustdesk/BOOSTMYSITES.exe",
    "          popd",
    "          mkdir -p ./out",
    "          mv ./target/release/rustdesk-portable-packer.exe ./out/boostmysites-remote-${{ env.VERSION }}-${{ matrix.job.arch }}.exe",
    "          sha256sum ./out/*.exe",
], [
    "      - name: Upload the Windows installer",
    "        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1",
    "        with:",
    "          name: boostmysites-remote-windows-${{ matrix.job.arch }}",
    "          path: ./out",
    "          if-no-files-found: error",
]]

def header(lines, keep_matrix_archs):
    """A job's lines up to `steps:`, with its matrix cut to the wanted archs."""
    i = lines.index("    steps:")
    head = lines[:i]
    return head

mac_head = job("build-for-macOS"); mac_head = mac_head[:mac_head.index("    steps:")]
win_head = job("build-for-windows-flutter"); win_head = win_head[:win_head.index("    steps:")]
# Windows: x64 only, and no dependency on the privacy-mode helper window (we do not ship it).
wtxt = "\n".join(win_head)
a = wtxt.index("          - {\n              target: aarch64-pc-windows-msvc"); b = wtxt.index("            }", a) + len("            }")
wtxt = wtxt[:a].rstrip("\n") + wtxt[b:]
assert "needs: [build-RustDeskTempTopMostWindow, generate-bridge]" in wtxt
wtxt = wtxt.replace("needs: [build-RustDeskTempTopMostWindow, generate-bridge]", "needs: [generate-bridge]")
win_head = wtxt.rstrip("\n").split("\n")

out = [
    "# BOOSTMYSITES Remote: RustDesk built under our name for macOS (Apple silicon + Intel) and Windows (64-bit).",
    "# The steps are RustDesk's own (.github/workflows/flutter-build.yml at the same tag), fewer of them, plus",
    "# boostmysites/apply.py right after checkout. Nothing is signed here: the Mac app is signed on our own Mac.",
    "# Written by boostmysites/gen-workflow.py: after moving to a new RustDesk version run it again; do not edit by hand.",
    "# A build starts when a tag bms-<version>-<n> is pushed, or by hand from the Actions tab.",
    "name: BOOSTMYSITES Remote",
    "",
    "on:",
    "  workflow_dispatch:",
    "  push:",
    "    tags:",
    "      - 'bms-*'",
    "",
    "permissions:",
    "  contents: read",
    "",
] + env + ["", "jobs:", "  generate-bridge:", "    uses: ./.github/workflows/bridge.yml", ""]

def emit(head, st):
    lines = list(head) + ["    steps:"]
    for s in st: lines += s + [""]
    return lines

out += emit(mac_head, mac_steps) + emit(win_head, win_steps)
text = "\n".join(out).rstrip("\n") + "\n"
for bad in ("secrets.", "inputs.", "MACOS_P12", "SIGN_BASE_URL"):
    assert bad not in text, bad
(repo / ".github/workflows/boostmysites.yml").write_text(text)
print(len(text.split("\n")), "lines")
