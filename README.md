<div align="center">

<img src="assets/banner.svg" width="100%" alt="Mitaro. Computer science student at MTUCI. Python, Flask, security.">
<br>
<img src="assets/stats.svg" width="100%" alt="GitHub in numbers: repositories, commits, stars, followers and the amount of code written.">

<br>

<img src="assets/head-about.svg" alt="Who am I">

</div>

<img src="assets/whoami.svg" align="left" width="292" hspace="14" alt="Halftone portrait of Omar, aka Mitaro">

I'm **Omar**, and online I go by **Mitaro**. I study computer science at **MTUCI** and I write mostly `Python` and `Flask`, with plain `JavaScript` on the front end.

The projects below lean on one idea: **local-first**. Two of them keep your files on your own machine, and none of them needs a cloud service in the middle. That's why I reach for `SQLite` and the local disk before I reach for someone else's servers.

Right now I'm getting better at backend architecture and at the security side of things: encryption, hashing, how to store a password properly. On the side I'm prototyping a personal AI assistant in the spirit of Jarvis, mostly to see how far I can push it.

Outside of code I train hand-to-hand combat. The habit of keeping a cold head under pressure carries over to debugging.

<br clear="left">

<div align="center">

<a href="https://t.me/treadways"><img src="assets/btn-telegram.svg" width="240" alt="Telegram, @treadways"></a>
<a href="mailto:miri.saro@bk.ru"><img src="assets/btn-email.svg" width="240" alt="Email, miri.saro@bk.ru"></a>
<a href="https://instagram.com/stere.os"><img src="assets/btn-instagram.svg" width="240" alt="Instagram, @stere.os"></a>

</div>

> [!CAUTION]
> Working product beats endless planning. Readable code beats clever code. Anything that touches user data gets security from day one.

<div align="center">

<img src="assets/head-build.svg" alt="What I build">
<br>
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
<img src="assets/numbers.svg" width="100%" alt="Public repositories, commits, kilobytes of code and years on GitHub, plus a bar of code by language. Most of it is Python, then HTML, CSS and JavaScript.">

<br>

<img src="assets/head-stack.svg" alt="My tech stack">
<br>
<img src="assets/stack.svg" width="100%" alt="Python, Flask, JavaScript, HTML5, CSS3, SQLite, Docker, Git, GitHub, GitHub Actions, Bash, Linux, Figma, Obsidian, Java, Zed.">

<br>

<img src="assets/head-obsidian.svg" alt="My Obsidian dashboard">
<br>
<img src="assets/obsidian.svg" width="100%" alt="A pixel-art sketch of my Obsidian home dashboard drawn as an old Macintosh window: a title tile with the day of the year, a clock, a dot calendar, study and recent lists, posters of what I am watching, stats tiles, a pixel portrait and the plugins it runs on.">

<sub>A pixel-art sketch of the layout with sample data. The real vault is private.</sub>

</div>

Obsidian is where everything that is not code lives: lecture notes, reading, a journal and a map of my projects. The vault is called **Equilibrium**: about 600 notes in 11 folders, versioned in Git.

Its home page is a dashboard I built myself. It is a single [Datacore](https://github.com/blacksmithgu/datacore) block written in JSX that asks the vault one question and draws everything from the answer. Paths, links and labels live in one config note instead of the code, so the dashboard keeps working when I rename a folder. The look is a separate CSS snippet of about 1,400 lines with a strict black-and-white system: matte panels, thin lines, no glow. It takes its colors from the active theme, so light and dark mode both work, and there is a layout for the phone too.

| Widget | What it does |
| --- | --- |
| **Header** | A sticker with the day of the year as a progress meter |
| **Clock** | A live clock; only this component re-renders every second |
| **Dot calendar** | One dot per day of the month, days with lecture notes light up, today is inverted |
| **Study** | Every subject folder with its note count and a check mark if I wrote something this week |
| **Recent** | The latest lecture, practice and lab notes, tagged LEC, PRA or LAB |
| **Watching** | Posters of what I am watching with season and episode badges, loaded only when they scroll into view |
| **Stats** | Notes, edits in the last seven days, films and series, counted straight from the vault |
| **Links** | Quick pills to the planner, the cinema shelf and the rest of the vault |

Around the dashboard: **Bases** for the film and series shelves, **Kanban**, **Calendar**, **Excalidraw** for diagrams, and a vault map note with the tag dictionary, my rules for notes and a set of ready-made queries.

<div align="center">

<img src="assets/head-timeline.svg" alt="Timeline">
<br>
<img src="assets/timeline.svg" width="100%" alt="July 2022 joined GitHub. December 2024 Mouros. February 2026 AetherCloud. April 2026 VantaVault and Campus Coworking. September 2026 Java and Python practice repos and this profile.">

<br>

<img src="assets/head-now.svg" alt="Right now">

</div>

- Building **Flask** backends with cleaner structure
- Studying **security**: encryption, hashing, local-first design
- Prototyping a personal **AI assistant**, Jarvis-style
- Studying computer science at **MTUCI**

<div align="center">

<img src="assets/footer.svg" width="100%" alt="Thanks for reading.">

</div>
