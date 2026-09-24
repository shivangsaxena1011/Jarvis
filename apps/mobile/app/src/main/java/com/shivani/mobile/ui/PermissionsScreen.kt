package com.shivani.mobile.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.shivani.mobile.permissions.PermissionManager
import com.shivani.mobile.ui.theme.*

@Composable
fun PermissionsScreen() {
    val context = LocalContext.current
    var isAccessibility by remember { mutableStateOf(PermissionManager.isAccessibilityEnabled(context)) }
    var isPhotos by remember { mutableStateOf(PermissionManager.isPhotosPermissionGranted(context)) }
    var isNotifs by remember { mutableStateOf(PermissionManager.isNotificationPermissionGranted(context)) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkSlate)
            .padding(20.dp)
    ) {
        item {
            Text(
                text = "PHONE PERMISSIONS",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = AccentCyan
            )
            Text(
                text = "Only grant permissions required for your workflow",
                fontSize = 12.sp,
                color = TextMuted
            )
            Spacer(modifier = Modifier.height(20.dp))
        }

        item {
            PermissionCard(
                title = "Accessibility Service",
                description = "Required to inspect visible UI nodes, click buttons, and execute actions when instructed by your voice or laptop agent.",
                isEnabled = isAccessibility,
                onConfigure = { PermissionManager.openAccessibilitySettings(context) }
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        item {
            PermissionCard(
                title = "Photos & Media",
                description = "Enables finding hackathon photos or screenshots to use in workflows (e.g. sharing an image to LinkedIn).",
                isEnabled = isPhotos,
                onConfigure = { PermissionManager.openApplicationDetailsSettings(context) }
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        item {
            PermissionCard(
                title = "Notifications",
                description = "Allows SHIVANI to summarize visible incoming notifications only when you explicitly ask.",
                isEnabled = isNotifs,
                onConfigure = { PermissionManager.openApplicationDetailsSettings(context) }
            )
        }
    }
}

@Composable
fun PermissionCard(
    title: String,
    description: String,
    isEnabled: Boolean,
    onConfigure: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = title, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
                Text(
                    text = if (isEnabled) "ENABLED" else "DISABLED",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (isEnabled) AccentGreen else DangerRed
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, fontSize = 12.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedButton(
                onClick = onConfigure,
                modifier = Modifier.align(Alignment.End),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = AccentCyan)
            ) {
                Text(text = if (isEnabled) "Configure" else "Enable")
            }
        }
    }
}
