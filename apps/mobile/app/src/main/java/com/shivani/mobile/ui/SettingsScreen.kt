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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.shivani.mobile.ui.theme.*

@Composable
fun SettingsScreen() {
    var bridgePort by remember { mutableStateOf("8765") }
    var dataMinimization by remember { mutableStateOf(true) }
    var autoReconnect by remember { mutableStateOf(true) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkSlate)
            .padding(20.dp)
    ) {
        item {
            Text(
                text = "SETTINGS",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = AccentCyan
            )
            Text(
                text = "Bridge network and data privacy preferences",
                fontSize = 12.sp,
                color = TextMuted
            )
            Spacer(modifier = Modifier.height(20.dp))
        }

        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                colors = CardDefaults.cardColors(containerColor = SurfaceDark)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Data Minimization",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Text(
                        text = "Filters accessibility trees to transmit only target elements and minimizes data transfer across bridge.",
                        fontSize = 12.sp,
                        color = TextMuted
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Switch(
                        checked = dataMinimization,
                        onCheckedChange = { dataMinimization = it },
                        colors = SwitchDefaults.colors(checkedThumbColor = AccentCyan)
                    )
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
        }

        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                colors = CardDefaults.cardColors(containerColor = SurfaceDark)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Keepalive Heartbeat",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Text(
                        text = "Regularly reports connection status to laptop SHIVANI without background battery drain.",
                        fontSize = 12.sp,
                        color = TextMuted
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Switch(
                        checked = autoReconnect,
                        onCheckedChange = { autoReconnect = it },
                        colors = SwitchDefaults.colors(checkedThumbColor = AccentCyan)
                    )
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
        }

        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                colors = CardDefaults.cardColors(containerColor = SurfaceDark)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "About SHIVANI MOBILE",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(text = "Version: 0.1.0 (Phase 7 Build)", fontSize = 12.sp, color = TextMuted)
                    Text(text = "Security: Keystore Encrypted AES-256", fontSize = 12.sp, color = TextMuted)
                    Text(text = "Protocol: TLS/Authenticated WebSockets", fontSize = 12.sp, color = TextMuted)
                }
            }
        }
    }
}
