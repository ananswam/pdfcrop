// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "PDFCrop",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "PDFCrop", targets: ["PDFCrop"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "PDFCrop",
            path: "Sources"
        )
    ]
)
