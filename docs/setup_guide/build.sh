#!/bin/sh
# Builds SETUP_GUIDE.pdf from SETUP_GUIDE.tex on a Mac or Linux. Run it from the folder it is in: ./build.sh
set -e
cd "$(dirname "$0")"

if ! command -v pdflatex >/dev/null 2>&1; then
    echo "pdflatex was not found on this computer."
    echo
    case "$(uname -s)" in
        Darwin)
            echo "One-time install (needs Homebrew, from https://brew.sh), then open a new Terminal window and run ./build.sh again:"
            echo "    brew install --cask mactex-no-gui"
            ;;
        *)
            echo "One-time install on Debian or Ubuntu, then run ./build.sh again:"
            echo "    sudo apt install texlive-latex-extra"
            ;;
    esac
    echo
    echo "Without installing anything: upload SETUP_GUIDE.tex to https://www.overleaf.com"
    echo "as a new project, press Recompile and download the PDF from there."
    exit 1
fi

# Twice: the first pass records the cross-references, the second pass prints them.
pdflatex -interaction=nonstopmode -halt-on-error SETUP_GUIDE.tex
pdflatex -interaction=nonstopmode -halt-on-error SETUP_GUIDE.tex

echo
echo "Built SETUP_GUIDE.pdf"
