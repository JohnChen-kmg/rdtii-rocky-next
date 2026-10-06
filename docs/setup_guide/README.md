# Setup guide

Two documents for a computer that has nothing installed, each a `.tex` source with its
PDF built beside it:

| Source | Built copy | What it is |
| --- | --- | --- |
| `SETUP_GUIDE.tex` | `SETUP_GUIDE.pdf` | The full guide. Each step checks first and installs what is missing, says what each package is for, what a working setup looks like, and what to do when something is not found. |
| `SETUP_NOTE.tex` | `SETUP_NOTE.pdf` | The short note. The installs only, in order, until the tool opens. Whether everything works is left to the tool's own Check buttons and health dots. |

Both PDFs are committed, so nobody has to build them to read them. Rebuild after editing
a `.tex`.

## Building the PDFs

| System | Do this |
| --- | --- |
| Windows | double-click `build.cmd`, or run it from a window |
| Mac, Linux | `./build.sh` in a Terminal (if it says *permission denied*: `chmod +x build.sh` once) |
| Anything, nothing installed | upload the `.tex` to [Overleaf](https://www.overleaf.com) as a new project and press Recompile |

Both scripts take every `.tex` in this folder, run `pdflatex` on it twice (the second
pass fills in the cross-references) and leave the PDF next to the source. When
`pdflatex` is missing they stop and print the one-time install line for the system they
are on:

| System | One-time install |
| --- | --- |
| Windows | `winget install MiKTeX.MiKTeX` |
| Mac | `brew install --cask mactex-no-gui` (needs [Homebrew](https://brew.sh)) |
| Debian, Ubuntu | `sudo apt install texlive-latex-extra` |

Open a new window after installing; the old one does not know the new program yet.
On MiKTeX the first build asks whether it may fetch the packages the documents use
(`listings`, `enumitem`, `booktabs` and the like); allow it, it is a one-time download.

Both documents are plain pdfLaTeX with standard packages only, so they build the same
everywhere, Overleaf included.

## What is committed

The two `.tex` sources, their PDFs, the two build scripts and this file. The `.aux`,
`.log` and `.out` files pdflatex leaves behind are kept out by the `.gitignore` here.
