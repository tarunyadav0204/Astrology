package com.astroroshni.mobile

import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import java.io.File

/** Target a video receiver, leaving review and publishing to the selected app. */
class ReelShareModule(private val context: ReactApplicationContext) : ReactContextBaseJavaModule(context) {
  override fun getName() = "ReelShare"

  @ReactMethod
  fun shareToApp(url: String, destination: String, promise: Promise) {
    val target = when (destination) {
      "Instagram" -> "com.instagram.android"
      "Facebook" -> "com.facebook.katana"
      "YouTube" -> "com.google.android.youtube"
      else -> { promise.resolve(false); return }
    }
    try {
      val uri = Uri.parse(url)
      require(uri.scheme == "file") { "Expected a local reel file" }
      val file = File(requireNotNull(uri.path)).canonicalFile
      val directory = File(context.filesDir, "shared-reels").canonicalFile
      require(file.path.startsWith(directory.path + File.separator) && file.isFile && file.length() > 0) {
        "Reel file is unavailable"
      }
      val contentUri = FileProvider.getUriForFile(context, context.packageName + ".SharingFileProvider", file)
      val intent = Intent(Intent.ACTION_SEND).apply {
        type = "video/mp4"
        setPackage(target)
        putExtra(Intent.EXTRA_STREAM, contentUri)
        clipData = ClipData.newUri(context.contentResolver, "AstroRoshni", contentUri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
      }
      if (intent.resolveActivity(context.packageManager) == null) {
        promise.resolve(false)
        return
      }
      val activity = context.currentActivity
      if (activity == null) { promise.resolve(false); return }
      activity.runOnUiThread {
        try {
          activity.startActivity(intent)
          // Success means the upload/share flow opened, not that it was published.
          promise.resolve(true)
        } catch (_: ActivityNotFoundException) {
          promise.resolve(false)
        } catch (_: SecurityException) {
          promise.resolve(false)
        } catch (error: Exception) {
          promise.reject("REEL_SHARE_FAILED", error)
        }
      }
    } catch (error: Exception) {
      promise.reject("REEL_SHARE_FAILED", error)
    }
  }
}
