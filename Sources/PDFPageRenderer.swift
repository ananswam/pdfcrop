
import PDFKit
import AppKit

struct PDFPageRenderer {
    static func render(page: PDFPage, with cropRect: CGRect?) -> NSImage {
        let pageBounds = page.bounds(for: .mediaBox)
        let width = Int(pageBounds.width)
        let height = Int(pageBounds.height)

        // Create a bitmap context in memory.
        guard let context = CGContext(data: nil, 
                                    width: width, 
                                    height: height, 
                                    bitsPerComponent: 8, 
                                    bytesPerRow: 0, 
                                    space: CGColorSpaceCreateDeviceRGB(), 
                                    bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue) else {
            return NSImage(size: pageBounds.size) // Return blank image on failure
        }

        // Both CGContext and PDFPage have a bottom-left origin, so no flipping is needed.

        // Draw the page and crop rect into the context.
        page.draw(with: .mediaBox, to: context)
        if let cropRect = cropRect {
            context.setStrokeColor(NSColor.red.cgColor)
            context.setLineWidth(2.0)
            context.addRect(cropRect)
            context.strokePath()
        }

        // Create a CGImage from the context, then create an NSImage from that.
        guard let cgImage = context.makeImage() else {
            return NSImage(size: pageBounds.size)
        }

        return NSImage(cgImage: cgImage, size: NSSize(width: width, height: height))
    }
}
