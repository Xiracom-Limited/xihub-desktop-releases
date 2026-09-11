# xihub-desktop releases

Public release artifacts for [xihub-desktop](https://github.com/Xiracom-Limited/xihub-desktop) (private repo — source code lives there, this repo only ever holds built releases).

Download the latest installer for your platform from the [Releases page](https://github.com/Xiracom-Limited/xihub-desktop-releases/releases/latest).

Publishing a release here also mirrors it to `https://s3.xiracom.co.ke/xihub-releases/desktop/` automatically (see `.github/workflows/mirror-to-s3.yml`) — the in-app updater checks S3 first and falls back to this repo if S3 is unreachable.
