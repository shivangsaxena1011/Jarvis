package com.shivani.mobile.storage

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class ActivityLogEntry(
    val id: String,
    val timeFormatted: String,
    val action: String,
    val details: String,
    val success: Boolean
)

object ActivityLogger {
    private val entries = mutableListOf<ActivityLogEntry>()
    private val dateFormat = SimpleDateFormat("hh:mm a", Locale.getDefault())

    fun log(action: String, details: String, success: Boolean = true) {
        val entry = ActivityLogEntry(
            id = System.currentTimeMillis().toString(),
            timeFormatted = dateFormat.format(Date()),
            action = action,
            details = details,
            success = success
        )
        synchronized(entries) {
            entries.add(0, entry)
            if (entries.size > 100) {
                entries.removeAt(entries.size - 1)
            }
        }
    }

    fun getRecentActivities(): List<ActivityLogEntry> {
        synchronized(entries) {
            return entries.toList()
        }
    }
}
