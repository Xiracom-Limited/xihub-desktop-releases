import os
import sys
import glob
import subprocess
import shutil

appdir = sys.argv[1]
libdir = os.path.join(appdir, "lib")
os.makedirs(libdir, exist_ok=True)

# System and desktop libraries that MUST come from the host OS
# Bundling these causes fatal symbol collisions with the host's GLib/GTK/GStreamer/Wayland/X11
EXCLUDE_PREFIXES = (
    # Core system & C/C++ runtime
    "libc.", "libm.", "libdl.", "libpthread.", "librt.", "ld-linux",
    "libstdc++", "libgcc_s", "libresolv.", "libutil.",
    # OS plumbing & service bus
    "libmount", "libselinux", "libsystemd", "libdbus", "libblkid",
    "libcap", "libudev", "libpcre",
    # Crypto & TLS (must match host certificates / crypto subsystem)
    "libgcrypt", "libgpg-error", "libgnutls", "libnettle", "libhogweed",
    "libp11-kit", "libtasn1",
    # Desktop toolkit & graphics subsystem
    "libglib", "libgobject", "libgio", "libgmodule", "libgthread",
    "libgtk", "libgdk", "libpango", "libcairo", "libharfbuzz",
    "libfontconfig", "libfreetype", "libepoxy", "libxkbcommon",
    "libatk", "libatspi",
    # Display drivers & servers (GPU hardware integration)
    "libGL", "libGLX", "libEGL", "libGLdispatch", "libdrm", "libgbm",
    "libwayland", "libX11", "libxcb", "libXext", "libXfixes", "libXcomposite",
    "libXdamage", "libXrandr", "libXcursor", "libXinerama", "libXi",
    "libnvidia",
    # Audio & media frameworks (must talk to host audio daemon)
    "libasound", "libpulse", "libpipewire", "libgst", "libgstreamer",
)

def is_excluded(filename):
    # NEVER exclude Flutter app binaries / plugins
    if filename == "xihub" or filename.endswith("_plugin.so") or filename in (
        "libflutter_linux_gtk.so", "libwebrtc.so", "libpdfium.so", "libdartjni.so",
        "libsentry.so", "libsqlite3.so", "crashpad_handler", "libapp.so"
    ):
        return False
    return any(filename.startswith(prefix) for prefix in EXCLUDE_PREFIXES)

def get_ldd_deps(filepath):
    try:
        out = subprocess.check_output(["ldd", filepath], stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return {}
    deps = {}
    for line in out.splitlines():
        line = line.strip()
        if "=>" in line:
            parts = line.split("=>")
            soname = parts[0].strip()
            rest = parts[1].strip()
            target = rest.split()[0] if rest else ""
            if target and os.path.isfile(target):
                deps[soname] = target
        elif line.startswith("/") and os.path.isfile(line.split()[0]):
            target = line.split()[0]
            soname = os.path.basename(target)
            deps[soname] = target
    return deps

to_inspect = []

# Seed with all libav and libsw libraries installed on system
for pat in [
    "/usr/lib/x86_64-linux-gnu/libav*.so*",
    "/usr/lib/x86_64-linux-gnu/libsw*.so*",
    "/usr/lib/x86_64-linux-gnu/libayatana-appindicator3*.so*",
]:
    for f in glob.glob(pat):
        soname = os.path.basename(f)
        if is_excluded(soname):
            continue
        dest = os.path.join(libdir, soname)
        if not os.path.exists(dest):
            if os.path.islink(f):
                linkto = os.readlink(f)
                try:
                    os.symlink(linkto, dest)
                except Exception:
                    shutil.copy2(f, dest)
            else:
                shutil.copy2(f, dest)
            to_inspect.append(dest)

# Also inspect all binaries already in appdir
for root, _, files in os.walk(appdir):
    for f in files:
        p = os.path.join(root, f)
        if f.endswith(".so") or f == "xihub" or ".so." in f:
            to_inspect.append(p)

seen = set()
copied = set()

while to_inspect:
    curr = to_inspect.pop()
    if curr in seen:
        continue
    seen.add(curr)
    deps = get_ldd_deps(curr)
    for soname, target_path in deps.items():
        base = os.path.basename(target_path)
        if is_excluded(soname) or is_excluded(base):
            continue
        
        dest = os.path.join(libdir, soname)
        if not os.path.exists(dest):
            print(f"Bundling dependency: {soname} from {target_path}")
            shutil.copy2(target_path, dest)
            copied.add(soname)
            to_inspect.append(dest)

print(f"Total bundled dependencies: {len(copied)}")
