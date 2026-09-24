package com.shivani.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.shivani.mobile.service.ShivaniDeviceService
import com.shivani.mobile.ui.*
import com.shivani.mobile.ui.theme.DarkSlate
import com.shivani.mobile.ui.theme.ShivaniMobileTheme
import com.shivani.mobile.ui.theme.SurfaceDark

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start device bridge service
        ShivaniDeviceService.startService(this)

        setContent {
            ShivaniMobileTheme {
                val navController = rememberNavController()
                var currentTab by remember { mutableStateOf("home") }

                Scaffold(
                    bottomBar = {
                        NavigationBar(containerColor = SurfaceDark) {
                            NavigationBarItem(
                                selected = currentTab == "home",
                                onClick = {
                                    currentTab = "home"
                                    navController.navigate("home")
                                },
                                label = { Text("Home") },
                                icon = { Text("📱") }
                            )
                            NavigationBarItem(
                                selected = currentTab == "connection",
                                onClick = {
                                    currentTab = "connection"
                                    navController.navigate("connection")
                                },
                                label = { Text("Pair") },
                                icon = { Text("🔗") }
                            )
                            NavigationBarItem(
                                selected = currentTab == "permissions",
                                onClick = {
                                    currentTab = "permissions"
                                    navController.navigate("permissions")
                                },
                                label = { Text("Perms") },
                                icon = { Text("🛡️") }
                            )
                            NavigationBarItem(
                                selected = currentTab == "activity",
                                onClick = {
                                    currentTab = "activity"
                                    navController.navigate("activity")
                                },
                                label = { Text("Logs") },
                                icon = { Text("📜") }
                            )
                            NavigationBarItem(
                                selected = currentTab == "devices",
                                onClick = {
                                    currentTab = "devices"
                                    navController.navigate("devices")
                                },
                                label = { Text("Devices") },
                                icon = { Text("💻") }
                            )
                            NavigationBarItem(
                                selected = currentTab == "settings",
                                onClick = {
                                    currentTab = "settings"
                                    navController.navigate("settings")
                                },
                                label = { Text("Settings") },
                                icon = { Text("⚙️") }
                            )
                        }
                    },
                    containerColor = DarkSlate
                ) { innerPadding ->
                    NavHost(
                        navController = navController,
                        startDestination = "home",
                        modifier = Modifier.padding(innerPadding)
                    ) {
                        composable("home") {
                            HomeScreen(
                                onNavigateToConnection = {
                                    currentTab = "connection"
                                    navController.navigate("connection")
                                },
                                onNavigateToPermissions = {
                                    currentTab = "permissions"
                                    navController.navigate("permissions")
                                }
                            )
                        }
                        composable("connection") {
                            ConnectionScreen(
                                onPairingSuccess = {
                                    currentTab = "home"
                                    navController.navigate("home")
                                }
                            )
                        }
                        composable("permissions") {
                            PermissionsScreen()
                        }
                        composable("activity") {
                            ActivityScreen()
                        }
                        composable("devices") {
                            DevicesScreen()
                        }
                        composable("settings") {
                            SettingsScreen()
                        }
                    }
                }
            }
        }
    }
}
