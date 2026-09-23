package com.astroroshni.mobile

import android.app.Activity
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.LifecycleEventListener
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.modules.core.DeviceEventManagerModule
import com.google.android.play.core.appupdate.AppUpdateManager
import com.google.android.play.core.appupdate.AppUpdateManagerFactory
import com.google.android.play.core.appupdate.AppUpdateOptions
import com.google.android.play.core.install.InstallStateUpdatedListener
import com.google.android.play.core.install.model.ActivityResult
import com.google.android.play.core.install.model.AppUpdateType
import com.google.android.play.core.install.model.InstallStatus
import com.google.android.play.core.install.model.UpdateAvailability

class PlayInAppUpdateModule(reactContext: ReactApplicationContext) :
  ReactContextBaseJavaModule(reactContext), LifecycleEventListener {

  private val manager: AppUpdateManager = AppUpdateManagerFactory.create(reactContext)
  private var listenerRegistered = false
  private val installListener = InstallStateUpdatedListener { state ->
    emitStatus(installStatusName(state.installStatus()))
  }

  init {
    reactContext.addLifecycleEventListener(this)
  }

  override fun getName(): String = "PlayInAppUpdate"

  @ReactMethod
  fun check(promise: Promise) {
    manager.appUpdateInfo
      .addOnSuccessListener { info ->
        val map = Arguments.createMap().apply {
          putBoolean(
            "updateAvailable",
            info.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE,
          )
          putBoolean(
            "updateInProgress",
            info.updateAvailability() == UpdateAvailability.DEVELOPER_TRIGGERED_UPDATE_IN_PROGRESS,
          )
          putBoolean("immediateAllowed", info.isUpdateTypeAllowed(AppUpdateType.IMMEDIATE))
          putBoolean("flexibleAllowed", info.isUpdateTypeAllowed(AppUpdateType.FLEXIBLE))
          putInt("availableVersionCode", info.availableVersionCode())
          putInt("updatePriority", info.updatePriority())
          val staleness = info.clientVersionStalenessDays()
          if (staleness == null) putNull("stalenessDays") else putInt("stalenessDays", staleness)
          putString("installStatus", installStatusName(info.installStatus()))
        }
        promise.resolve(map)
      }
      .addOnFailureListener { error ->
        promise.reject("play_update_check_failed", error.message, error)
      }
  }

  @ReactMethod
  fun start(mode: String, promise: Promise) {
    reactApplicationContext.runOnUiQueueThread {
      startOnUiThread(mode, promise)
    }
  }

  private fun startOnUiThread(mode: String, promise: Promise) {
    val activity = reactApplicationContext.currentActivity
    if (activity == null) {
      promise.reject("no_activity", "No foreground activity")
      return
    }
    val updateType = if (mode == "immediate") AppUpdateType.IMMEDIATE else AppUpdateType.FLEXIBLE
    manager.appUpdateInfo
      .addOnSuccessListener { info ->
        val downloaded = info.installStatus() == InstallStatus.DOWNLOADED
        if (downloaded) {
          promise.resolve("downloaded")
          emitStatus("downloaded")
          return@addOnSuccessListener
        }
        val inProgress = info.updateAvailability() == UpdateAvailability.DEVELOPER_TRIGGERED_UPDATE_IN_PROGRESS
        val available = info.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE &&
          info.isUpdateTypeAllowed(updateType)
        if (!inProgress && !available) {
          promise.resolve("unavailable")
          return@addOnSuccessListener
        }
        if (updateType == AppUpdateType.FLEXIBLE) {
          ensureListener()
        }
        manager.startUpdateFlow(info, activity, AppUpdateOptions.newBuilder(updateType).build())
          .addOnSuccessListener { resultCode ->
            promise.resolve(
              when (resultCode) {
                Activity.RESULT_OK -> "accepted"
                Activity.RESULT_CANCELED -> "canceled"
                ActivityResult.RESULT_IN_APP_UPDATE_FAILED -> "failed"
                else -> "failed"
              },
            )
          }
          .addOnFailureListener { error ->
            promise.reject("play_update_start_failed", error.message, error)
          }
      }
      .addOnFailureListener { error ->
        promise.reject("play_update_check_failed", error.message, error)
      }
  }

  @ReactMethod
  fun completeUpdate(promise: Promise) {
    reactApplicationContext.runOnUiQueueThread {
      manager.completeUpdate()
        .addOnSuccessListener { promise.resolve(null) }
        .addOnFailureListener { error ->
          promise.reject("play_update_complete_failed", error.message, error)
        }
    }
  }

  @ReactMethod
  fun addListener(eventName: String) {
  }

  @ReactMethod
  fun removeListeners(count: Int) {
  }

  override fun onHostResume() {
  }

  override fun onHostPause() {
  }

  override fun onHostDestroy() {
    if (listenerRegistered) {
      manager.unregisterListener(installListener)
      listenerRegistered = false
    }
  }

  private fun ensureListener() {
    if (listenerRegistered) return
    manager.registerListener(installListener)
    listenerRegistered = true
  }

  private fun emitStatus(status: String) {
    if (!reactApplicationContext.hasActiveReactInstance()) return
    val payload = Arguments.createMap().apply { putString("status", status) }
    reactApplicationContext
      .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
      .emit("PlayInAppUpdateStatus", payload)
  }

  private fun installStatusName(status: Int): String = when (status) {
    InstallStatus.PENDING -> "pending"
    InstallStatus.DOWNLOADING -> "downloading"
    InstallStatus.DOWNLOADED -> "downloaded"
    InstallStatus.INSTALLING -> "installing"
    InstallStatus.INSTALLED -> "installed"
    InstallStatus.FAILED -> "failed"
    InstallStatus.CANCELED -> "canceled"
    else -> "unknown"
  }
}
