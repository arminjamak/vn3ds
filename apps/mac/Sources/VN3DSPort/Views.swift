// The window: one screen per stage of the trip.
import AppKit
import CoreImage.CIFilterBuiltins
import SwiftUI
import UniformTypeIdentifiers

let accent = Color(red: 0.93, green: 0.33, blue: 0.42)

struct ContentView: View {
    @StateObject var trip = Trip()
    @StateObject var library = InstalledGames()
    @StateObject var sync = SaveSync()

    var body: some View {
        VStack(spacing: 0) {
            Header(stage: trip.stage)
            Divider()
            Group {
                switch trip.stage {
                case .drop: DropScreen(trip: trip, library: library, sync: sync)
                case .route: RouteScreen(trip: trip)
                case .setup: SetupScreen(trip: trip)
                case .sending: SendingScreen(trip: trip)
                case .done: DoneScreen(trip: trip, sync: sync)
                case .failed(let message): FailedScreen(trip: trip, message: message)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding(28)
        }
        .frame(width: 680, height: 520)
        .tint(accent)
        .onAppear {   // tests: VN3DS_APP_INPUT=game [VN3DS_APP_ROUTE=wifi|sd] skip the clicks
            let env = ProcessInfo.processInfo.environment
            if let game = env["VN3DS_APP_INPUT"] {
                trip.drop([URL(fileURLWithPath: game)])
                if let r = env["VN3DS_APP_ROUTE"].flatMap(Route.init(rawValue:)) { trip.choose(r) }
            }
        }
    }
}

struct Header: View {
    let stage: Stage
    private var index: Int {
        switch stage {
        case .drop: return 0
        case .route: return 1
        case .setup: return 2
        case .sending, .failed: return 3
        case .done: return 4
        }
    }

    var body: some View {
        HStack(spacing: 18) {
            Text("vn3ds").font(.system(size: 20, weight: .bold, design: .rounded))
            Spacer()
            ForEach(Array(["Game", "Route", "3DS", "Send"].enumerated()), id: \.offset) { i, name in
                HStack(spacing: 6) {
                    Circle().fill(i < index ? accent : i == index ? accent.opacity(0.5) : .gray.opacity(0.3))
                        .frame(width: 8, height: 8)
                    Text(name).font(.callout).foregroundStyle(i <= index ? .primary : .secondary)
                }
            }
        }
        .padding(.horizontal, 24).padding(.vertical, 14)
    }
}

// MARK: 1. the game

struct DropScreen: View {
    @ObservedObject var trip: Trip
    @ObservedObject var library: InstalledGames
    @ObservedObject var sync: SaveSync
    @State private var hovering = false

    var body: some View {
        VStack(spacing: 16) {
            ZStack {
                RoundedRectangle(cornerRadius: 18)
                    .strokeBorder(style: StrokeStyle(lineWidth: 2.5, dash: [9, 7]))
                    .foregroundStyle(hovering ? accent : .secondary.opacity(0.5))
                    .background(RoundedRectangle(cornerRadius: 18)
                        .fill(hovering ? accent.opacity(0.08) : Color.secondary.opacity(0.05)))
                HStack(spacing: 18) {
                    Image(systemName: "book.pages").font(.system(size: 40, weight: .light))
                        .foregroundStyle(hovering ? accent : .secondary)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Drop your visual novel here").font(.title3.weight(.semibold))
                        Text("Any Ren'Py game: its folder, a .zip, an Android .apk or a Mac .app")
                            .font(.callout).foregroundStyle(.secondary)
                    }
                    Spacer(minLength: 0)
                    Button("Choose…") { choose() }
                }
                .padding(.horizontal, 22)
            }
            .frame(height: 104)
            .onDrop(of: [.fileURL], isTargeted: $hovering) { providers in
                load(providers)
                return true
            }
            LibraryList(library: library) { game in
                trip.drop([URL(fileURLWithPath: game.path)])
                trip.choose(.wifi)   // one step: convert, find the 3DS, send (with the saves)
            }
            HStack(spacing: 16) {
                SyncControls(sync: sync).font(.footnote)
                Spacer()
                ExportAppsButton().font(.footnote)
            }
            Text("Only port games you have the rights to.").font(.footnote).foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func load(_ providers: [NSItemProvider]) {
        var urls: [URL] = []
        let group = DispatchGroup()
        for p in providers {
            group.enter()
            _ = p.loadObject(ofClass: URL.self) { url, _ in
                if let url { DispatchQueue.main.async { urls.append(url) } }
                group.leave()
            }
        }
        group.notify(queue: .main) { trip.drop(urls) }
    }

    private func choose() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = true
        panel.allowsMultipleSelection = true
        panel.message = "Choose the visual novel (its folder, .zip, .apk or .app)"
        if panel.runModal() == .OK { trip.drop(panel.urls) }
    }
}

// MARK: 2. the way there

struct RouteScreen: View {
    @ObservedObject var trip: Trip

    var body: some View {
        VStack(spacing: 22) {
            Text("How should \(trip.gameName) get to your 3DS?").font(.title2.weight(.semibold))
            HStack(spacing: 18) {
                RouteCard(icon: "wifi", title: "Over Wi-Fi", tag: "Very easy",
                          lines: ["Nothing to unplug", "Full picture and sound",
                                  "About 1.5 MB a second"]) { trip.choose(.wifi) }
                RouteCard(icon: "sdcard", title: "With the SD card", tag: "Fast",
                          lines: ["Full picture and sound", "Copies in seconds",
                                  "Take the card out of the 3DS"]) { trip.choose(.sd) }
            }
            VStack(spacing: 10) {
                Toggle(isOn: $trip.in3D) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Make it 3D").font(.callout.weight(.medium))
                        Text("Movies and scenes in stereoscopic 3D. Slower; downloads a 99 MB depth model once.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                .toggleStyle(.checkbox)
                .frame(width: 558, alignment: .leading)
                if Bridge.snapshotDir != nil {
                    Toggle(isOn: $trip.withSnapshot) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Also send Snapshot").font(.callout.weight(.medium))
                            Text("A new visual novel about the exploration of existence itself, made for vn3ds")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .toggleStyle(.checkbox)
                    .frame(width: 558, alignment: .leading)
                }
            }
            Button("Back") { trip.reset() }.buttonStyle(.link)
        }
    }
}

struct RouteCard: View {
    let icon: String, title: String, tag: String, lines: [String]
    let action: () -> Void
    @State private var hover = false

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Image(systemName: icon).font(.system(size: 30)).foregroundStyle(accent)
                        .frame(height: 36)
                    Spacer()
                    Text(tag).font(.caption.weight(.semibold)).padding(.horizontal, 8).padding(.vertical, 3)
                        .background(Capsule().fill(accent.opacity(0.15))).foregroundStyle(accent)
                }
                Text(title).font(.title3.weight(.semibold))
                ForEach(lines, id: \.self) { l in
                    Label(l, systemImage: "checkmark").font(.callout).foregroundStyle(.secondary)
                }
            }
            .padding(20)
            .frame(width: 270, height: 200, alignment: .topLeading)
            .background(RoundedRectangle(cornerRadius: 18).fill(Color.secondary.opacity(hover ? 0.14 : 0.07)))
            .overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(hover ? accent : .clear, lineWidth: 2))
        }
        .buttonStyle(.plain)
        .onHover { hover = $0 }
    }
}

