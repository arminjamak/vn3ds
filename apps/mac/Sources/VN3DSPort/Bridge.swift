// Runs the converter's app commands (tools/vnpack/appbridge.py) and turns
// their JSON lines into events on the main thread.
import Foundation

struct BridgeEvent {
    let name: String
    let data: [String: Any]

    func string(_ key: String) -> String? { data[key] as? String }
    func int(_ key: String) -> Int64? { (data[key] as? NSNumber)?.int64Value }
    func strings(_ key: String) -> [String] { data[key] as? [String] ?? [] }
}

final class Bridge {
    private var process: Process?
    private var buffer = Data()
    private var errors = ""

    /// How to run the converter: the frozen one inside the app, else the
    /// repository's Python (VN3DS_REPO, or the folder the app was built in).
    static func command(_ args: [String]) -> (URL, [String], [String: String])? {
        var env = ProcessInfo.processInfo.environment
        if let res = Bundle.main.resourceURL {
            let frozen = res.appendingPathComponent("port/vn3ds-port")
            if FileManager.default.isExecutableFile(atPath: frozen.path) {
                return (frozen, ["--vn3ds-bridge"] + args, env)
            }
        }
        let repo = env["VN3DS_REPO"] ?? (Bundle.main.object(forInfoDictionaryKey: "VN3DSRepo") as? String)
        guard let repo, FileManager.default.fileExists(atPath: repo + "/tools/vnpack/appbridge.py") else {
            return nil
        }
        env["PYTHONPATH"] = repo + "/tools"
        // a Finder-launched app has a bare PATH: find Homebrew's ffmpeg and python
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + (env["PATH"] ?? "/usr/bin:/bin")
        let venv = repo + "/.venv/bin/python3"
        let python = FileManager.default.isExecutableFile(atPath: venv) ? venv : "/usr/bin/env"
        let pre = python == venv ? [] : ["python3"]
        return (URL(fileURLWithPath: python), pre + ["-u", "-m", "vnpack.appbridge"] + args, env)
    }

    /// Snapshot, ported and ready to send (the route step's checkbox).
    static var snapshotDir: String? {
        if let p = Bundle.main.resourceURL?.appendingPathComponent("snapshot").path,
           FileManager.default.fileExists(atPath: p + "/game.bin") { return p }
        if let repo = ProcessInfo.processInfo.environment["VN3DS_REPO"]
            ?? (Bundle.main.object(forInfoDictionaryKey: "VN3DSRepo") as? String) {
            let p = repo + "/build/snapshot"
            if FileManager.default.fileExists(atPath: p + "/game.bin") { return p }
        }
        return nil
    }

    /// The bundled vn3ds.cia (for FBI), if there is one.
    static var ciaPath: String? {
        if let p = Bundle.main.resourceURL?.appendingPathComponent("vn3ds.cia").path,
           FileManager.default.fileExists(atPath: p) { return p }
        if let repo = ProcessInfo.processInfo.environment["VN3DS_REPO"]
            ?? (Bundle.main.object(forInfoDictionaryKey: "VN3DSRepo") as? String) {
            let p = repo + "/engine/vn3ds.cia"
            if FileManager.default.fileExists(atPath: p) { return p }
        }
        return nil
    }

    func run(_ args: [String], onEvent: @escaping (BridgeEvent) -> Void,
             onExit: @escaping (Int32, String) -> Void) {
        guard let (exe, argv, env) = Bridge.command(args) else {
            onExit(1, "The converter is missing from this app.")
            return
        }
        let p = Process()
        p.executableURL = exe
        p.arguments = argv
        p.environment = env
        let out = Pipe(), err = Pipe()
        p.standardOutput = out
        p.standardError = err
        let lines = DispatchQueue(label: "vn3ds.bridge")   // keeps the events in order
        let take: (Data) -> Void = { [weak self] chunk in
            guard let self, !chunk.isEmpty else { return }
            self.buffer.append(chunk)
            while let nl = self.buffer.firstIndex(of: 10) {
                let line = self.buffer.subdata(in: self.buffer.startIndex..<nl)
                self.buffer.removeSubrange(self.buffer.startIndex...nl)
                guard let obj = try? JSONSerialization.jsonObject(with: line) as? [String: Any],
                      let name = obj["event"] as? String else { continue }
                let ev = BridgeEvent(name: name, data: obj)
                DispatchQueue.main.async { onEvent(ev) }
            }
        }
        out.fileHandleForReading.readabilityHandler = { h in
            let chunk = h.availableData
            lines.sync { take(chunk) }
        }
        err.fileHandleForReading.readabilityHandler = { [weak self] h in
            if let s = String(data: h.availableData, encoding: .utf8) {
                self?.errors = String(((self?.errors ?? "") + s).suffix(4000))
            }
        }
        p.terminationHandler = { [weak self] proc in
            out.fileHandleForReading.readabilityHandler = nil
            err.fileHandleForReading.readabilityHandler = nil
            let rest = out.fileHandleForReading.readDataToEndOfFile()
            lines.sync { take(rest + Data([10])) }   // the last lines come before the exit
            let tail = self?.errors ?? ""
            DispatchQueue.main.async { onExit(proc.terminationStatus, tail) }
        }
        buffer = Data()
        errors = ""
        do {
            try p.run()
            process = p
        } catch {
            onExit(1, error.localizedDescription)
        }
    }

    func stop() {
        if let p = process, p.isRunning { p.terminate() }
        process = nil
    }
}
