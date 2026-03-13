# Installation

This guide walks you through everything you need to install and set up DOE with Claude Code. Even if you've never used a terminal before, you'll be up and running by the end.

## What you need before starting

### A computer

Mac, Windows, or Linux all work. The examples in these docs use Mac, but the commands are almost identical on all three platforms — we'll note any differences as they come up.

### A terminal

The terminal is a text-based interface to your computer. Instead of clicking icons and menus, you type commands and press Enter. It looks like a blank screen with a blinking cursor — and it's where all your interactions with Claude Code happen. VSCode has a built-in terminal (Terminal > New Terminal) so you don't need a separate app.

**How to open it:**

- **Mac** — Open Finder, go to Applications > Utilities, and double-click Terminal. Or press Cmd+Space, type "Terminal", and hit Enter.
- **Windows** — Search for "Windows Terminal" or "PowerShell" in the Start menu. Windows Terminal is recommended if you have it.
- **Linux** — Press Ctrl+Alt+T, or find Terminal in your applications menu.

Don't worry if the terminal feels unfamiliar. You'll pick it up quickly — most of what you'll do is type short commands and read the output.

### VSCode

Visual Studio Code (VSCode) is a free code editor. You'll use it to see your project files and run Claude Code. Download it from [code.visualstudio.com](https://code.visualstudio.com). The Claude Code extension is also available in the VSCode marketplace.

### A Claude account

Sign up at [claude.ai](https://claude.ai). You'll need a Pro or Max subscription to use Claude Code. No API key is needed — Claude Code handles authentication automatically when you run `claude` for the first time.

### Git

Git is a save system for your code. Every time you finish a piece of work, you "commit" it — like saving your game. If something breaks later, you can go back to any previous save. This is one of the most important tools in software development, and DOE relies on it heavily.

**To install it:**

- **Mac** — Open your terminal and type `git --version`. If Git isn't installed, macOS will prompt you to install it (via Xcode Command Line Tools). Follow the prompts.
- **Windows** — Download from [git-scm.com](https://git-scm.com) and run the installer. Use the default settings.
- **Linux** — Run `sudo apt install git` (Ubuntu/Debian) or `sudo dnf install git` (Fedora).

**To check it's installed:**

```
git --version
```

You should see something like `git version 2.43.0`.

**One-time setup** — tell Git who you are (this labels your save points):

```
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Choose your setup

There are three ways to use Claude Code. All three work identically with DOE — the commands and workflow are the same. Only the interface is different.

**Option A: VSCode Extension** (recommended for beginners)

Install the Claude Code extension from the VSCode marketplace. Claude appears as a sidebar panel inside VSCode. You can see your files, terminal, and Claude all in one window.

**Option B: VSCode Terminal**

Open VSCode's built-in terminal (Terminal > New Terminal) and run `claude` from there. Same as using a standalone terminal, but inside VSCode so you can see your files alongside the terminal.

**Option C: Standalone Terminal**

Use your system terminal (Terminal on Mac, Windows Terminal on Windows). Run `claude` directly. Best if you're comfortable with command-line tools.

All three options work identically with DOE. The commands and workflow are the same — only the interface is different. These docs show terminal commands, which work in all three setups.

## Step-by-step installation

### 1. Download and install VSCode

Go to [code.visualstudio.com](https://code.visualstudio.com) and download the version for your operating system. Run the installer and follow the prompts — the defaults are fine.

Once installed, open VSCode. You'll use it as your main workspace for seeing files and running commands.

### 2. Install Git

Git tracks every change you make. See the Git section above for platform-specific instructions.

### 3. Open the terminal in VSCode

In VSCode, go to **Terminal > New Terminal** (or press Ctrl+` on Windows/Linux, Cmd+` on Mac). A terminal panel will appear at the bottom of the VSCode window. This is where you'll run the remaining commands.

### 4. Install Claude Code

Install Claude Code following the instructions at the [Claude Code website](https://docs.anthropic.com/en/docs/claude-code). Alternatively, if you're using VSCode, you can install the **Claude Code extension** directly from the VSCode marketplace — search for "Claude Code" in the Extensions panel.

### 5. Run Claude Code

In your terminal, type:

```
claude
```

The first time you run it, Claude Code will walk you through authentication with your Claude account. No API key is needed — it handles this automatically. Just follow the prompts to sign in with your Claude Pro or Max account.

### 6. Get the DOE Starter Kit

The DOE Starter Kit is a collection of files that set up the framework in your project — configuration, commands, hooks, and scripts.

**Option 1: Clone from GitHub (recommended)**

```
git clone https://github.com/yourusername/doe-starter-kit.git my-project
cd my-project
```

This creates a new folder called `my-project` with all the DOE files inside. You can replace `my-project` with whatever name you want.

**Option 2: Download as a ZIP**

Go to the GitHub repository page, click the green "Code" button, select "Download ZIP", and unzip it wherever you want your project to live.

### 7. Run the setup script

From inside your project folder, run:

```
bash setup.sh
```

This script does several things automatically:

- Installs the slash commands (like `/stand-up` and `/wrap`) so Claude Code recognises them
- Sets up Git hooks — automatic checks that run every time you save your work (they catch common mistakes before they become problems)
- Creates the directory structure DOE expects (`directives/`, `execution/`, `tasks/`, etc.)
- Initialises Git if it's not already set up

### 8. Verify it works

Start Claude Code from your project folder:

```
claude
```

You should see Claude Code's interface appear — a text prompt where you can type.

Now check that the DOE commands are available:

```
/commands
```

This should show a list of available slash commands, including things like `/stand-up`, `/wrap`, and `/sitrep`. If you see these, everything is working.

Type `/exit` or press Ctrl+C to leave Claude Code for now.

## What just happened

Here's what you now have installed:

- **VSCode** — the code editor where you see your files and run commands
- **Git** — the save system that tracks every change
- **Claude Code** — the AI coding assistant, authenticated with your Claude account
- **The DOE Starter Kit** — a project folder with all the configuration, commands, hooks, and scripts that make DOE work

Your project folder now has a specific structure — with directories for directives, execution scripts, tasks, and more. You don't need to memorise this right now. The [Configuration](configuration.md) guide explains each piece, and Claude Code itself knows where everything goes.

Next step: [Your First Session](first-session.md) — where you'll actually build something.