// MARK: 3. vn3ds on the 3DS

struct SetupScreen: View {
    @ObservedObject var trip: Trip

    var body: some View {
        VStack(spacing: 18) {
            if trip.route == .sd {
                SDSetup(trip: trip)
            } else if trip.readyIP != nil {
                Ready(text: "vn3ds is ready on your 3DS")
            } else if trip.showInstall {
                Text("First, put vn3ds on your 3DS").font(.title2.weight(.semibold))
                HStack(alignment: .center, spacing: 14) {
                    InstallCard(icon: "house", title: "Homebrew Launcher",
                                steps: ["Open the Homebrew Launcher", "Press Y"],
                                status: trip.netloaderSeen ? trip.engine.detail : "Waiting for the launcher…",
                                fraction: trip.netloaderSeen ? trip.engine.fraction : nil) {
                        Text("Y").font(.system(size: 56, weight: .bold, design: .rounded))
                            .foregroundStyle(.white).frame(width: 104, height: 104)
                            .background(Circle().fill(Color(red: 0.36, green: 0.68, blue: 0.36)))
                            .shadow(color: .black.opacity(0.18), radius: 4, y: 3).padding(.top, 34)
                    }
                    Text("or").font(.headline).foregroundStyle(.secondary)
                    InstallCard(icon: "qrcode", title: "FBI",
                                steps: ["Open FBI, choose Remote Install", "Scan QR Code, then this code",
                                        "Open vn3ds from the HOME Menu"],
                                status: trip.ciaFetched ? "FBI is installing vn3ds…" : (trip.ciaURL == nil ? "vn3ds.cia isn't in this app" : "Waiting for FBI…"),
                                fraction: nil) {
                        if let url = trip.ciaURL { QRCode(text: url).frame(width: 118, height: 118) }
                    }
                }
            } else {
                Text("Open vn3ds on your 3DS").font(.title2.weight(.semibold))
                Text("It listens for games while it's open: \(trip.gameName) goes straight into its library.")
                    .foregroundStyle(.secondary).multilineTextAlignment(.center)
                ProgressView().controlSize(.small)
                Button("vn3ds isn't on this 3DS") { trip.showInstall = true }.buttonStyle(.link)
            }
            Spacer(minLength: 0)
            ConvertStatus(trip: trip)
        }
    }
}

