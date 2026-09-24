package com.shivani.mobile.accessibility

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.os.Bundle
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.shivani.mobile.bridge.UIElement
import com.shivani.mobile.bridge.VisibleObservation

class ShivaniAccessibilityService : AccessibilityService() {

    companion object {
        var instance: ShivaniAccessibilityService? = null
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Event-driven updates can update active window cache
    }

    override fun onInterrupt() {
        // Handle interruption
    }

    override fun onDestroy() {
        super.onDestroy()
        if (instance == this) {
            instance = null
        }
    }

    fun captureVisibleUI(): VisibleObservation {
        val rootNode = rootInActiveWindow ?: return VisibleObservation("unknown", "unknown")
        val pkg = rootNode.packageName?.toString() ?: "unknown"
        val elements = mutableListOf<UIElement>()

        traverseNode(rootNode, elements)

        return VisibleObservation(
            package_name = pkg,
            activity_name = "ActiveWindow",
            elements = elements,
            timestamp = System.currentTimeMillis() / 1000.0
        )
    }

    private fun traverseNode(node: AccessibilityNodeInfo?, list: MutableList<UIElement>) {
        if (node == null || !node.isVisibleToUser) return

        val text = node.text?.toString() ?: ""
        val desc = node.contentDescription?.toString() ?: ""
        val resId = node.viewIdResourceName ?: ""
        val clickable = node.isClickable

        // Data minimization: only collect nodes with text, description, or clickability
        if (text.isNotEmpty() || desc.isNotEmpty() || clickable) {
            val rect = Rect()
            node.getBoundsInScreen(rect)
            list.add(
                UIElement(
                    element_id = resId.ifEmpty { "node_${list.size}" },
                    type = node.className?.toString()?.substringAfterLast(".") ?: "view",
                    text = text,
                    content_desc = desc,
                    resource_id = resId,
                    clickable = clickable,
                    bounds = listOf(rect.left, rect.top, rect.right, rect.bottom)
                )
            )
        }

        for (i in 0 until node.childCount) {
            traverseNode(node.getChild(i), list)
        }
    }

    fun performTap(x: Float, y: Float, callback: ((Boolean) -> Unit)? = null) {
        val path = Path().apply {
            moveTo(x, y)
        }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                callback?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                callback?.invoke(false)
            }
        }, null)
    }

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long = 300, callback: ((Boolean) -> Unit)? = null) {
        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                callback?.invoke(true)
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                callback?.invoke(false)
            }
        }, null)
    }

    fun performHome(): Boolean {
        return performGlobalAction(GLOBAL_ACTION_HOME)
    }

    fun performBack(): Boolean {
        return performGlobalAction(GLOBAL_ACTION_BACK)
    }

    fun performTypeText(text: String): Boolean {
        val rootNode = rootInActiveWindow ?: return false
        val focused = rootNode.findFocus(AccessibilityNodeInfo.FOCUS_INPUT) ?: return false
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        return focused.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
    }
}
