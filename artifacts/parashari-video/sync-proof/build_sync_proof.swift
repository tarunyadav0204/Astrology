import AppKit
import AVFoundation
import CoreText

let root = URL(fileURLWithPath: "/Users/tarunydv/Desktop/Code/AstrologyApp/artifacts/parashari-video/sync-proof")
let beforeURL = URL(fileURLWithPath: "/Users/tarunydv/Desktop/Code/AstrologyApp/artifacts/parashari-desk-guide/screenshots/01-desktop-overview.png")
let afterURL = URL(fileURLWithPath: "/Users/tarunydv/Desktop/Code/AstrologyApp/artifacts/parashari-desk-guide/screenshots/06-shadbala.png")
let audioURL = root.appendingPathComponent("narration.aiff")
let silentURL = root.appendingPathComponent("sync-proof-silent.mp4")
let outputURL = root.appendingPathComponent("Parashari_Desk_Synchronization_Proof.mp4")

let width = 1920
let height = 1080
let fps: Int32 = 30
let duration = 22.0

func loadCGImage(_ url: URL) -> CGImage {
    guard let image = NSImage(contentsOf: url),
          let data = image.tiffRepresentation,
          let rep = NSBitmapImageRep(data: data),
          let cg = rep.cgImage else {
        fatalError("Unable to load \(url.path)")
    }
    return cg
}

let before = loadCGImage(beforeURL)
let after = loadCGImage(afterURL)

try? FileManager.default.removeItem(at: silentURL)
try? FileManager.default.removeItem(at: outputURL)

let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mp4)
let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 9_000_000,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
        AVVideoMaxKeyFrameIntervalKey: 60
    ]
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
input.expectsMediaDataInRealTime = false
let attrs: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height
]
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attrs)
guard writer.canAdd(input) else { fatalError("Cannot add video input") }
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

let colorSpace = CGColorSpaceCreateDeviceRGB()

func ease(_ value: Double) -> Double {
    let x = max(0, min(1, value))
    return x * x * (3 - 2 * x)
}

func interpolate(_ start: CGPoint, _ end: CGPoint, _ amount: Double) -> CGPoint {
    let p = ease(amount)
    return CGPoint(x: start.x + (end.x - start.x) * p, y: start.y + (end.y - start.y) * p)
}

func drawText(_ text: String, rect: CGRect, fontSize: CGFloat, color: NSColor, weight: NSFont.Weight = .regular, alignment: CTTextAlignment = .left, context: CGContext) {
    let style = NSMutableParagraphStyle()
    style.alignment = alignment == .center ? .center : .left
    style.lineSpacing = 3
    let attrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: fontSize, weight: weight),
        .foregroundColor: color,
        .paragraphStyle: style
    ]
    let attributed = NSAttributedString(string: text, attributes: attrs)
    let framesetter = CTFramesetterCreateWithAttributedString(attributed)
    let path = CGPath(rect: rect, transform: nil)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: attributed.length), path, nil)
    CTFrameDraw(frame, context)
}

func roundedRect(_ context: CGContext, _ rect: CGRect, radius: CGFloat, fill: NSColor, stroke: NSColor? = nil, lineWidth: CGFloat = 1) {
    let path = CGPath(roundedRect: rect, cornerWidth: radius, cornerHeight: radius, transform: nil)
    context.addPath(path)
    context.setFillColor(fill.cgColor)
    context.fillPath()
    if let stroke {
        context.addPath(path)
        context.setStrokeColor(stroke.cgColor)
        context.setLineWidth(lineWidth)
        context.strokePath()
    }
}

