
import SwiftUI
import PDFKit

struct CropControlsView: View {
    @Binding var cropRect: CGRect?
    let pageBounds: CGRect

    // Custom bindings that translate between the CGRect (in points) and margin values (as proportions 0.0-1.0).
    private var topMargin: Binding<Double> {
        Binding(
            get: { 
                guard let rect = cropRect, pageBounds.height > 0 else { return 0 }
                return (pageBounds.maxY - rect.maxY) / pageBounds.height
            },
            set: { newValue in
                guard var rect = cropRect else { return }
                let marginInPoints = newValue * pageBounds.height
                let newMaxY = pageBounds.maxY - marginInPoints
                rect = CGRect(x: rect.minX, y: rect.minY, width: rect.width, height: newMaxY - rect.minY)
                cropRect = rect
            }
        )
    }

    private var bottomMargin: Binding<Double> {
        Binding(
            get: { 
                guard let rect = cropRect, pageBounds.height > 0 else { return 0 }
                return (rect.minY - pageBounds.minY) / pageBounds.height
            },
            set: { newValue in
                guard var rect = cropRect else { return }
                let marginInPoints = newValue * pageBounds.height
                let newMinY = pageBounds.minY + marginInPoints
                let oldMaxY = rect.maxY
                rect = CGRect(x: rect.minX, y: newMinY, width: rect.width, height: oldMaxY - newMinY)
                cropRect = rect
            }
        )
    }

    private var leftMargin: Binding<Double> {
        Binding(
            get: { 
                guard let rect = cropRect, pageBounds.width > 0 else { return 0 }
                return (rect.minX - pageBounds.minX) / pageBounds.width
            },
            set: { newValue in
                guard var rect = cropRect else { return }
                let marginInPoints = newValue * pageBounds.width
                let newMinX = pageBounds.minX + marginInPoints
                let oldMaxX = rect.maxX
                rect = CGRect(x: newMinX, y: rect.minY, width: oldMaxX - newMinX, height: rect.height)
                cropRect = rect
            }
        )
    }

    private var rightMargin: Binding<Double> {
        Binding(
            get: { 
                guard let rect = cropRect, pageBounds.width > 0 else { return 0 }
                return (pageBounds.maxX - rect.maxX) / pageBounds.width
            },
            set: { newValue in
                guard var rect = cropRect else { return }
                let marginInPoints = newValue * pageBounds.width
                let newMaxX = pageBounds.maxX - marginInPoints
                rect = CGRect(x: rect.minX, y: rect.minY, width: newMaxX - rect.minX, height: rect.height)
                cropRect = rect
            }
        )
    }

    var body: some View {
        VStack {
            HStack {
                Text("Top").frame(width: 50, alignment: .leading)
                Slider(value: topMargin, in: 0...1.0)
                Text(String(format: "%.2f", topMargin.wrappedValue))
            }
            HStack {
                Text("Bottom").frame(width: 50, alignment: .leading)
                Slider(value: bottomMargin, in: 0...1.0)
                Text(String(format: "%.2f", bottomMargin.wrappedValue))
            }
            HStack {
                Text("Left").frame(width: 50, alignment: .leading)
                Slider(value: leftMargin, in: 0...1.0)
                Text(String(format: "%.2f", leftMargin.wrappedValue))
            }
            HStack {
                Text("Right").frame(width: 50, alignment: .leading)
                Slider(value: rightMargin, in: 0...1.0)
                Text(String(format: "%.2f", rightMargin.wrappedValue))
            }
        }.padding()
    }
}
