package com.astroroshni.mobile

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.content.ContextCompat
import com.facebook.react.bridge.*
import com.facebook.react.modules.core.DeviceEventManagerModule
import java.util.Locale

class SpeechRecognitionModule(private val reactContext: ReactApplicationContext) :
  ReactContextBaseJavaModule(reactContext), RecognitionListener {
  companion object {
    private const val MINIMUM_LISTENING_MILLIS = 6500L
    private const val COMPLETE_SILENCE_MILLIS = 3200L
    private const val POSSIBLY_COMPLETE_SILENCE_MILLIS = 2200L
    private const val PARTIAL_STABLE_MILLIS = 1300L
    private const val MAX_LISTENING_MILLIS = 14000L
  }

  private var speechRecognizer: SpeechRecognizer? = null
  private var pendingPromise: Promise? = null
  private var currentLocale: String = Locale.getDefault().toLanguageTag()
  private var latestTranscript: String = ""
  private var manualStopRequested: Boolean = false
  private var listeningStartedAtMillis: Long = 0L
  private var lastRmsDebugAtMillis: Long = 0L
  private val mainHandler = Handler(Looper.getMainLooper())
  private val partialStableRunnable = Runnable {
    resolveWithLatestTranscript("partial_stable")
  }
  private val maxListeningRunnable = Runnable {
    resolveWithLatestTranscript("max_listening")
  }

  override fun getName(): String = "SpeechRecognition"

  private fun emitDebug(event: String, details: String = "") {
    if (!reactContext.hasActiveReactInstance()) return
    val payload = Arguments.createMap().apply {
      putString("event", event)
      putString("details", details)
      putString("latestTranscript", latestTranscript)
      putDouble("elapsedMs", if (listeningStartedAtMillis > 0L) (System.currentTimeMillis() - listeningStartedAtMillis).toDouble() else 0.0)
    }
    reactContext
      .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
      .emit("SpeechRecognitionDebug", payload)
  }

  @ReactMethod
  fun isAvailable(promise: Promise) {
    promise.resolve(SpeechRecognizer.isRecognitionAvailable(reactContext))
  }

  @ReactMethod
  fun startListening(locale: String?, promise: Promise) {
    try {
      if (!SpeechRecognizer.isRecognitionAvailable(reactContext)) {
        promise.reject("not_available", "Speech recognition is not available on this device")
        return
      }
      if (ContextCompat.checkSelfPermission(reactContext, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
        promise.reject("no_permission", "Microphone permission is required")
        return
      }
      if (pendingPromise != null) {
        promise.reject("busy", "Speech recognition is already active")
        return
      }
      val activity: Activity? = getCurrentActivity()
      if (activity == null) {
        promise.reject("no_activity", "No active screen available for speech recognition")
        return
      }

      currentLocale = normalizeLocale(locale)
      latestTranscript = ""
      manualStopRequested = false
      listeningStartedAtMillis = System.currentTimeMillis()
      lastRmsDebugAtMillis = 0L
      clearTimers()
      pendingPromise = promise
      emitDebug("startListening", currentLocale)
      mainHandler.post {
        try {
          try {
            speechRecognizer?.cancel()
            speechRecognizer?.destroy()
          } catch (e: Exception) {
            // Ignore stale recognizer cleanup failures before a fresh start.
          }
          speechRecognizer = null
          val recognizer = SpeechRecognizer.createSpeechRecognizer(activity).also {
            it.setRecognitionListener(this)
            speechRecognizer = it
          }

          val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, currentLocale)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, currentLocale)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, false)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, reactContext.packageName)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, MINIMUM_LISTENING_MILLIS)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, COMPLETE_SILENCE_MILLIS)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, POSSIBLY_COMPLETE_SILENCE_MILLIS)
          }
          recognizer.startListening(intent)
          emitDebug("recognizerStarted", currentLocale)
          mainHandler.postDelayed(maxListeningRunnable, MAX_LISTENING_MILLIS)
        } catch (e: Exception) {
          val currentPromise = pendingPromise
          pendingPromise = null
          clearTimers()
          emitDebug("startFailed", e.message ?: "")
          currentPromise?.reject("start_failed", e.message ?: "Could not start speech recognition", e)
        }
      }
    } catch (e: Exception) {
      pendingPromise = null
      clearTimers()
      emitDebug("startFailedOuter", e.message ?: "")
      promise.reject("start_failed", e.message ?: "Could not start speech recognition", e)
    }
  }

  @ReactMethod
  fun stopListening() {
    mainHandler.post {
      try {
        manualStopRequested = true
        clearTimers()
        emitDebug("stopListening")
        speechRecognizer?.stopListening()
      } catch (e: Exception) {
        val promise = pendingPromise
        pendingPromise = null
        manualStopRequested = false
        clearTimers()
        emitDebug("stopFailed", e.message ?: "")
        promise?.reject("stop_failed", e.message ?: "Could not stop speech recognition", e)
      }
    }
  }

  @ReactMethod
  fun cancelListening() {
    pendingPromise?.reject("cancelled", "Speech recognition cancelled")
    pendingPromise = null
    latestTranscript = ""
    manualStopRequested = false
    listeningStartedAtMillis = 0L
    lastRmsDebugAtMillis = 0L
    clearTimers()
    emitDebug("cancelListening")
    mainHandler.post {
      try {
        speechRecognizer?.cancel()
      } catch (e: Exception) {
        // ignore cancellation failures
      }
    }
  }

  @ReactMethod
  fun addListener(eventName: String?) {
    // Required for NativeEventEmitter compatibility.
  }

  @ReactMethod
  fun removeListeners(count: Int) {
    // Required for NativeEventEmitter compatibility.
  }

  override fun onReadyForSpeech(params: Bundle?) {
    emitDebug("onReadyForSpeech")
  }
  override fun onBeginningOfSpeech() {
    emitDebug("onBeginningOfSpeech")
  }
  override fun onRmsChanged(rmsdB: Float) {
    val now = System.currentTimeMillis()
    if (now - lastRmsDebugAtMillis >= 700L) {
      lastRmsDebugAtMillis = now
      emitDebug("onRmsChanged", rmsdB.toString())
    }
  }
  override fun onBufferReceived(buffer: ByteArray?) {}
  override fun onEndOfSpeech() {
    emitDebug("onEndOfSpeech")
    // Settle shortly after end-of-speech using the best transcript we have.
    // resolveWithLatestTranscript rejects cleanly if it is still blank.
    mainHandler.postDelayed({ resolveWithLatestTranscript("end_of_speech") }, 250L)
  }
  override fun onEvent(eventType: Int, params: Bundle?) {
    emitDebug("onEvent", eventType.toString())
  }

  override fun onPartialResults(partialResults: Bundle?) {
    val partial = partialResults
      ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
      ?.firstOrNull()
      ?.trim()
      .orEmpty()
    if (partial.isBlank()) {
      emitDebug("onPartialResultsBlank")
      return
    }
    latestTranscript = partial
    emitDebug("onPartialResults", partial)
    mainHandler.removeCallbacks(partialStableRunnable)
    mainHandler.postDelayed(partialStableRunnable, PARTIAL_STABLE_MILLIS)
    // RN 0.81 / New Arch: prefer emitDeviceEvent over getJSModule(RCTDeviceEventEmitter).
    if (reactContext.hasActiveReactInstance()) {
      reactContext.emitDeviceEvent("SpeechRecognitionPartial", partial)
    }
  }

  override fun onResults(results: Bundle?) {
    val transcript = results
      ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
      ?.firstOrNull()
      ?.trim()
      ?.takeIf { it.isNotBlank() }
      ?: latestTranscript.trim()
    val promise = pendingPromise
    pendingPromise = null
    clearTimers()
    emitDebug("onResults", transcript)
    latestTranscript = ""
    manualStopRequested = false
    listeningStartedAtMillis = 0L
    lastRmsDebugAtMillis = 0L
    if (transcript.isBlank()) {
      promise?.reject("no_speech", "No speech detected")
    } else {
      promise?.resolve(transcript)
    }
    mainHandler.post {
      try {
        speechRecognizer?.cancel()
        speechRecognizer?.destroy()
      } catch (e: Exception) {
        // ignore cleanup failures
      }
      speechRecognizer = null
    }
  }

  override fun onError(error: Int) {
    val transcriptFallback = latestTranscript.trim()
    emitDebug("onError", "${errorCode(error)}:${errorMessage(error)}")
    val promise = pendingPromise
    pendingPromise = null
    clearTimers()
    val shouldUseTranscriptFallback =
      transcriptFallback.isNotBlank() && (
        manualStopRequested ||
          error == SpeechRecognizer.ERROR_NO_MATCH ||
          error == SpeechRecognizer.ERROR_CLIENT ||
          error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT
      )
    latestTranscript = ""
    manualStopRequested = false
    listeningStartedAtMillis = 0L
    lastRmsDebugAtMillis = 0L
    if (shouldUseTranscriptFallback) {
      promise?.resolve(transcriptFallback)
      mainHandler.post {
        try {
          speechRecognizer?.cancel()
          speechRecognizer?.destroy()
        } catch (e: Exception) {
          // ignore cleanup failures
        }
        speechRecognizer = null
      }
      return
    }
    promise?.reject(errorCode(error), errorMessage(error))
    mainHandler.post {
      try {
        speechRecognizer?.cancel()
        speechRecognizer?.destroy()
      } catch (e: Exception) {
        // ignore cleanup failures
      }
      speechRecognizer = null
    }
  }

  override fun invalidate() {
    pendingPromise = null
    latestTranscript = ""
    manualStopRequested = false
    listeningStartedAtMillis = 0L
    lastRmsDebugAtMillis = 0L
    clearTimers()
    emitDebug("invalidate")
    mainHandler.post {
      try {
        speechRecognizer?.destroy()
      } catch (e: Exception) {
        // ignore
      }
      speechRecognizer = null
    }
    super.invalidate()
  }

  private fun normalizeLocale(locale: String?): String {
    val raw = (locale ?: "").trim().lowercase(Locale.US)
    return when {
      raw.startsWith("hi") || raw == "hindi" -> "hi-IN"
      // Preserve explicit English regions (en-US, en-GB, en-IN, …).
      raw.matches(Regex("^en[-_][a-z]{2}$")) -> {
        val parts = raw.split('-', '_')
        "en-${parts[1].uppercase(Locale.US)}"
      }
      // App language codes like "english" / "en" / blank → US English (previous default).
      raw.startsWith("en") || raw == "english" || raw.isBlank() -> "en-US"
      else -> locale ?: Locale.getDefault().toLanguageTag()
    }
  }

  private fun clearTimers() {
    mainHandler.removeCallbacks(partialStableRunnable)
    mainHandler.removeCallbacks(maxListeningRunnable)
  }

  private fun resolveWithLatestTranscript(reason: String) {
    val transcript = latestTranscript.trim()
    val promise = pendingPromise ?: return
    if (transcript.isBlank()) {
      // partial_stable can race with an empty partial overwrite; keep listening and
      // let max_listening / onResults / onError settle the promise.
      if (reason == "partial_stable") {
        emitDebug("resolveBlankIgnored", reason)
        return
      }
      // Terminal reasons must always settle so the JS promise cannot hang.
      pendingPromise = null
      latestTranscript = ""
      manualStopRequested = false
      listeningStartedAtMillis = 0L
      lastRmsDebugAtMillis = 0L
      clearTimers()
      emitDebug("resolveBlank", reason)
      promise.reject("no_speech", "No speech detected")
      mainHandler.post {
        try {
          speechRecognizer?.cancel()
          speechRecognizer?.destroy()
        } catch (e: Exception) {
          // ignore cleanup failures
        }
        speechRecognizer = null
      }
      return
    }
    pendingPromise = null
    latestTranscript = ""
    manualStopRequested = false
    listeningStartedAtMillis = 0L
    lastRmsDebugAtMillis = 0L
    clearTimers()
    emitDebug("resolveWithLatestTranscript", reason)
    promise.resolve(transcript)
    mainHandler.post {
      try {
        speechRecognizer?.cancel()
        speechRecognizer?.destroy()
      } catch (e: Exception) {
        // ignore cleanup failures
      }
      speechRecognizer = null
    }
  }

  private fun errorCode(error: Int): String = "speech_error_$error"

  private fun errorMessage(error: Int): String = when (error) {
    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
    SpeechRecognizer.ERROR_CLIENT -> "Speech recognition client error"
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Speech recognition permission denied"
    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Speech recognition network error"
    SpeechRecognizer.ERROR_NO_MATCH -> "Could not understand the speech"
    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech recognizer is busy"
    SpeechRecognizer.ERROR_SERVER -> "Speech recognition server error"
    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech was detected"
    else -> "Speech recognition failed"
  }
}
