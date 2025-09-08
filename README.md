# dwcom

**dwcom** is a plugin for the [TeamTalk Commander](https://dlee.org/teamtalk/ttcom) that enables the distribution of events through sounds, speech, notifications, and logs.

---

## Installation & Setup

### Prerequisites

Before installing the plugin, you must install its dependencies.
The instructions below assume a standard `pip` installation. If you are using a virtual environment, Anaconda, or another Python environment, adapt the commands accordingly.

```bash
pip install accessible_output3 cyal soundfile ntfpy pyprowl notify_py
```

---

### macOS-Specific Requirements

On macOS, `pyobjc` and `appkit` are required for NSSpeech support. You may also need [Homebrew](https://brew.sh) installed for certain dependencies.

1. Install Homebrew (see [Homebrew homepage](https://brew.sh) for instructions).
2. Install `pyobjc` and `appkit` for NSSpeech support:

```bash
pip install pyobjc
pip install appkit
```

> **Important:** Install them in the exact order shown above.
> Do **not** attempt to install both at once.

#### If Installation Fails

If `pyobjc` or `appkit` fails to install, try installing additional build dependencies with Homebrew:

```bash
brew install cmake
brew install cairo
```

Then retry the `pyobjc` and `appkit` installation steps.
If it still fails, there is no known solution at this time.
In this case, use VoiceOver in the ttcom configuration instead of `nsspeech`.

#### Case Sensitivity Fix for appkit

If installation succeeds, locate the `appkit` folder in your Python site-packages (path varies depending on your environment) and rename it from:

```
appkit → AppKit
```

Without this change, importing `appkit` will fail.

---

Got it 👍 — here’s a smoother rewrite of the Linux section so it matches the tone and flow of the macOS one:

---

### GNU/Linux-Specific Requirements

On Linux, **speech-dispatcher** is required to enable speech output.

1. Install `speech-dispatcher` (package names vary by distribution):

* **Debian/Ubuntu-based:**

```bash
sudo apt install speech-dispatcher
```
* **Red Hat-based:**

```bash
sudo yum install speech-dispatcher
```
* **Arch-based:**

```bash
sudo pacman -S speech-dispatcher
```

2. Depending on your distribution, the package may be named differently:

* `speechd`
* `lib-speech-dispatcher`

3. If you want, you can also install python espeak backends.

* `python-espeak`
* `python-espeak-ng`

---

## Plugin Installation

Before installing dwcom, navigate to your `ttcom` directory and create a `plugins` folder if it does not already exist.

```bash
mkdir plugins
cd plugins
```

You can then install the plugin using one of the methods below.

---

### Method 1 — Git

From within the `plugins` folder:

```bash
git clone https://github.com/dragonwolfsp/dwcom
```

Installation complete.

---

### Method 2 — Release Download

1. Visit the [latest release page](https://github.com/dragonwolfsp/dwcom/releases/latest).
2. Download the attached `dwcom.tar` file.
3. Extract it to:

```
<your_ttcom_directory>/plugins/dwcom
```

That’s it — you’re all set.

---

# Configuration

**dwcom** includes several configuration options, all of which can be applied to any or all server configurations in `ttcom`.

> **Note:**  
> Changing configuration options requires refreshing the `ttcom` configuration file using the `refresh` command.  
> This may cause `ttcom` to log out and back into multiple servers at once.

You can place any configuration option:
- **Under a specific server’s section** — to apply only to that server.
- **Under the server defaults section** — to apply to all servers.

Boolean options accept:
- **Truthy:** `true`, `1`, `y`, `yes`  
- **Falsy:** `false`, `0`, `n`, `no`

Keys are **not** case-sensitive.  
For example, `speechdModule` is the same as `speechdmodule`.

---

## Configuring Speech

By default:
- Speech is **enabled** for all servers.
- The speech method (`speechEngine`) is set to `auto`.
- Speech interruption is **enabled**.

### Options

| Option          | Type     | Description |
|-----------------|----------|-------------|
| `speech`        | bool     | Enables or disables speech. Default: `true`. |
| `speechEngine`  | string   | Speech engine to use. Options: `auto`, `dolphin`, `espeak`, `jaws`, `nsspeech`, `nvda`, `pctalker`, `sapi`, `speechd`, `systemaccess`, `voiceover`, `windoweyes`, `zdsr`. |
| `speechInterrupt` | bool   | If `true`, new speech interrupts current speech. Default: `true`. |
| `speechdModule` | string   | Output module for Speech Dispatcher. Ignored if Speech Dispatcher is not used. |
| `speechVoice`   | string   | Voice for the selected engine (if supported). |
| `speechRate`    | number   | Speech rate for the selected engine. |
| `speechVolume`  | number   | Output volume for the selected engine. |
| `speechPitch`   | number   | Pitch for the selected engine. |
| `noSpeak`       | string   | Prevents certain events from being spoken. |

---

### `noSpeak` Usage

`noSpeak` accepts a list of event names joined with `+`.  
Example: disable speech for `updateuser`, `updatechannel`, and `serverupdate` events:

```

noSpeak = updateuser+updatechannel+serverupdate

```

**Common event names:**
- `updateuser` — User status changes
- `adduser` — User joins channel
- `removeuser` — User leaves channel
- `loggedin` — User logs in
- `loggedout` — User logs out

---

---

### Randomized Login/Logout Messages

dwcom supports **custom randomized speech messages** for login and logout events.

* Create the following text files in your `ttcom/text/` directory:

  * `logins.txt`
  * `logouts.txt`

* Each file should contain one possible spoken message **per line**.

* When a user logs in or out, dwcom will randomly select a line from the corresponding file to speak.

If the files are missing or empty, dwcom falls back to the default messages:

* `"logged in"`
* `"logged out"`

**Example (`logins.txt`):**

```
runeports in with a flash of golden light.
soars in from on high
Charges in, blade held high
```

**Example (`logouts.txt`):**

```
runeports away in a flash of golden light.
leaps into the sky, soaring away.
Draws a blade and charges off.
```

---

## Configuring Sounds

By default:
- Sounds are **enabled**.
- Sound pack: `default`.
- Playback type: `overlapping`.
- Volume: `100`.

### Options

| Option          | Type     | Description |
|-----------------|----------|-------------|
| `sounds`        | bool     | Enables/disables sounds. Default: `true`. |
| `soundPack`     | string   | Name of the sound pack. Default: `default`. |
| `soundVolume`   | number (0–100) | Playback volume. Default: `100`. |
| `playbackType`  | string   | How sounds are played. Options: `overlapping`, `interrupting`, `oneByOne`. Default: `overlapping`. |
| `noSound`       | string   | Prevents certain events from playing sounds. Usage is the same as `noSpeak` |

---

## Configuring Notifications

By default:
- All notifications are **disabled**.
- When enabled, login/logout events and messages will trigger notifications.

### Options

| Option          | Type     | Description |
|-----------------|----------|-------------|
| `notifyLogInOut` | bool    | Notify when users log in/out. Default: `true`. |
| `notifyMessage` | bool     | Notify when a message is received. Default: `true`. |

---

### Ntfy Notifications

[Ntfy](https://ntfy.sh) is a free, open-source, HTTP-based pub/sub push notification service.

| Option     | Type   | Description |
|------------|--------|-------------|
| `ntfy`     | bool   | Enable/disable Ntfy notifications. Default: `false`. |
| `ntfyTopic`| string | Ntfy topic to publish to. |
| `ntfyUrl`  | string | URL of the Ntfy instance. |

---

### Prowl Notifications

[Prowl](https://www.prowlapp.com/) is a push notification service for iOS.

| Option     | Type   | Description |
|------------|--------|-------------|
| `prowl`    | bool   | Enable/disable Prowl notifications. Default: `false`. |
| `prowlKey` | string | Prowl API key. |

---

### System Notifications

dwcom can send notifications directly to the system it is running on.

| Option         | Type   | Description |
|----------------|--------|-------------|
| `systemNotify` | bool   | Enable/disable system notifications. |

---

## Configuring Logging

By default:
- Logging is **enabled**.
- Max log size: `4 MB` per file.
- Max log files: `5`.
- Total log storage: ~`20 MB` before rotating.

### Options

| Option        | Type   | Description |
|---------------|--------|-------------|
| `log`         | bool   | Enable/disable logging. Default: `true`. |
| `maxLogSize`  | number | Max size (in MB) before log rotation. Default: `4`. |
| `maxLogFiles` | number | Max number of log files before overwriting oldest. Default: `5`. |

---

# Known Issues

* **Windows COM Errors**  
  On Windows systems, `COM` errors may sometimes occur when attempting to use speech output.
