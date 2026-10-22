// One trip of a visual novel to the 3DS: drop it in, pick the way there,
// get vn3ds onto the 3DS the first time, convert, send. "Port another"
// starts the next one.
import Foundation
import SwiftUI

enum Route: String { case wifi, sd }

enum Stage: Equatable { case drop, route, setup, sending, done, failed(String) }

struct Progress: Equatable {
    var label = ""
    var detail = ""
    var fraction: Double? = nil
}

final class Trip: ObservableObject {
    @Published var stage: Stage = .drop
    @Published var inputs: [URL] = []
    @Published var route: Route = .wifi
    /// Send Snapshot along (on by default the first time).
    @Published var withSnapshot: Bool
    /// Movies and scenes in stereoscopic 3D (port.py's --3d; remembered, off at first).
    @Published var in3D: Bool {
        didSet { UserDefaults.standard.set(in3D, forKey: "vn3dsIn3D") }
    }

    // converting (starts as soon as the route is picked)
    @Published var converting = Progress()
    @Published var convertedDir: String?
    @Published var title: String?
    /// Why the game stayed 2D although 3D was asked for (no depth model or runtime).
    @Published var note3D: String?

    // the 3DS: installing vn3ds the first time, then finding it
    @Published var ciaURL: String?
    @Published var ciaFetched = false
    @Published var netloaderSeen = false
    @Published var engine = Progress()
    @Published var readyIP: String?
    @Published var readySD: String?
    @Published var showInstall: Bool

    // sending
    @Published var sending = Progress()
    /// The Ren'Py saves that went along: (sent, [(slot, why not)]).
    @Published var saves: (sent: Int, keptBack: [(String, String)])?
    @Published var savesDetail = ""

    /// vn3ds has reached a 3DS from this Mac before: skip the install step.
    var installedBefore: Bool {
        get { UserDefaults.standard.bool(forKey: "vn3dsInstalled") }
        set { UserDefaults.standard.set(newValue, forKey: "vn3dsInstalled") }
    }

    private let convertBridge = Bridge(), setupBridge = Bridge(), sendBridge = Bridge()

    init() {
        showInstall = !UserDefaults.standard.bool(forKey: "vn3dsInstalled")
        withSnapshot = !UserDefaults.standard.bool(forKey: "vn3dsInstalled") && Bridge.snapshotDir != nil
        in3D = UserDefaults.standard.bool(forKey: "vn3dsIn3D")
    }

    /// Snapshot is going too (and isn't the game itself).
    var sendsSnapshot: Bool {
        guard withSnapshot, let snap = Bridge.snapshotDir else { return false }
        return convertedDir.map { URL(fileURLWithPath: $0).lastPathComponent }
            != URL(fileURLWithPath: snap).lastPathComponent
    }

    var gameName: String {
        title ?? inputs.first.map { $0.deletingPathExtension().lastPathComponent } ?? "Your game"
    }

    static var outputFolder: String {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        return base.appendingPathComponent("vn3ds/games").path
    }

    // MARK: steps

    func drop(_ urls: [URL]) {
        guard !urls.isEmpty else { return }
        inputs = urls
        stage = .route
    }

    func choose(_ r: Route) {
        route = r
        stage = .setup
        startConverting()
        startSetup()
    }

    func reset() {
        for b in [convertBridge, setupBridge, sendBridge] { b.stop() }
        inputs = []
        converting = Progress(); convertedDir = nil; title = nil; note3D = nil
        ciaURL = nil; ciaFetched = false; netloaderSeen = false; engine = Progress()
        readyIP = nil; readySD = nil; sending = Progress(); saves = nil; savesDetail = ""
        showInstall = !installedBefore
        withSnapshot = false
        stage = .drop
    }

    private func fail(_ message: String) {
        for b in [convertBridge, setupBridge, sendBridge] { b.stop() }
        stage = .failed(message)
    }

    private func progress(_ ev: BridgeEvent) -> Progress {
        var p = Progress(label: ev.string("label") ?? "", detail: ev.string("detail") ?? "")
        if let d = ev.int("done"), let t = ev.int("total"), t > 0 { p.fraction = Double(d) / Double(t) }
        if ev.string("state") == "done" { p.fraction = 1 }
        return p
    }

    private func startConverting() {
        converting = Progress(label: "Getting ready", detail: "")
        // the same build for both ways: the smallest files with no visible loss
        // (3D: the first time, the "depth" step shows the model's download)
        convertBridge.run(["port", "--quality", "balanced"] + (in3D ? ["--3d"] : [])
                          + ["-o", Trip.outputFolder] + inputs.map { $0.path }, onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "step" where ev.string("state") != "skip":
                self.converting = self.progress(ev)
                if ev.string("id") == "depth", ev.string("state") == "done",
                   let d = ev.string("detail"), d.hasPrefix("stays 2D: ") {
                    self.note3D = "It's in 2D: " + d.dropFirst("stays 2D: ".count)
                }
            case "converted":
                self.convertedDir = ev.string("out_dir")
                self.title = ev.string("title") ?? self.title
                self.converting = Progress(label: "Converted", detail: "", fraction: 1)
                self.sendIfReady()
            case "error": self.fail(ev.string("message") ?? "The conversion stopped.")
            default: break
            }
        }, onExit: { [weak self] status, err in
            guard let self, status != 0, self.convertedDir == nil, case .setup = self.stage else { return }
            self.fail(err.isEmpty ? "The conversion stopped." : String(err.suffix(600)))
        })
    }

    private func startSetup() {
        var args = ["setup", "--route", route.rawValue]
        if let cia = Bridge.ciaPath { args += ["--cia", cia] }
        setupBridge.run(args, onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "cia": self.ciaURL = ev.string("url")
            case "cia_fetched": self.ciaFetched = true
            case "netloader": self.netloaderSeen = true
            case "step": self.engine = self.progress(ev)
            case "ready":
                self.readyIP = ev.string("ip")
                self.readySD = ev.string("sd")
                self.sendIfReady()
            case "error": self.fail(ev.string("message") ?? "Couldn't reach the 3DS.")
            default: break
            }
        }, onExit: { _, _ in })
    }

    private func sendIfReady() {
        guard stage == .setup, let dir = convertedDir, readyIP != nil || readySD != nil else { return }
        stage = .sending
        sending = Progress(label: "Sending", detail: "")
        let to = readyIP.map { ["--wifi", $0] } ?? ["--sd", readySD!]
        let games = [dir] + (sendsSnapshot ? [Bridge.snapshotDir!] : [])
        sendBridge.run(["send"] + to + games, onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "step" where ev.string("id") == "game" || ev.string("id") == "engine":
                self.sending = self.progress(ev)
            case "step" where ev.string("id") == "saves":
                self.savesDetail = ev.string("detail") ?? ""
            case "saves":
                let kept = (ev.data["kept_back"] as? [[String]] ?? []).compactMap {
                    $0.count == 2 ? ($0[0], $0[1]) : nil }
                self.saves = (Int(ev.int("sent") ?? 0), kept)
            case "done":
                self.installedBefore = true
                self.stage = .done
            case "error": self.fail(ev.string("message") ?? "The transfer stopped.")
            default: break
            }
        }, onExit: { [weak self] status, err in
            guard let self, status != 0, self.stage == .sending else { return }
            self.fail(err.isEmpty ? "The transfer stopped." : String(err.suffix(600)))
        })
    }
}
