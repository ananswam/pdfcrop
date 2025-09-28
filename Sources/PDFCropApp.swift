
import SwiftUI

// An App Delegate to handle app lifecycle events
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        // This ensures the app quits when the last window is closed.
        return true
    }
}

@main
struct PDFCropApp: App {
    // Inject the App Delegate into the SwiftUI App lifecycle
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
