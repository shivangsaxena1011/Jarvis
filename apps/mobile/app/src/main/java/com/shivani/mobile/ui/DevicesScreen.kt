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
import com.shivani.mobile.security.KeyStoreManager
import com.shivani.mobile.ui.theme.*

@Composable
fun DevicesScreen() {
    val context = LocalContext.current
    val pairedLaptop = remember { KeyStoreManager.getLaptopName(context) }
    val authToken = remember { KeyStoreManager.getAuthToken(context) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkSlate)
            .padding(20.dp)
    ) {
        item {
            Text(
                text = "PAIRED DEVICES",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = AccentCyan
            )
            Text(
                text = "Computers authorized to connect with this phone",
                fontSize = 12.sp,
                color = TextMuted
            )
            Spacer(modifier = Modifier.height(20.dp))
        }

        if (authToken == null) {
            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                    colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                ) {
                    Text(
                        text = "No computers currently paired. Use the Connection screen to pair with your laptop.",
                        fontSize = 13.sp,
                        color = TextMuted,
                        modifier = Modifier.padding(20.dp)
                    )
                }
            }
        } else {
            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                    colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = pairedLaptop,
                                fontSize = 15.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Authenticated via Keystore • Active",
                                fontSize = 12.sp,
                                color = AccentGreen
                            )
                        }
                        TextButton(
                            onClick = {
                                KeyStoreManager.clearPairing(context)
                            }
                        ) {
                            Text(text = "Revoke", color = DangerRed)
                        }
                    }
                }
            }
        }
    }
}
