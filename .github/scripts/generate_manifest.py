import os
import glob
import json
import datetime

tag = os.environ.get("RELEASE_TAG", "")
version = tag.lstrip("v")
base = f"https://xihub.co.ke/downloads/desktop/{tag}"
assets_dir = "release-assets"

win_exe = next((os.path.basename(f) for f in glob.glob(f"{assets_dir}/*.exe")), None)
win_zip = next((os.path.basename(f) for f in glob.glob(f"{assets_dir}/*win*.zip") or glob.glob(f"{assets_dir}/*.zip")), None)
linux_deb = next((os.path.basename(f) for f in glob.glob(f"{assets_dir}/*.deb")), None)
linux_tar = next((os.path.basename(f) for f in glob.glob(f"{assets_dir}/*linux*.tar.gz") or glob.glob(f"{assets_dir}/*.tar.gz")), None)
linux_appimage = next((os.path.basename(f) for f in glob.glob(f"{assets_dir}/*.AppImage")), None)

platforms = {}
if win_exe:
    platforms["windows-x86_64"] = {"url": f"{base}/{win_exe}"}
    platforms["windows-x86_64-nsis"] = {"url": f"{base}/{win_exe}"}
if win_zip:
    platforms["windows-x86_64-zip"] = {"url": f"{base}/{win_zip}"}
if linux_deb:
    platforms["linux-x86_64-deb"] = {"url": f"{base}/{linux_deb}"}
    platforms["linux-x86_64"] = {"url": f"{base}/{linux_deb}"}
if linux_tar:
    platforms["linux-x86_64-tar"] = {"url": f"{base}/{linux_tar}"}
if linux_appimage:
    platforms["linux-x86_64-appimage"] = {"url": f"{base}/{linux_appimage}"}
    platforms["linux-x86_64"] = {"url": f"{base}/{linux_appimage}"}

manifest = {
    "version": version,
    "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "platforms": platforms,
}

os.makedirs(assets_dir, exist_ok=True)
output_path = os.path.join(assets_dir, "latest.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated {output_path}:")
print(json.dumps(manifest, indent=2))
