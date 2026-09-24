package com.shivani.mobile.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.shivani.mobile.security.KeyStoreManager
import com.shivani.mobile.ui.theme.*

@Composable
fun ConnectionScreen(onPairingSuccess: () -> Unit) {
    val context = LocalContext.current
    var pairingCode by remember { mutableStateOf("") }
    var laptopIp by remember { mutableStateOf("192.168.1.100") }
    var statusMessage by remember { mutableStateOf<String?>(null) }
    var isError by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkSlate)
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "DEVICE PAIRING",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = AccentCyan
        )
        Text(
            text = "Authenticate this phone with your SHIVANI desktop",
            fontSize = 12.sp,
            color = TextMuted
        )

        Spacer(modifier = Modifier.height(24.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Pair with this computer?",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "SHIVANI on your laptop will be granted authorized access to open apps, inspect visible UI, and assist you with tasks.",
                    fontSize = 13.sp,
                    color = TextMuted
                )

                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = laptopIp,
                    onValueChange = { laptopIp = it },
                    label = { Text("Laptop IP / Hostname", color = TextMuted) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = AccentCyan,
                        unfocusedBorderColor = BorderDark
                    )
                )

                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = pairingCode,
                    onValueChange = { if (it.length <= 6) pairingCode = it },
                    label = { Text("6-Digit Pairing Code", color = TextMuted) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = AccentCyan,
                        unfocusedBorderColor = BorderDark
                    )
                )

                Spacer(modifier = Modifier.height(20.dp))

                Button(
                    onClick = {
                        if (pairingCode.length == 6) {
                            // Save simulated cryptographic pairing token
                            val generatedToken = "tok_" + System.currentTimeMillis()
                            KeyStoreManager.savePairingData(
                                context,
                                deviceId = "shivani-android-001",
                                authToken = generatedToken,
                                laptopName = "Shivani Desktop ($laptopIp)"
                            )
                            statusMessage = "Pairing successful! Connected."
                            isError = false
                            onPairingSuccess()
                        } else {
                            statusMessage = "Please enter a valid 6-digit code."
                            isError = true
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentGreen),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(text = "Approve & Connect", color = DarkSlate, fontWeight = FontWeight.Bold)
                }
            }
        }

        if (statusMessage != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = statusMessage!!,
                color = if (isError) DangerRed else AccentGreen,
                fontSize = 13.sp
            )
        }
    }
}