struct SDSetup: View {
    @ObservedObject var trip: Trip
    var body: some View {
        if let sd = trip.readySD {
            Ready(text: "vn3ds is on the SD card (\(URL(fileURLWithPath: sd).lastPathComponent))")
        } else {
            VStack(spacing: 14) {
                Image(systemName: "sdcard").font(.system(size: 50, weight: .light)).foregroundStyle(accent)
                Text("Put the 3DS's SD card into this Mac").font(.title2.weight(.semibold))
                Text("Turn the 3DS off, take out the card and put it in this Mac's card reader. "
                     + (trip.installedBefore ? "" : "vn3ds is copied onto it first, then your game."))
                    .foregroundStyle(.secondary).multilineTextAlignment(.center).frame(maxWidth: 440)
                ProgressView().controlSize(.small)
            }
        }
    }
}

struct InstallCard<Extra: View>: View {
    let icon: String, title: String, steps: [String], status: String
    let fraction: Double?
    @ViewBuilder let extra: () -> Extra

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(title, systemImage: icon).font(.title3.weight(.semibold))
            ForEach(Array(steps.enumerated()), id: \.offset) { i, s in
                HStack(alignment: .top, spacing: 8) {
                    Text("\(i + 1)").font(.caption.weight(.bold)).frame(width: 18, height: 18)
                        .background(Circle().fill(accent.opacity(0.18)))
                    Text(s).font(.callout)
                }
            }
            HStack { Spacer(); extra(); Spacer() }
            Spacer(minLength: 0)
            if let f = fraction { ProgressView(value: f) }
            Text(status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
        }
        .padding(18)
        .frame(width: 270, height: 290, alignment: .topLeading)
        .background(RoundedRectangle(cornerRadius: 18).fill(Color.secondary.opacity(0.07)))
    }
}

struct Ready: View {
    let text: String
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: "checkmark.circle.fill").font(.system(size: 46)).foregroundStyle(.green)
            Text(text).font(.title3.weight(.semibold))
            Text("Your game is sent as soon as it's converted.").foregroundStyle(.secondary)
        }
        .padding(.top, 30)
    }
}

struct ConvertStatus: View {
    @ObservedObject var trip: Trip
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(trip.convertedDir == nil ? "Converting \(trip.gameName)" : "\(trip.gameName) is converted")
                    .font(.callout.weight(.medium))
                Spacer()
                Text([trip.converting.label, trip.converting.detail].filter { !$0.isEmpty }.joined(separator: " · "))
                    .font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            if let f = trip.converting.fraction { ProgressView(value: f) } else { ProgressView().progressViewStyle(.linear) }
        }
        .padding(14)
        .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.07)))
    }
}

