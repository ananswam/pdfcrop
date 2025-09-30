# PDFCrop

This is a macOS application for cropping PDFs. You can download the `.tar.gz` from [here](https://github.com/ananswam/pdfcrop/releases/download/v0.0.1/PDFCrop.tar.gz) or build it yourself.

This uses `PDFKit` to do PDF operations, which is built in on macOS. Warning: This entire thing is vibe coded.

## Building and Running

To build the application, run the following command:

```bash
./build.sh
```

This will create a `PDFCrop.app` file in the current directory. You can then run this application.

## Icon Setup

To set up the application icon, use the `setup_icon.sh` script. This script takes a single argument: the path to a 1024x1024 PNG file.

```bash
./setup_icon.sh icon.png
```

This will generate the `AppIcon.iconset` directory with all the required icon sizes.
