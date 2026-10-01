import os
import sys
import glob
import subprocess
import shutil

appdir = sys.argv[1]
libdir = os.path.join(appdir, "lib")
os.makedirs(libdir, exist_ok=True)

# Core system libraries that MUST come from host OS (GPU drivers, display servers, glibc, audio)
EXCLUDE_EXACT = {
    # glibc & core runtime
    "libc.so.6", "libm.so.6", "libdl.so.2", "librt.so.1", "libpthread.so.0",
    "ld-linux-x86-64.so.2", "libresolv.so.2", "libutil.so.1",
    # graphics drivers & displays (must match host GPU hardware)
    "libGL.so.1", "libGLX.so.0", "libEGL.so.1", "libGLdispatch.so.0",
    "libdrm.so.2", "libgbm.so.1",
    "libX11.so.6", "libxcb.so.1", "libX11-xcb.so.1", "libXext.so.6",
    "libXfixes.so.3", "libXcomposite.so.1", "libXdamage.so.1", "libXrandr.so.2",
    # audio drivers (must talk to host audio daemon)
    "libasound.so.2", "libpulse.so.0", "libpipewire-0.3.so.0",
    # desktop toolkit (use host GTK so themes/desktop integration work)
    "libgtk-3.so.0", "libgdk-3.so.0", "libglib-2.0.so.0", "libgobject-2.0.so.0",
    "libgio-2.0.so.0", "libcairo.so.2", "libcairo-gobject.so.2",
    "libpango-1.0.so.0", "libpangocairo-1.0.so.0", "libfontconfig.so.1",
}

EXCLUDE_STARTSWITH = (
    "ld-linux-", "libnvidia-",
)

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
]:
    for f in glob.glob(pat):
        soname = os.path.basename(f)
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
        if soname in EXCLUDE_EXACT or base in EXCLUDE_EXACT:
            continue
        if any(base.startswith(prefix) for prefix in EXCLUDE_STARTSWITH):
            continue
        
        dest = os.path.join(libdir, soname)
        if not os.path.exists(dest):
            print(f"Bundling dependency: {soname} from {target_path}")
            shutil.copy2(target_path, dest)
            copied.add(soname)
            to_inspect.append(dest)

print(f"Total bundled dependencies: {len(copied)}")
