<div align="center">

<img src="assets/banner.svg" width="100%" alt="Mitaro. Computer science student at MTUCI. Python, Flask, security.">
<br>
<img src="assets/stats.svg" width="100%" alt="GitHub in numbers: repositories, commits, stars, followers and the amount of code written.">

<br>

<img src="assets/head-about.svg" alt="Who am I">

</div>

I'm **Omar**, and online I go by **Mitaro**. I study computer science at **MTUCI**. I started with `Python` and `Flask`, and lately I also write `Java` with Spring Boot and `Svelte` for bigger projects.

The projects below lean on one idea: **local-first**. In all four the data stays on a machine you control instead of a cloud service in the middle. That's why I reach for `SQLite` and the local disk before I reach for someone else's servers.

Right now I'm getting better at backend architecture and at the security side of things: encryption, hashing, how to store a password properly. On the side I'm prototyping a personal AI assistant in the spirit of Jarvis, mostly to see how far I can push it.

Outside of code I train hand-to-hand combat. The habit of keeping a cold head under pressure carries over to debugging.

<div align="center">

<a href="https://t.me/treadways"><img src="assets/btn-telegram.svg" width="240" alt="Telegram, @treadways"></a>
<a href="mailto:miri.saro@bk.ru"><img src="assets/btn-email.svg" width="240" alt="Email, miri.saro@bk.ru"></a>
<a href="https://instagram.com/stere.os"><img src="assets/btn-instagram.svg" width="240" alt="Instagram, @stere.os"></a>

</div>

<div align="center">

<img src="assets/rules.svg" width="100%" alt="House rules. Working product beats endless planning. Readable code beats clever code. Anything that touches user data gets security from day one.">

</div>

<div align="center">

<img src="assets/head-build.svg" alt="What I build">
<br>
<a href="https://github.com/mitaro-cs/StorageSystem"><img src="assets/project-groupbase.svg" width="100%" alt="groupbase, the StorageSystem repository. A study-group app that runs on the group leader's own PC. Works offline, files encrypted on disk with AES-256-GCM, sign-in by QR code or fingerprint, roles and moderation, exam countdown, host app for Windows and macOS with one-click updates. Java, Spring Boot, Svelte, Tauri."></a>

</div>

<details>
<summary><b>How to run groupbase</b></summary>

Download the installer from the [latest release](https://github.com/mitaro-cs/StorageSystem/releases/latest): `windows-setup.exe` for Windows 10 and 11, `macos-apple-silicon.dmg` or `macos-intel.dmg` for a Mac.

1. Install it. On macOS drag it to Applications; if the system cannot verify the developer, use System Settings → Privacy & Security → Open Anyway. On Windows choose More info → Run anyway. No admin rights needed.
2. On the first launch enter the group name, your name and a password. You become the site admin and the group leader.
3. Open Settings → Server → Internet, sign in to the free tunnel and press "Open access" to get a permanent link and a QR code for the group.

Or build it yourself (JDK 21+ and Node.js 22+):

```bash
git clone https://github.com/mitaro-cs/StorageSystem.git groupbase
cd groupbase
make build
java -jar target/groupbase.jar serve
```

How it fits together: `Tauri host app` → `Spring Boot server` → `SQLite`; every phone keeps its own copy of the data and syncs when the host computer is back on.

</details>

<div align="center">

<a href="https://github.com/mitaro-cs/VantaVault"><img src="assets/project-vantavault.svg" width="100%" alt="VantaVault. A private vault for external drives. Password access with PBKDF2-SHA256, local AES-encrypted archives, session protection, lockout after failed logins, automatic drive detection. Python, JavaScript, HTML, CSS."></a>

</div>

<details>
<summary><b>How to run VantaVault</b></summary>

```bash
git clone https://github.com/mitaro-cs/VantaVault.git
cd VantaVault
chmod +x main && ./main      # macOS / Linux
.\main.ps1                   # Windows (PowerShell), or open main.bat
```

</details>

<div align="center">

<a href="https://github.com/mitaro-cs/AetherCloud"><img src="assets/project-aethercloud.svg" width="100%" alt="AetherCloud. Turns your own disk into a private cloud with a web dashboard. Nested folders, uploads, image previews, per-user quotas, disk sync check, installable PWA, Docker Compose. Flask, SQLite."></a>

</div>

<details>
<summary><b>How to run AetherCloud</b></summary>

```bash
git clone https://github.com/mitaro-cs/AetherCloud.git
cd AetherCloud
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python AetherCloud.py        # then open http://127.0.0.1:5000

# or with Docker
cp .env.example .env && docker compose up -d
```

How it fits together: `Client / PWA` → `Flask routes and templates` → `SQLite metadata` → `local disk or a mounted volume`.

</details>

<div align="center">

<a href="https://github.com/mitaro-cs/KworkingSystem"><img src="assets/project-coworking.svg" width="100%" alt="Campus Coworking. A booking panel for a university coworking space. Seat booking with overlap checks, check-in by student ID, profiles and themes, Pomodoro, lofi, study library, REST API. Flask, SQLite, vanilla JavaScript."></a>

</div>

<details>
<summary><b>How to run Campus Coworking</b></summary>

```bash
git clone https://github.com/mitaro-cs/KworkingSystem.git
cd KworkingSystem
./start_macos.command        # Windows: start_windows.bat
```

The start file creates a virtual environment, installs `requirements.txt`, opens the browser and serves the app on `http://127.0.0.1:5000`. Set `PORT=8000` to change the port.

</details>

Also in my repositories: [Mouros](https://github.com/mitaro-cs/Mouros) is my Python practice archive, and [Java](https://github.com/mitaro-cs/Java) and [Python](https://github.com/mitaro-cs/Python) hold the first steps in each language.

<div align="center">

<img src="assets/head-reel.svg" alt="The commit reel">
<br>
<img src="assets/reel.svg" width="100%" alt="A film strip where every frame is one of my real commits, newest first, with its date, its repository and its unedited message.">

<sub>Every frame is a real commit from my repositories, unedited. The strip updates itself.</sub>

<br>

<img src="assets/head-numbers.svg" alt="By the numbers">
<br>
<img src="assets/numbers.svg" width="100%" alt="Public repositories, commits, megabytes of code and years on GitHub, plus a bar of code by language. Most of it is Java, then Svelte, Python and TypeScript.">

<br>

<img src="assets/head-stack.svg" alt="My tech stack">
<br>
<img src="assets/stack.svg" width="100%" alt="Python, Flask, Java, Spring, Svelte, TypeScript, JavaScript, HTML5, CSS3, SQLite, Docker, Git, GitHub, GitHub Actions, Bash, Linux, Figma, Obsidian, Rust, Tauri, Zed.">

<br>

<img src="assets/head-timeline.svg" alt="Timeline">
<br>
<img src="assets/timeline.svg" width="100%" alt="July 2022 joined GitHub. December 2024 Mouros. February 2026 AetherCloud. April 2026 VantaVault and Campus Coworking. September 2026 Java and Python practice repos, groupbase and this profile.">

<br>

<img src="assets/head-now.svg" alt="Right now">

</div>

- Building **Java** and **Flask** backends with cleaner structure
- Studying **security**: encryption, hashing, local-first design
- Prototyping a personal **AI assistant**, Jarvis-style
- Studying computer science at **MTUCI**

<div align="center">

<img src="assets/footer.svg" width="100%" alt="Thanks for reading.">

</div>
