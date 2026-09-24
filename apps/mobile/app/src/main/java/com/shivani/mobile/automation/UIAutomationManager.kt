package com.shivani.mobile.automation

import android.content.Context
import android.content.Intent
import com.shivani.mobile.accessibility.ShivaniAccessibilityService
import com.shivani.mobile.bridge.VisibleObservation
import com.shivani.mobile.storage.ActivityLogger

object UIAutomationManager {

    fun launchApp(context: Context, packageName: String): Boolean {
        val launchIntent = context.packageManager.getLaunchIntentForPackage(packageName) ?: return false
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED)
        context.startActivity(launchIntent)
        ActivityLogger.log("Launch App", packageName, success = true)
        return true
    }

    fun captureVisibleUI(): VisibleObservation? {
        val service = ShivaniAccessibilityService.instance ?: return null
        return service.captureVisibleUI()
    }

    fun tap(x: Float, y: Float, callback: (Boolean) -> Unit) {
        val service = ShivaniAccessibilityService.instance
        if (service == null) {
            callback(false)
            return
        }
        service.performTap(x, y) { success ->
            ActivityLogger.log("Tap", "Coordinates: ($x, $y)", success = success)
            callback(success)
        }
    }

    fun swipe(startX: Float, startY: Float, endX: Float, endY: Float, callback: (Boolean) -> Unit) {
        val service = ShivaniAccessibilityService.instance
        if (service == null) {
            callback(false)
            return
        }
        service.performSwipe(startX, startY, endX, endY) { success ->
            ActivityLogger.log("Swipe", "($startX, $startY) -> ($endX, $endY)", success = success)
            callback(success)
        }
    }

    fun pressBack(): Boolean {
        val service = ShivaniAccessibilityService.instance ?: return false
        val success = service.performBack()
        ActivityLogger.log("Navigation", "Back", success = success)
        return success
    }

    fun pressHome(): Boolean {
        val service = ShivaniAccessibilityService.instance ?: return false
        val success = service.performHome()
        ActivityLogger.log("Navigation", "Home", success = success)
        return success
    }

    fun typeText(text: String): Boolean {
        val service = ShivaniAccessibilityService.instance ?: return false
        val success = service.performTypeText(text)
        ActivityLogger.log("Type Text", "Length: ${text.length}", success = success)
        return success
    }
}