struct QRCode: View {
    let text: String
    var body: some View {
        if let img = QRCode.image(text) {
            Image(nsImage: img).interpolation(.none).resizable().scaledToFit()
                .padding(6).background(Color.white).clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    static func image(_ text: String) -> NSImage? {
        let f = CIFilter.qrCodeGenerator()
        f.message = Data(text.utf8)
        f.correctionLevel = "M"
        guard let out = f.outputImage,
              let cg = CIContext().createCGImage(out, from: out.extent) else { return nil }
        return NSImage(cgImage: cg, size: NSSize(width: out.extent.width, height: out.extent.height))
    }
}

// MARK: 4. sending and after

struct SendingScreen: View {
    @ObservedObject var trip: Trip
    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: trip.route == .sd ? "sdcard" : "wifi").font(.system(size: 46, weight: .light))
                .foregroundStyle(accent)
            Text(trip.route == .sd ? "Copying \(trip.gameName) to the SD card" : "Sending \(trip.gameName) to your 3DS")
                .font(.title2.weight(.semibold))
            if let f = trip.sending.fraction { ProgressView(value: f).frame(width: 380) }
            else { ProgressView().progressViewStyle(.linear).frame(width: 380) }
            Text(trip.sending.detail).font(.callout).foregroundStyle(.secondary)
            if !trip.savesDetail.isEmpty {
                Label(trip.savesDetail, systemImage: "bookmark").font(.callout).foregroundStyle(.secondary)
            }
            if trip.route == .wifi {
                Text("You can keep playing on the 3DS meanwhile.").font(.footnote).foregroundStyle(.secondary)
            }
        }
    }
}

struct DoneScreen: View {
    @ObservedObject var trip: Trip
    @ObservedObject var sync: SaveSync
    @State private var showKept = false
    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: "checkmark.circle.fill").font(.system(size: 56)).foregroundStyle(.green)
            Text(trip.sendsSnapshot ? "\(trip.gameName) and Snapshot are on your 3DS"
                                    : "\(trip.gameName) is on your 3DS").font(.title.weight(.semibold))
            Text(trip.route == .sd
                 ? "Eject the SD card, put it back in the 3DS and open vn3ds from the Homebrew Launcher."
                 : "It's in vn3ds's library now. Enjoy!")
                .foregroundStyle(.secondary).multilineTextAlignment(.center).frame(maxWidth: 420)
            if let n = trip.note3D {
                Label(n, systemImage: "view.3d").font(.caption).foregroundStyle(.secondary)
                    .lineLimit(2).frame(maxWidth: 420)
            }
            if let saves = trip.saves {
                VStack(spacing: 4) {
                    Label(saves.sent == 0 ? "No saves went along" :
                            "\(saves.sent) save\(saves.sent == 1 ? "" : "s") went along",
                          systemImage: "bookmark.fill").font(.callout.weight(.medium))
                    if !saves.keptBack.isEmpty {
                        Button("\(saves.keptBack.count) couldn't be carried over: why?") { showKept.toggle() }
                            .buttonStyle(.link).font(.caption)
                            .popover(isPresented: $showKept) {
                                VStack(alignment: .leading, spacing: 6) {
                                    ForEach(Array(saves.keptBack.enumerated()), id: \.offset) { _, k in
                                        Text("\(k.0): \(k.1)").font(.caption).fixedSize(horizontal: false, vertical: true)
                                    }
                                    Text("They stay where they are, untouched.").font(.caption).foregroundStyle(.secondary)
                                }
                                .padding(14).frame(width: 360)
                            }
                    }
                }
            }
            SyncControls(sync: sync).font(.callout)
            if trip.route == .sd, let sd = trip.readySD {
                Button("Eject the SD card") {
                    try? NSWorkspace.shared.unmountAndEjectDevice(at: URL(fileURLWithPath: sd))
                }
            }
            ExportAppsButton()
            Button("Port another game") { trip.reset() }
                .buttonStyle(.borderedProminent).controlSize(.large).padding(.top, 8)
        }
    }
}

