
import SwiftUI
import PDFKit

struct NavigationBarView: View {
    let pdfDocument: PDFDocument
    let currentPage: PDFPage?
    let onPrevious: () -> Void
    let onNext: () -> Void

    var body: some View {
        HStack {
            Button("Previous", action: onPrevious)
                .disabled(currentPage == nil || pdfDocument.index(for: currentPage!) == 0)
                .keyboardShortcut(.leftArrow, modifiers: [])
                .keyboardShortcut(.upArrow, modifiers: [])

            Spacer()
            if let page = currentPage {
                let index = pdfDocument.index(for: page)
                Text("Page \(index + 1) of \(pdfDocument.pageCount)")
            }
            Spacer()

            Button("Next", action: onNext)
                .disabled(currentPage == nil || pdfDocument.index(for: currentPage!) == pdfDocument.pageCount - 1)
                .keyboardShortcut(.rightArrow, modifiers: [])
                .keyboardShortcut(.downArrow, modifiers: [])
        }.padding([.leading, .trailing, .bottom])
    }
}
