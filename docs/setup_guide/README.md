# Setup guide

`SETUP_GUIDE.tex` is the guide for a computer that has nothing installed. It takes a
reader from an empty machine to the README's *Verify* step: the project folder, Python,
the packages of each stage (Scraping, Extraction, Mapping), Tesseract for scans, the free
local engine, and starting the tool. Each step checks first and installs only what is
missing.

`SETUP_GUIDE.pdf` is the built copy. It is committed, so nobody has to build it to read
it. Rebuild it after editing the `.tex`.

## Building the PDF

| System | Do this |
| --- | --- |
| Windows | double-click `build.cmd`, or run it from a window |
| Mac, Linux | `./build.sh` in a Terminal (if it says *permission denied*: `chmod +x build.sh` once) |
| Anything, nothing installed | upload `SETUP_GUIDE.tex` to [Overleaf](https://www.overleaf.com) as a new project and press Recompile |

Both scripts run `pdflatex` twice (the second pass fills in the cross-references) and
leave `SETUP_GUIDE.pdf` next to the source. When `pdflatex` is missing they stop and
print the one-time install line for the system they are on:

| System | One-time install |
| --- | --- |
| Windows | `winget install MiKTeX.MiKTeX` |
| Mac | `brew install --cask mactex-no-gui` (needs [Homebrew](https://brew.sh)) |
| Debian, Ubuntu | `sudo apt install texlive-latex-extra` |

Open a new window after installing; the old one does not know the new program yet.
On MiKTeX the first build asks whether it may fetch the packages the guide uses
(`listings`, `enumitem`, `booktabs` and the like); allow it, it is a one-time download.

The guide is plain pdfLaTeX with standard packages only, so it builds the same
everywhere, Overleaf included.

## What is committed

`SETUP_GUIDE.tex`, `SETUP_GUIDE.pdf`, the two build scripts and this file. The `.aux`,
`.log` and `.out` files pdflatex leaves behind are kept out by the `.gitignore` here.