func cursorPoint(at time: Double) -> CGPoint {
    let start = CGPoint(x: 1500, y: 1010)
    let sb = CGPoint(x: 1180, y: 1056)
    let heading = CGPoint(x: 430, y: 930)
    let leading = CGPoint(x: 470, y: 765)
    let lowest = CGPoint(x: 835, y: 765)
    let jupiter = CGPoint(x: 760, y: 570)
    let mars = CGPoint(x: 760, y: 205)
    if time < 4.9 { return start }
    if time < 6.5 { return interpolate(start, sb, (time - 4.9) / 1.6) }
    if time < 7.35 { return sb }
    if time < 8.15 { return interpolate(sb, heading, (time - 7.35) / 0.8) }
    if time < 9.15 { return interpolate(heading, leading, (time - 8.15) / 1.0) }
    if time < 10.9 { return leading }
    if time < 12.45 { return interpolate(leading, lowest, (time - 10.9) / 1.55) }
    if time < 13.2 { return lowest }
    if time < 14.0 { return interpolate(lowest, jupiter, (time - 13.2) / 0.8) }
    if time < 19.4 { return interpolate(jupiter, mars, (time - 14.0) / 5.4) }
    return mars
}

func drawCursor(_ context: CGContext, point: CGPoint, time: Double) {
    context.saveGState()
    context.setShadow(offset: CGSize(width: 2, height: -3), blur: 4, color: NSColor.black.withAlphaComponent(0.5).cgColor)
    let p = CGMutablePath()
    p.move(to: point)
    p.addLine(to: CGPoint(x: point.x + 12, y: point.y - 34))
    p.addLine(to: CGPoint(x: point.x + 21, y: point.y - 23))
    p.addLine(to: CGPoint(x: point.x + 34, y: point.y - 36))
    p.addLine(to: CGPoint(x: point.x + 42, y: point.y - 28))
    p.addLine(to: CGPoint(x: point.x + 28, y: point.y - 16))
    p.addLine(to: CGPoint(x: point.x + 40, y: point.y - 10))
    p.closeSubpath()
    context.addPath(p)
    context.setFillColor(NSColor.white.cgColor)
    context.fillPath()
    context.addPath(p)
    context.setStrokeColor(NSColor.black.cgColor)
    context.setLineWidth(2.5)
    context.strokePath()
    context.restoreGState()

    let clickStart = 6.62
    if time >= clickStart && time <= clickStart + 0.55 {
        let progress = (time - clickStart) / 0.55
        let radius = CGFloat(10 + 34 * progress)
        context.setStrokeColor(NSColor(calibratedRed: 0.65, green: 0.07, blue: 0.23, alpha: 1 - progress).cgColor)
        context.setLineWidth(5 - CGFloat(progress * 3))
        context.strokeEllipse(in: CGRect(x: point.x - radius, y: point.y - radius, width: radius * 2, height: radius * 2))
    }
}

func caption(at time: Double) -> String? {
    if time >= 0.8 && time < 5.2 {
        return "Parashari Desk keeps classical strength tools available\nwithout breaking the reading flow."
    }
    if time >= 5.2 && time < 8.0 {
        return "Move to SB, and open Shadbala."
    }
    if time >= 8.0 && time < 13.0 {
        return "At the top, the summary identifies the leading\nand lowest relative strengths."
    }
    if time >= 13.0 && time < 20.7 {
        return "Each planetary row presents its Rupas, total points and assessment together,\nmaking relative strength easy to compare."
    }
    return nil
}

