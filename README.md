# xihub-desktop releases

Public release artifacts for [xihub-desktop](https://github.com/Xiracom-Limited/xihub-desktop) (private repo — source code lives there, this repo only ever holds built releases).

Download the latest installer for your platform from the [Releases page](https://github.com/Xiracom-Limited/xihub-desktop-releases/releases/latest).

Publishing a release here also mirrors it to our S3 (Garage) bucket automatically (see `.github/workflows/mirror-to-s3.yml`) — Garage has no anonymous/public access, so it's served publicly via `https://xihub.co.ke/downloads/desktop/` (LMS's `DesktopDownloadController`) rather than a raw S3 URL. The in-app updater checks that first and falls back to this repo if it's unreachable.
