// The Ren'Py games installed on this Mac (vnpack/library.py), and keeping
// their saves in step with the 3DS (vnpack/savesync.py): once by hand, or
// always, through a login item that runs the converter's sync agent.
import AppKit
import Foundation
import SwiftUI

struct InstalledGame: Identifiable, Equatable {
    var id: String { path }
    let path: String
    let title: String
    let version: String?
    let size: Int64
    let saves: Int
    let place: String
    var cover: String?
}

final class InstalledGames: ObservableObject {
    @Published var games: [InstalledGame] = []
    @Published var searching = false
    private let bridge = Bridge()
    private var searched = false

    func search(again: Bool = false) {
        guard !searching, again || !searched else { return }
        searched = true
        searching = true
        var found: [InstalledGame] = []
        bridge.run(["library"], onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "game":
                guard let path = ev.string("path") else { return }
                found.append(InstalledGame(path: path, title: ev.string("title") ?? path,
                                           version: ev.string("version"), size: ev.int("size") ?? 0,
                                           saves: Int(ev.int("saves") ?? 0), place: ev.string("where") ?? "",
                                           cover: nil))
                self.games = found
            case "cover":
                if let path = ev.string("path"), let i = self.games.firstIndex(where: { $0.path == path }) {
                    self.games[i].cover = ev.string("cover")
                }
            default: break
            }
        }, onExit: { [weak self] _, _ in self?.searching = false })
    }
}

/// The login item: `vn3ds-port --vn3ds-bridge sync-agent`, started by
/// launchd at login and kept running. It waits for vn3ds on the Wi-Fi.
final class SaveSync: ObservableObject {
    static let label = "io.github.arminjamak.vn3ds.sync"
    @Published var enabled: Bool
    @Published var lastSync: Date?
    @Published var running = false
    @Published var message: String?
    private let bridge = Bridge()
    private var timer: Timer?

    static var plistURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/LaunchAgents/\(label).plist")
    }

    static var statusURL: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("vn3ds/sync/status.json")
    }

    init() {
        enabled = FileManager.default.fileExists(atPath: SaveSync.plistURL.path)
        if enabled { install() }   // (the app may have moved: point the agent at this copy)
        readStatus()
        timer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { [weak self] _ in
            self?.readStatus()
        }
    }

    func readStatus() {
        guard let data = try? Data(contentsOf: SaveSync.statusURL),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
        if let t = obj["last_sync"] as? Double { lastSync = Date(timeIntervalSince1970: t) }
    }

    func set(_ on: Bool) {
        if on { install() } else { uninstall() }
        enabled = on
    }

    private func install() {
        guard let (exe, argv, env) = Bridge.command(["sync-agent"]) else {
            message = "The converter is missing from this app."
            return
        }
        let logs = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs")
        var keepEnv: [String: String] = [:]
        for k in ["PYTHONPATH", "PATH", "HOME"] { if let v = env[k] { keepEnv[k] = v } }
        let plist: [String: Any] = [
            "Label": SaveSync.label,
            "ProgramArguments": [exe.path] + argv,
            "EnvironmentVariables": keepEnv,
            "RunAtLoad": true,
            "KeepAlive": true,
            "ProcessType": "Background",
            "StandardOutPath": logs.appendingPathComponent("vn3ds-sync.log").path,
            "StandardErrorPath": logs.appendingPathComponent("vn3ds-sync.log").path,
        ]
        do {
            try FileManager.default.createDirectory(at: SaveSync.plistURL.deletingLastPathComponent(),
                                                    withIntermediateDirectories: true)
            let data = try PropertyListSerialization.data(fromPropertyList: plist, format: .xml, options: 0)
            let old = try? Data(contentsOf: SaveSync.plistURL)
            if old == data, launchctl(["print", "gui/\(getuid())/\(SaveSync.label)"]) { return }
            launchctl(["bootout", "gui/\(getuid())/\(SaveSync.label)"])
            try data.write(to: SaveSync.plistURL)
            launchctl(["bootstrap", "gui/\(getuid())", SaveSync.plistURL.path])
            message = nil
        } catch {
            message = "Couldn't set up the login item: \(error.localizedDescription)"
        }
    }

    private func uninstall() {
        launchctl(["bootout", "gui/\(getuid())/\(SaveSync.label)"])
        try? FileManager.default.removeItem(at: SaveSync.plistURL)
    }

    @discardableResult
    private func launchctl(_ args: [String]) -> Bool {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/bin/launchctl")
        p.arguments = args
        p.standardOutput = FileHandle.nullDevice
        p.standardError = FileHandle.nullDevice
        do { try p.run() } catch { return false }
        p.waitUntilExit()
        return p.terminationStatus == 0
    }

    /// Once, now (vn3ds must be open on the 3DS).
    func syncNow() {
        guard !running else { return }
        running = true
        message = "Looking for vn3ds…"
        bridge.run(["sync"], onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "synced":
                let games = ev.data["games"] as? [String: [String: Any]] ?? [:]
                let parts = games.map { "\($0.key): \($0.value["summary"] as? String ?? "")" }
                self.message = parts.isEmpty ? "Nothing to sync yet." : parts.sorted().joined(separator: "\n")
                self.lastSync = Date()
            case "error": self.message = ev.string("message")
            default: break
            }
        }, onExit: { [weak self] status, err in
            guard let self else { return }
            self.running = false
            if status != 0 && self.message == "Looking for vn3ds…" {
                self.message = err.isEmpty ? "The sync stopped." : String(err.suffix(300))
            }
        })
    }
}

