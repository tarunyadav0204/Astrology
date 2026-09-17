# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in /usr/local/Cellar/android-sdk/24.3.3/tools/proguard/proguard-android.txt
# You can edit the include path and order by changing the proguardFiles
# directive in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# react-native-reanimated
-keep class com.swmansion.reanimated.** { *; }
-keep class com.facebook.react.turbomodule.** { *; }

# Add any project specific keep options here:

# @generated begin expo-build-properties - expo prebuild (DO NOT MODIFY)
# Keep enough native-bridge surface for release R8 without disabling obfuscation.
-keepattributes SourceFile,LineNumberTable,Signature,*Annotation*,Exceptions,InnerClasses,EnclosingMethod,JavascriptInterface
-renamesourcefileattribute SourceFile
-keep class com.facebook.hermes.unicode.** { *; }
-keep class com.facebook.jni.** { *; }
-keep class com.razorpay.** { *; }
-dontwarn com.razorpay.**
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-keep class com.appsflyer.** { *; }
-keep class com.margelo.nitro.** { *; }
# @generated end expo-build-properties
