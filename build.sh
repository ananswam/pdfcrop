#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Building the project..."
swift build -c release

echo "Creating Info.plist..."
cat <<EOF > Info.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PDFCrop</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.pdfcrop</string>
    <key>CFBundleName</key>
    <string>PDFCrop</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSMainNibFile</key>
    <string></string>
</dict>
</plist>
EOF

echo "Creating application bundle..."
BIN_PATH=$(swift build --show-bin-path -c release)
APP_NAME="PDFCrop.app"

# Clean up old version
rm -rf "$APP_NAME"

# Create directory structure
mkdir -p "$APP_NAME/Contents/MacOS"
mkdir -p "$APP_NAME/Contents/Resources"

# Add icon
iconutil -c icns AppIcon.iconset -o "$APP_NAME/Contents/Resources/AppIcon.icns"

# Copy executable
cp "$BIN_PATH/PDFCrop" "$APP_NAME/Contents/MacOS/"
ls -l "$APP_NAME/Contents/MacOS/"

# Move Info.plist
mv Info.plist "$APP_NAME/Contents/"
/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon.icns" "$APP_NAME/Contents/Info.plist"

# Create DMG
DMG_NAME="PDFCrop.dmg"
VOLUME_NAME="PDFCrop"

# Clean up old DMG
rm -f "$DMG_NAME"

echo "Creating DMG..."
hdiutil create -fs HFS+ -srcfolder "$APP_NAME" -volname "$VOLUME_NAME" "$DMG_NAME"

echo "Done. DMG created at $DMG_NAME"
