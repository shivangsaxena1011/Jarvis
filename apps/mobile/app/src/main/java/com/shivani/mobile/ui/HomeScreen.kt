package com.shivani.mobile.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.shivani.mobile.device.DeviceInfoProvider
import com.shivani.mobile.security.KeyStoreManager
import com.shivani.mobile.storage.ActivityLogger
import com.shivani.mobile.ui.theme.*

@Composable
fun HomeScreen(
    onNavigateToConnection: () -> Unit,
    onNavigateToPermissions: () -> Unit
) {
    val context = LocalContext.current
    var isConnected by remember { mutableStateOf(KeyStoreManager.getAuthToken(context) != null) }
    val laptopName = remember { KeyStoreManager.getLaptopName(context) }
    val batteryLevel = remember { DeviceInfoProvider.getBatteryLevel(context) }
    val recentActivities = remember { ActivityLogger.getRecentActivities() }
    val lastAction = recentActivities.firstOrNull()?.action ?: "No commands executed yet"

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkSlate)
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Header
        Text(
            text = "SHIVANI MOBILE",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = AccentCyan,
            letterSpacing = 2.sp
        )
        Text(
            text = "Autonomous Companion Node",
            fontSize = 12.sp,
            color = TextMuted
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Device Status Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "DEVICE STATUS",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextMuted
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(if (isConnected) AccentGreen else DangerRed)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = if (isConnected) "Connected" else "Disconnected",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isConnected) AccentGreen else DangerRed
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                Divider(color = BorderDark, thickness = 1.dp)
                Spacer(modifier = Modifier.height(16.dp))

                Text(text = "Paired Laptop:", fontSize = 12.sp, color = TextMuted)
                Text(
                    text = laptopName,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium,
                    color = TextPrimary
                )

                Spacer(modifier = Modifier.height(12.dp))

                Text(text = "Last Command:", fontSize = 12.sp, color = TextMuted)
                Text(
                    text = lastAction,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace,
                    color = AccentCyan
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Battery: $batteryLevel%", fontSize = 12.sp, color = TextMuted)
                    Text(text = "Bridge Port: 8765", fontSize = 12.sp, color = TextMuted)
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Quick Controls
        if (isConnected) {
            Button(
                onClick = {
                    KeyStoreManager.clearPairing(context)
                    isConnected = false
                },
                colors = ButtonDefaults.buttonColors(containerColor = SurfaceDark),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, DangerRed, RoundedCornerShape(8.dp))
            ) {
                Text(text = "Disconnect Device", color = DangerRed)
            }
        } else {
            Button(
                onClick = onNavigateToConnection,
                colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(text = "Pair with Computer", color = DarkSlate, fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedButton(
            onClick = onNavigateToPermissions,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = AccentCyan),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(8.dp))
        ) {
            Text(text = "Check Permissions")
        }
    }
}
