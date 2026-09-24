package com.shivani.mobile.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val DarkSlate = Color(0xFF0F172A)
val SurfaceDark = Color(0xFF1E293B)
val BorderDark = Color(0xFF334155)
val AccentCyan = Color(0xFF38BDF8)
val AccentGreen = Color(0xFF34D399)
val TextPrimary = Color(0xFFF8FAFC)
val TextMuted = Color(0xFF94A3B8)
val DangerRed = Color(0xFFF87171)

private val DarkColorScheme = darkColorScheme(
    primary = AccentCyan,
    secondary = AccentGreen,
    background = DarkSlate,
    surface = SurfaceDark,
    onPrimary = Color.Black,
    onSecondary = Color.Black,
    onBackground = TextPrimary,
    onSurface = TextPrimary
)

@Composable
fun ShivaniMobileTheme(
    darkTheme: Boolean = true, // Always enforce dark-first aesthetic
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
