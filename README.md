<div align="center">

<img src="assets/scene.svg" width="100%" alt="Mitaro. Omar, computer science student at MTUCI, local-first and security. A mission-control collage in early-80s style: commits per day over the last 90 days as a glowing amber chart, the Campus project in orbit with its Java classes, UI components, tests, migrations, screens and versions, a starburst sun over a night ocean and a code listing about me.">
<a href="https://github.com/mitaro-cs/Campus"><img src="assets/monitors.svg" width="100%" alt="A wall of CRT monitors: languages as a wireframe mountain range, a Campus readout, the moon with the year I came online, and commits by hour in Moscow time as a stepped mountain."></a>
<img src="assets/desk.svg" width="100%" alt="Data desk: commits per repository, languages, commits per week over 26 weeks and cumulative commits over time with one glowing line per repository.">

[telegram](https://t.me/treadways) · [email](mailto:miri.saro@bk.ru) · [instagram](https://instagram.com/stere.os) · [campus](https://github.com/mitaro-cs/Campus)

</div>

**Campus** is a study-group site and app that lives on the group leader's own computer: homework, a schedule from an `.ics` file, news and files. It works offline, keeps files encrypted with AES-256-GCM and signs in with passkeys.

<details>
<summary><b>Run Campus</b></summary>

1. Download the installer from the [latest release](https://github.com/mitaro-cs/Campus/releases/latest): `macos-apple-silicon.dmg`, `macos-intel.dmg` or `windows-setup.exe`.
2. Install it. The app is not signed, so the system asks once: on macOS use System Settings → Privacy & Security → Open Anyway, on Windows More info → Run anyway.
3. On the first launch enter the group name, your name and a password: you become the admin and the group leader.
4. Management → Server → CloudPub → Open access gives a permanent link and a QR code for the group.

Classmates open the link, sign in and add the site to their home screen as an app.

</details>

<sub>Every chart is real data, drawn by a Python script in <code>/scripts</code> and refreshed by GitHub Actions every six hours.</sub>