// MARK: views

struct LibraryList: View {
    @ObservedObject var library: InstalledGames
    let send: (InstalledGame) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Ren'Py games on this Mac").font(.headline)
                if library.searching { ProgressView().controlSize(.small) }
                Spacer()
                Button { library.search(again: true) } label: { Image(systemName: "arrow.clockwise") }
                    .buttonStyle(.borderless).help("Look again").disabled(library.searching)
            }
            if library.games.isEmpty {
                Text(library.searching ? "Looking in Applications, Downloads and Steam…"
                     : "None found in Applications, Downloads, Desktop, Documents or Steam. Drop one above.")
                    .font(.callout).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, minHeight: 60, alignment: .center)
            } else {
                ScrollView {
                    LazyVStack(spacing: 6) {
                        ForEach(library.games) { g in GameRow(game: g) { send(g) } }
                    }
                }
            }
        }
        .onAppear { library.search() }
    }
}

struct GameRow: View {
    let game: InstalledGame
    let send: () -> Void
    @State private var hover = false

    var body: some View {
        HStack(spacing: 12) {
            Cover(game: game).frame(width: 72, height: 42).clipShape(RoundedRectangle(cornerRadius: 6))
            VStack(alignment: .leading, spacing: 2) {
                Text(game.title + (game.version.map { " \($0)" } ?? "")).font(.callout.weight(.semibold))
                    .lineLimit(1)
                Text(details).font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            Spacer()
            Button(action: send) { Label("Send to 3DS", systemImage: "arrow.right.circle.fill") }
                .buttonStyle(.borderedProminent).controlSize(.small)
                .help(game.saves > 0 ? "Converts it and sends it over Wi-Fi with its saves" : "Converts it and sends it over Wi-Fi")
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(hover ? 0.12 : 0.06)))
        .onHover { hover = $0 }
    }

    private var details: String {
        var parts = [ByteCountFormatter.string(fromByteCount: game.size, countStyle: .file)]
        parts.append(game.saves == 0 ? "no saves" : "\(game.saves) save\(game.saves == 1 ? "" : "s")")
        parts.append(game.place)
        return parts.joined(separator: " · ")
    }
}

struct Cover: View {
    let game: InstalledGame
    var body: some View {
        if let c = game.cover, let img = NSImage(contentsOfFile: c) {
            Image(nsImage: img).resizable().scaledToFill()
        } else {
            ZStack {
                Color.secondary.opacity(0.12)
                Image(nsImage: NSWorkspace.shared.icon(forFile: game.path)).resizable().scaledToFit()
                    .padding(4)
            }
        }
    }
}

/// "Keep saves in sync" with when it last happened, and "Sync now".
struct SyncControls: View {
    @ObservedObject var sync: SaveSync
    @State private var explain = false

    var body: some View {
        HStack(spacing: 10) {
            Toggle("Keep saves in sync", isOn: Binding(get: { sync.enabled }, set: { sync.set($0) }))
                .toggleStyle(.switch).controlSize(.small)
            Button { explain.toggle() } label: { Image(systemName: "info.circle") }
                .buttonStyle(.borderless)
                .popover(isPresented: $explain) { SyncExplainer(sync: sync).padding(18).frame(width: 340) }
            if let t = sync.lastSync {
                Text("Last synced \(t.formatted(.relative(presentation: .named)))")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

struct SyncExplainer: View {
    @ObservedObject var sync: SaveSync
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Saves on both sides").font(.headline)
            Text("A save you make on the 3DS shows up in the game on this Mac, and the other way round. "
                 + "If both changed, the newer one wins; the other is kept as a backup.")
                .font(.callout)
            Text("When it happens").font(.subheadline.weight(.semibold))
            Text("When vn3ds opens, when you save, when you go back to the library or close vn3ds, and "
                 + "every 20 seconds while vn3ds is open. The 3DS can't run vn3ds while it's closed, so "
                 + "saves made then wait on its SD card and come across the next time vn3ds is open, even "
                 + "for a moment. With this switch on, a small helper starts with your Mac to catch it.")
                .font(.callout).foregroundStyle(.secondary)
            HStack {
                Button(sync.running ? "Syncing…" : "Sync now") { sync.syncNow() }.disabled(sync.running)
                Spacer()
            }
            if let m = sync.message {
                Text(m).font(.caption.monospaced()).foregroundStyle(.secondary).textSelection(.enabled)
            }
        }
    }
}
