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
  private var latestTranscript = ""
  private var activeSessionID: UUID?
  private var hasListeners = false

  override static func requiresMainQueueSetup() -> Bool {
    true
  }

  override func supportedEvents() -> [String]! {
    ["SpeechRecognitionPartial", "SpeechRecognitionDebug"]
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
    let status = SFSpeechRecognizer.authorizationStatus()
    resolve(status == .authorized || status == .notDetermined)
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
      let sessionID = self.activeSessionID
      if self.audioEngine.isRunning {
        self.audioEngine.stop()
        self.recognitionRequest?.endAudio()
      }
      // iOS does not guarantee another recognition callback after endAudio().
      // Always settle the React Native promise so the UI cannot spin forever.
      DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
        guard sessionID != nil, self.activeSessionID == sessionID else { return }
        self.settleWithLatestTranscript(reason: "manual_stop_timeout")
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
      request.taskHint = .dictation

      pendingResolve = resolve
      pendingReject = reject
      latestTranscript = ""
      let sessionID = UUID()
      activeSessionID = sessionID
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
        guard self.activeSessionID == sessionID else { return }

        if let transcription = result?.bestTranscription.formattedString.trimmingCharacters(in: .whitespacesAndNewlines),
           !transcription.isEmpty {
          self.latestTranscript = transcription
          if result?.isFinal == true {
            self.settleWithLatestTranscript(reason: "final_result")
            return
          }

          if self.hasListeners {
            self.sendEvent(withName: "SpeechRecognitionPartial", body: transcription)
          }
        }

        if let error {
          if !self.latestTranscript.isEmpty {
            self.settleWithLatestTranscript(reason: "error_with_partial")
          } else {
            self.pendingReject?("speech_error", error.localizedDescription, error)
            self.clearPendingCallbacks()
            self.cleanupAudioSession()
          }
        }
      }

      // A recognizer/provider stall must never leave JavaScript waiting forever.
      DispatchQueue.main.asyncAfter(deadline: .now() + 18.0) { [weak self] in
        guard let self, self.activeSessionID == sessionID else { return }
        if self.audioEngine.isRunning {
          self.audioEngine.stop()
          self.recognitionRequest?.endAudio()
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { [weak self] in
          guard let self, self.activeSessionID == sessionID else { return }
          self.settleWithLatestTranscript(reason: "maximum_listening_timeout")
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
    activeSessionID = nil
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

  private func emitDebug(_ event: String, details: String = "") {
    guard hasListeners else { return }
    sendEvent(withName: "SpeechRecognitionDebug", body: [
      "event": event,
      "details": details,
      "latestTranscript": latestTranscript,
    ])
  }

  private func settleWithLatestTranscript(reason: String) {
    guard pendingResolve != nil || pendingReject != nil else { return }
    let transcript = latestTranscript.trimmingCharacters(in: .whitespacesAndNewlines)
    emitDebug("resolveWithLatestTranscript", details: reason)
    if transcript.isEmpty {
      pendingReject?("no_speech", "No speech detected", nil)
    } else {
      pendingResolve?(transcript)
    }
    latestTranscript = ""
    clearPendingCallbacks()
    cleanupAudioSession()
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
