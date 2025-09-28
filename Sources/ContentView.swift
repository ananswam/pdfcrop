import SwiftUI
import PDFKit

struct ContentView: View {
    // MARK: - State Properties
    
    // Document State
    @State private var pdfDocument: PDFDocument?
    @State private var currentPage: PDFPage?
    @State private var cropRect: CGRect?
    @State private var sourceURL: URL?

    // View State
    @State private var previewImage: NSImage?
    @State private var showFileImporter = false
    @State private var isExporting = false
    @State private var documentToExport: PDFFile?
    
    @State private var previewSize: CGSize = .zero

    // Drag Gesture State
    @State private var isDragging = false

    // MARK: - Body
    
    var body: some View {
        VStack {
            Text("PDF Cropper")
                .font(.largeTitle)
                .padding()

            if let pdfDocument = pdfDocument, let page = currentPage {
                HStack(alignment: .top) {
                    VStack {
                        if let previewImage = previewImage {
                            Image(nsImage: previewImage)
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .background(GeometryReader { geo in
                                    Color.clear.onAppear { self.previewSize = geo.size }
                                })
                                .gesture(
                                    DragGesture(minimumDistance: 0)
                                        .onChanged { value in
                                            if !self.isDragging { self.isDragging = true }
                                            updateCropRectFromDrag(start: value.startLocation, current: value.location)
                                        }
                                        .onEnded { _ in self.isDragging = false }
                                )
                        } else {
                            ProgressView().onAppear(perform: updatePreviewImage)
                        }

                        NavigationBarView(pdfDocument: pdfDocument, currentPage: currentPage, onPrevious: goToPreviousPage, onNext: goToNextPage)
                    }

                    VStack {
                        CropControlsView(cropRect: $cropRect, pageBounds: page.bounds(for: .mediaBox))
                        Spacer()
                        Button("Crop & Save", action: saveCroppedPDF)
                        .padding()
                    }
                    .frame(width: 300)
                }

            } else {
                VStack {
                    Spacer()
                    Button("Browse for PDF") { showFileImporter = true }
                    Spacer()
                }
            }
        }
        .frame(minWidth: 1000, minHeight: 600)
        .padding()
        .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.pdf]) { handleFileImport(result: $0) }
        .fileExporter(isPresented: $isExporting, document: documentToExport, contentType: .pdf, defaultFilename: defaultSaveName) { handleFileExport(result: $0) }
        .onChange(of: currentPage) { updatePreviewImage() }
        .onChange(of: cropRect) {
            if !isDragging { updatePreviewImage() }
        }
    }
    
    // MARK: - Helper Functions

    private var defaultSaveName: String {
        sourceURL?.deletingPathExtension().lastPathComponent.appending("-cropped.pdf") ?? "cropped.pdf"
    }

    private func goToPreviousPage() {
        guard let doc = pdfDocument, let page = currentPage else { return }
        let index = doc.index(for: page)
        if index > 0 {
            currentPage = doc.page(at: index - 1)
        }
    }

    private func goToNextPage() {
        guard let doc = pdfDocument, let page = currentPage else { return }
        let index = doc.index(for: page)
        if index < doc.pageCount - 1 {
            currentPage = doc.page(at: index + 1)
        }
    }

    private func updatePreviewImage() {
        guard let page = currentPage else { return }
        self.previewImage = PDFPageRenderer.render(page: page, with: cropRect)
    }

    private func updateCropRectFromDrag(start: CGPoint, current: CGPoint) {
        guard let page = currentPage, previewSize.width > 0, previewSize.height > 0 else { return }
        let pageBounds = page.bounds(for: .mediaBox)

        let startX = (start.x / previewSize.width) * pageBounds.width
        let startY = (1 - (start.y / previewSize.height)) * pageBounds.height
        let currentX = (current.x / previewSize.width) * pageBounds.width
        let currentY = (1 - (current.y / previewSize.height)) * pageBounds.height

        let newRect = CGRect(x: min(startX, currentX),
                             y: min(startY, currentY),
                             width: abs(startX - currentX),
                             height: abs(startY - currentY))
        
        self.cropRect = newRect
        self.previewImage = PDFPageRenderer.render(page: page, with: newRect)
    }
    
    private func handleFileImport(result: Result<URL, Error>) {
        switch result {
        case .success(let url):
            if url.startAccessingSecurityScopedResource() {
                defer { url.stopAccessingSecurityScopedResource() }
                self.sourceURL = url
                let doc = PDFDocument(url: url)
                self.pdfDocument = doc
                self.currentPage = doc?.page(at: 0)
                self.cropRect = self.currentPage?.bounds(for: .mediaBox)
            }
        case .failure(let error):
            print("Error importing file: \(error.localizedDescription)")
        }
    }

    private func saveCroppedPDF() {
        guard let doc = pdfDocument?.copy() as? PDFDocument,
              let crop = cropRect else { return }

        for i in 0..<doc.pageCount {
            if let page = doc.page(at: i) {
                page.setBounds(crop, for: .cropBox)
            }
        }

        if let data = doc.dataRepresentation() {
            documentToExport = PDFFile(data: data)
            isExporting = true
        }
    }

    private func handleFileExport(result: Result<URL, Error>) {
        switch result {
        case .success(let url):
            print("Saved to \(url)")
        case .failure(let error):
            print("Save failed: \(error.localizedDescription)")
        }
    }
}