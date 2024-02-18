![auto_patch release](https://img.shields.io/badge/release-version1.0-blue)

# AUTO PATCH

```
 █████╗ ██╗   ██╗████████╗ ██████╗     ██████╗  █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║
███████║██║   ██║   ██║   ██║   ██║    ██████╔╝███████║   ██║   ██║     ███████║
██╔══██║██║   ██║   ██║   ██║   ██║    ██╔═══╝ ██╔══██║   ██║   ██║     ██╔══██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║     ██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
```

# Description

This project is designed to facilitate the rapid selection of repositories and corresponding commits within environments hosting multiple Git repositories, such as Android, Linux kernel, and other types of SDKs, through an interactive interface. It automates the generation of diff files and source files based on the selected commits.

# Setup

- Install a Python version that is 3.6 or newer.
- install [FZF](https://github.com/junegunn/fzf)

# Usage

run auto_patch.py and generate patch files in auto_create_patch.

```
python3 auto_patch.py -i [sdk path] -o [patch path]
```
