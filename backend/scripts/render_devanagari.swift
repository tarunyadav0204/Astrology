import AppKit
import Foundation

struct Job: Decodable {
    let name: String
    let text: String
    let size: Double
    let weight: String
}

let input = CommandLine.arguments[1]
let outputDir = CommandLine.arguments[2]
let data = try Data(contentsOf: URL(fileURLWithPath: input))
let jobs = try JSONDecoder().decode([Job].self, from: data)
try FileManager.default.createDirectory(atPath: outputDir, withIntermediateDirectories: true)

let color = NSColor(calibratedRed: 62.0 / 255.0, green: 32.0 / 255.0, blue: 18.0 / 255.0, alpha: 1)
let soft = NSColor(calibratedRed: 98.0 / 255.0, green: 58.0 / 255.0, blue: 34.0 / 255.0, alpha: 1)
let rule = NSColor(calibratedRed: 156.0 / 255.0, green: 36.0 / 255.0, blue: 32.0 / 255.0, alpha: 1)

for job in jobs {
    let fontName = (job.weight == "bold")
        ? "KohinoorDevanagari-Bold"
        : (job.weight == "semibold" || job.weight == "rule" ? "KohinoorDevanagari-Semibold" : "KohinoorDevanagari-Medium")
    let font = NSFont(name: fontName, size: job.size) ?? NSFont(name: "Kohinoor Devanagari", size: job.size)!
    let ink: NSColor
    if job.weight == "soft" {
        ink = soft
    } else if job.weight == "rule" {
        ink = rule
    } else {
        ink = color
    }
    let attr = NSAttributedString(string: job.text, attributes: [.font: font, .foregroundColor: ink])
    let bounds = attr.size()
    let pad: CGFloat = 8
    let width = Int(ceil(bounds.width + pad * 2))
    let height = Int(ceil(bounds.height + pad * 2))
    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: width,
        pixelsHigh: height,
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else { continue }
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSColor.clear.setFill()
    NSRect(x: 0, y: 0, width: width, height: height).fill(using: .copy)
    attr.draw(at: NSPoint(x: pad, y: pad * 0.4))
    NSGraphicsContext.restoreGraphicsState()
    guard let png = rep.representation(using: .png, properties: [:]) else { continue }
    let path = (outputDir as NSString).appendingPathComponent(job.name + ".png")
    try png.write(to: URL(fileURLWithPath: path))
    print("\(job.name) \(width) \(height)")
}