func drawFrame(time: Double, into buffer: CVPixelBuffer) {
    CVPixelBufferLockBaseAddress(buffer, [])
    defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
    guard let base = CVPixelBufferGetBaseAddress(buffer),
          let context = CGContext(data: base, width: width, height: height, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: colorSpace, bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue) else {
        fatalError("Unable to create frame context")
    }

    context.setFillColor(NSColor(calibratedWhite: 0.98, alpha: 1).cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))

    let transitionStart = 6.76
    let transitionEnd = 7.34
    let mix: Double
    if time <= transitionStart { mix = 0 }
    else if time >= transitionEnd { mix = 1 }
    else { mix = ease((time - transitionStart) / (transitionEnd - transitionStart)) }

    let frameRect = CGRect(x: 0, y: 0, width: width, height: height)
    context.setAlpha(CGFloat(1 - mix))
    context.draw(before, in: frameRect)
    if mix > 0 {
        context.setAlpha(CGFloat(mix))
        context.draw(after, in: frameRect)
    }
    context.setAlpha(1)

    if time < 3.4 {
        let alpha = CGFloat(min(1, time / 0.35) * min(1, (3.4 - time) / 0.45))
        roundedRect(context, CGRect(x: 60, y: 865, width: 620, height: 132), radius: 18, fill: NSColor(calibratedWhite: 0.08, alpha: 0.88 * alpha))
        drawText("SYNCHRONIZATION PROOF", rect: CGRect(x: 88, y: 945, width: 550, height: 28), fontSize: 18, color: NSColor(calibratedRed: 0.96, green: 0.67, blue: 0.74, alpha: alpha), weight: .bold, context: context)
        drawText("Shadbala transition", rect: CGRect(x: 86, y: 890, width: 560, height: 55), fontSize: 34, color: NSColor.white.withAlphaComponent(alpha), weight: .semibold, context: context)
    }

    if let line = caption(at: time) {
        roundedRect(context, CGRect(x: 275, y: 42, width: 1370, height: 118), radius: 18, fill: NSColor(calibratedWhite: 0.05, alpha: 0.84))
        drawText(line, rect: CGRect(x: 315, y: 68, width: 1290, height: 76), fontSize: 30, color: .white, weight: .medium, alignment: .center, context: context)
    }

    drawCursor(context, point: cursorPoint(at: time), time: time)
}

let frameCount = Int(duration * Double(fps))
for frameIndex in 0..<frameCount {
    while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.002) }
    var maybeBuffer: CVPixelBuffer?
    let pixelStatus = CVPixelBufferCreate(
        kCFAllocatorDefault,
        width,
        height,
        kCVPixelFormatType_32ARGB,
        attrs as CFDictionary,
        &maybeBuffer
    )
    guard pixelStatus == kCVReturnSuccess else { fatalError("Unable to allocate pixel buffer: \(pixelStatus)") }
    guard let buffer = maybeBuffer else { fatalError("Unable to allocate frame") }
    let time = Double(frameIndex) / Double(fps)
    drawFrame(time: time, into: buffer)
    let pts = CMTime(value: CMTimeValue(frameIndex), timescale: fps)
    if !adaptor.append(buffer, withPresentationTime: pts) {
        fatalError("Append failed: \(writer.error?.localizedDescription ?? "unknown")")
    }
}

input.markAsFinished()
let writingDone = DispatchSemaphore(value: 0)
writer.finishWriting { writingDone.signal() }
writingDone.wait()
if writer.status != .completed {
    fatalError("Video writer failed: \(writer.error?.localizedDescription ?? "unknown")")
}

let composition = AVMutableComposition()
let videoAsset = AVURLAsset(url: silentURL)
let audioAsset = AVURLAsset(url: audioURL)
guard let sourceVideo = videoAsset.tracks(withMediaType: .video).first,
      let videoTrack = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fatalError("Unable to create video composition track")
}
try videoTrack.insertTimeRange(CMTimeRange(start: .zero, duration: CMTime(seconds: duration, preferredTimescale: 600)), of: sourceVideo, at: .zero)

if let sourceAudio = audioAsset.tracks(withMediaType: .audio).first,
   let audioTrack = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) {
    let audioStart = CMTime(seconds: 0.8, preferredTimescale: 600)
    let available = CMTimeSubtract(CMTime(seconds: duration, preferredTimescale: 600), audioStart)
    let useDuration = CMTimeMinimum(audioAsset.duration, available)
    try audioTrack.insertTimeRange(CMTimeRange(start: .zero, duration: useDuration), of: sourceAudio, at: audioStart)
}

guard let exporter = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
    fatalError("Unable to create exporter")
}
exporter.outputURL = outputURL
exporter.outputFileType = .mp4
exporter.shouldOptimizeForNetworkUse = true
let exportDone = DispatchSemaphore(value: 0)
exporter.exportAsynchronously { exportDone.signal() }
exportDone.wait()
if exporter.status != .completed {
    fatalError("Export failed: \(exporter.error?.localizedDescription ?? "unknown")")
}

print(outputURL.path)
