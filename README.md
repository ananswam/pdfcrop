# PDF Auto-Cropper for E-ink Devices

A Python tool that automatically crops PDF pages to remove margins and creates uniform-sized pages, optimized for better viewing on e-ink devices like Kindle, Kobo, and other e-readers.

## Installation

### Install uv

Run `curl -LsSf https://astral.sh/uv/install.sh | sh` on your terminal. Close and re-open the window.

### Install Dependencies

From the `crop` directory, run `./install.sh`. This will install everything.

## Usage

### GUI Mode (Recommended)

The easiest way to use the tool is with the interactive GUI:

```bash
uv run crop.py --gui ~/Downloads/your-document.pdf
```

The GUI allows you to:
- Preview pages and navigate through the document
- Select crop areas by clicking and dragging
- Set page ranges for cropping (only specific pages)
- Toggle between viewing all pages or just the crop range
- See real-time preview of what will be cropped

### Command Line Mode

For automated processing or when you know the exact crop margins:

```bash
# Auto-detect optimal crop margins
uv run crop.py document.pdf

# Specify custom crop margins (as percentages 0.0-1.0)
uv run crop.py document.pdf --left 0.1 --right 0.1 --top 0.05 --bottom 0.05

# Short form
uv run crop.py document.pdf -l 0.15 -r 0.1 -t 0.08 -b 0.12

# Specify output file
uv run crop.py document.pdf -o cropped-output.pdf

# Adjust auto-detection parameters
uv run crop.py document.pdf --buffer 0.02 --footer-height 0.15
```

#### Command Line Options

- `--left`, `-l`: Left margin to crop (0.0-1.0)
- `--right`, `-r`: Right margin to crop (0.0-1.0) 
- `--top`, `-t`: Top margin to crop (0.0-1.0)
- `--bottom`, `-b`: Bottom margin to crop (0.0-1.0)
- `--output`, `-o`: Output PDF path
- `--buffer`: Buffer space around auto-detected content (default: 0.01)
- `--footer-height`: Height ratio to check for footer content (default: 0.1)
- `--no-optimize`: Disable PDF compression

If no crop margins are specified, the tool automatically analyzes the PDF to detect optimal margins by finding content boundaries and avoiding footers/page numbers.

## Features

- **Automatic margin detection**: Analyzes PDF content to find optimal crop boundaries
- **Footer detection**: Intelligently ignores page numbers and footer content
- **Interactive GUI**: Visual selection of crop areas with live preview
- **Uniform page sizing**: Creates consistent page dimensions across the document
- **Page range selection**: Crop only specific pages while leaving others unchanged
- **E-ink optimization**: Optimized output for better e-reader viewing