struct FailedScreen: View {
    @ObservedObject var trip: Trip
    let message: String
    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 44)).foregroundStyle(.orange)
            Text("That didn't work").font(.title2.weight(.semibold))
            ScrollView { Text(message).font(.callout.monospaced()).textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading) }
                .frame(maxHeight: 180).padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.08)))
            Button("Start over") { trip.reset() }.buttonStyle(.borderedProminent)
        }
    }
}

// MARK: apps for an emulator

/// Writes every novel converted here as <id>.3dsx (with vn3ds.3dsx) into a
/// folder: an emulator's games folder (Azahar, Citra, Lime3DS; on an AYN
/// Thor that's Roms/3ds) or a card's 3ds folder.
final class AppExport: ObservableObject {
    @Published var running = false
    @Published var progress = Progress()
    @Published var result: String?
    @Published var dest: URL?
    private let bridge = Bridge()

    func choose() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.canCreateDirectories = true
        panel.prompt = "Export here"
        panel.message = "Choose where the apps go: an emulator's games folder (on an AYN Thor: " +
            "Roms/3ds), or a folder to copy over later"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        start(url)
    }

    func start(_ url: URL) {
        dest = url
        running = true
        result = nil
        progress = Progress(label: "Apps", detail: "Starting…")
        bridge.run(["export-apps", "--dest", url.path, Trip.outputFolder], onEvent: { [weak self] ev in
            guard let self else { return }
            switch ev.name {
            case "step":
                var p = Progress(label: ev.string("label") ?? "", detail: ev.string("detail") ?? "")
                if let d = ev.int("done"), let t = ev.int("total"), t > 0 { p.fraction = Double(d) / Double(t) }
                self.progress = p
            case "exported":
                let n = (ev.data["apps"] as? [Any])?.count ?? 0
                self.result = "\(n) app\(n == 1 ? "" : "s") and vn3ds.3dsx are in \(url.lastPathComponent)."
            case "error": self.result = ev.string("message") ?? "The export stopped."
            default: break
            }
        }, onExit: { [weak self] status, err in
            guard let self else { return }
            self.running = false
            if status != 0 && self.result == nil {
                self.result = err.isEmpty ? "The export stopped." : String(err.suffix(400))
            }
        })
    }
}

struct ExportAppsButton: View {
    @StateObject private var export = AppExport()

    var body: some View {
        Button("Export apps for an emulator…") { export.choose() }
            .buttonStyle(.link)
            .sheet(isPresented: Binding(get: { export.running || export.result != nil },
                                        set: { if !$0 { export.result = nil } })) {
                VStack(spacing: 14) {
                    Image(systemName: "square.stack.3d.up").font(.system(size: 40)).foregroundStyle(accent)
                    Text("Apps for an emulator").font(.title3.weight(.semibold))
                    if export.running {
                        if let f = export.progress.fraction { ProgressView(value: f).frame(width: 320) }
                        else { ProgressView().progressViewStyle(.linear).frame(width: 320) }
                        Text(export.progress.detail).font(.callout).foregroundStyle(.secondary)
                    } else if let r = export.result {
                        Text(r).multilineTextAlignment(.center).frame(maxWidth: 360)
                        Text("Each novel is its own app: add the folder to the emulator's games " +
                             "list, or copy the files beside vn3ds.3dsx (sdmc:/3ds/ on a 3DS).")
                            .font(.footnote).foregroundStyle(.secondary)
                            .multilineTextAlignment(.center).frame(maxWidth: 360)
                        HStack {
                            if let d = export.dest {
                                Button("Show in Finder") { NSWorkspace.shared.open(d) }
                            }
                            Button("Done") { export.result = nil }.buttonStyle(.borderedProminent)
                        }
                    }
                }
                .padding(28)
                .frame(width: 440)
            }
    }
}
