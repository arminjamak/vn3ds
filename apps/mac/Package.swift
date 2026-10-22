// swift-tools-version:5.9
// The vn3ds Mac app: drag a visual novel in, it ends up on the 3DS.
// Built into a .dmg by build_dmg.sh (no Xcode project).
import PackageDescription

let package = Package(
    name: "VN3DSPort",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "VN3DSPort", path: "Sources/VN3DSPort")
    ]
)
