import AppKit
import AVFoundation

let root = URL(fileURLWithPath: "/Users/tarunydv/Desktop/Code/AstrologyApp/artifacts/parashari-video/sync-proof")
let video = AVURLAsset(url: root.appendingPathComponent("Parashari_Desk_Synchronization_Proof.mp4"))
let generator = AVAssetImageGenerator(asset: video)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero

for second in [2.0, 6.4, 7.1, 8.8, 10.5, 12.5, 15.0, 18.5] {
    let time = CMTime(seconds: second, preferredTimescale: 600)
    let image = try generator.copyCGImage(at: time, actualTime: nil)
    let bitmap = NSBitmapImageRep(cgImage: image)
    guard let png = bitmap.representation(using: .png, properties: [:]) else { continue }
    let name = String(format: "review-%04.1f.png", second)
    try png.write(to: root.appendingPathComponent(name))
}

print("review frames written")
