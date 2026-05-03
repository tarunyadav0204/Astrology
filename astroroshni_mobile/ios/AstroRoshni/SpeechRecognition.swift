import AVFoundation
import Foundation
import Speech

@objc(SpeechRecognition)
class SpeechRecognition: RCTEventEmitter {
  private let audioEngine = AVAudioEngine()
  private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
  private var recognitionTask: SFSpeechRecognitionTask?
  private var speechRecognizer: SFSpeechRecognizer?
  private var pendingResolve: RCTPromiseResolveBlock?
  private var pendingReject: RCTPromiseRejectBlock?
  private var hasListeners = false

  override static func requiresMainQueueSetup() -> Bool {
    true
  }

  override func supportedEvents() -> [String]! {
    ["SpeechRecognitionPartial"]
  }

  override func startObserving() {
    hasListeners = true
  }

  override func stopObserving() {
    hasListeners = false
  }

  @objc
  override func invalidate() {
    cleanupAudioSession()
    super.invalidate()
  }

  @objc(isAvailable:rejecter:)
  func isAvailable(
    _ resolve: RCTPromiseResolveBlock,
    rejecter reject: RCTPromiseRejectBlock
  ) {
    resolve(SFSpeechRecognizer.authorizationStatus() != .restricted)
  }

  @objc(startListening:resolver:rejecter:)
  func startListening(
    _ locale: String?,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    if pendingResolve != nil || pendingReject != nil {
      reject("busy", "Speech recognition is already active", nil)
      return
    }

    requestPermissions { [weak self] granted, permissionError in
      guard let self else { return }
      guard granted else {
        reject("no_permission", permissionError ?? "Microphone and speech recognition permission are required", nil)
        return
      }

      DispatchQueue.main.async {
        self.beginRecognition(locale: locale, resolve: resolve, reject: reject)
      }
    }
  }

  @objc
  func stopListening() {
    DispatchQueue.main.async {
      if self.audioEngine.isRunning {
        self.audioEngine.stop()
        self.recognitionRequest?.endAudio()
      }
    }
  }

  @objc
  func cancelListening() {
    DispatchQueue.main.async {
      self.pendingReject?("cancelled", "Speech recognition cancelled", nil)
      self.clearPendingCallbacks()
      self.cleanupAudioSession()
    }
  }

  private func beginRecognition(
    locale: String?,
    resolve: @escaping RCTPromiseResolveBlock,
    reject: @escaping RCTPromiseRejectBlock
  ) {
    cleanupAudioSession()

    let normalizedLocale = normalizedLocaleIdentifier(locale)
    guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: normalizedLocale)), recognizer.isAvailable else {
      reject("not_available", "Speech recognition is not available on this device", nil)
      return
    }

    do {
      let audioSession = AVAudioSession.sharedInstance()
      try audioSession.setCategory(.record, mode: .measurement, options: [.duckOthers])
      try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

      let request = SFSpeechAudioBufferRecognitionRequest()
      request.shouldReportPartialResults = true

      pendingResolve = resolve
      pendingReject = reject
      speechRecognizer = recognizer
      recognitionRequest = request

      let inputNode = audioEngine.inputNode
      let recordingFormat = inputNode.outputFormat(forBus: 0)
      inputNode.removeTap(onBus: 0)
      inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
        self?.recognitionRequest?.append(buffer)
      }

      audioEngine.prepare()
      try audioEngine.start()

      recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
        guard let self else { return }

        if let transcription = result?.bestTranscription.formattedString.trimmingCharacters(in: .whitespacesAndNewlines),
           !transcription.isEmpty {
          if result?.isFinal == true {
            self.pendingResolve?(transcription)
            self.clearPendingCallbacks()
            self.cleanupAudioSession()
            return
          }

          if self.hasListeners {
            self.sendEvent(withName: "SpeechRecognitionPartial", body: transcription)
          }
        }

        if let error {
          self.pendingReject?("speech_error", error.localizedDescription, error)
          self.clearPendingCallbacks()
          self.cleanupAudioSession()
        }
      }
    } catch {
      cleanupAudioSession()
      reject("speech_error", error.localizedDescription, error)
    }
  }

  private func requestPermissions(completion: @escaping (Bool, String?) -> Void) {
    AVAudioSession.sharedInstance().requestRecordPermission { micGranted in
      guard micGranted else {
        completion(false, "Microphone permission is required")
        return
      }

      SFSpeechRecognizer.requestAuthorization { status in
        switch status {
        case .authorized:
          completion(true, nil)
        case .denied:
          completion(false, "Speech recognition permission was denied")
        case .restricted:
          completion(false, "Speech recognition is restricted on this device")
        case .notDetermined:
          completion(false, "Speech recognition permission is not determined yet")
        @unknown default:
          completion(false, "Speech recognition permission failed")
        }
      }
    }
  }

  private func cleanupAudioSession() {
    recognitionTask?.cancel()
    recognitionTask = nil

    recognitionRequest?.endAudio()
    recognitionRequest = nil

    if audioEngine.isRunning {
      audioEngine.stop()
    }
    audioEngine.inputNode.removeTap(onBus: 0)

    try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
  }

  private func clearPendingCallbacks() {
    pendingResolve = nil
    pendingReject = nil
  }

  private func normalizedLocaleIdentifier(_ locale: String?) -> String {
    let raw = (locale ?? "").trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    if raw.hasPrefix("hi") || raw == "hindi" {
      return "hi-IN"
    }
    if raw.isEmpty || raw.hasPrefix("en") || raw == "english" {
      return "en-US"
    }
    return locale ?? Locale.current.identifier
  }
}
