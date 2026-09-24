package com.shivani.mobile.bridge

import kotlinx.serialization.Serializable

@Serializable
data class CommandRequest(
    val request_id: String,
    val device_id: String,
    val action: String,
    val parameters: Map<String, String> = emptyMap(),
    val timestamp: Double = 0.0
)

@Serializable
data class CommandResponse(
    val request_id: String,
    val device_id: String,
    val success: Boolean,
    val result: Map<String, String> = emptyMap(),
    val error: String? = null,
    val execution_time_ms: Double = 0.0
)

@Serializable
data class UIElement(
    val element_id: String,
    val type: String,
    val text: String = "",
    val content_desc: String = "",
    val resource_id: String = "",
    val clickable: Boolean = false,
    val bounds: List<Int> = listOf(0, 0, 0, 0)
)

@Serializable
data class VisibleObservation(
    val package_name: String,
    val activity_name: String,
    val elements: List<UIElement> = emptyList(),
    val timestamp: Double = 0.0
)
