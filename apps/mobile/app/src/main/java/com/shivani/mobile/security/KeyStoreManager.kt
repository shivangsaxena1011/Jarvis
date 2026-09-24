package com.shivani.mobile.security

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys

object KeyStoreManager {
    private const val PREFS_NAME = "shivani_secure_keys"
    private const val KEY_DEVICE_ID = "device_id"
    private const val KEY_AUTH_TOKEN = "auth_token"
    private const val KEY_LAPTOP_NAME = "laptop_name"

    private fun getPrefs(context: Context): SharedPreferences {
        val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
        return EncryptedSharedPreferences.create(
            PREFS_NAME,
            masterKeyAlias,
            context,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun savePairingData(context: Context, deviceId: String, authToken: String, laptopName: String) {
        getPrefs(context).edit().apply {
            putString(KEY_DEVICE_ID, deviceId)
            putString(KEY_AUTH_TOKEN, authToken)
            putString(KEY_LAPTOP_NAME, laptopName)
            apply()
        }
    }

    fun getDeviceId(context: Context): String {
        return getPrefs(context).getString(KEY_DEVICE_ID, "shivani-android-001") ?: "shivani-android-001"
    }

    fun getAuthToken(context: Context): String? {
        return getPrefs(context).getString(KEY_AUTH_TOKEN, null)
    }

    fun getLaptopName(context: Context): String {
        return getPrefs(context).getString(KEY_LAPTOP_NAME, "Shivani Desktop") ?: "Shivani Desktop"
    }

    fun clearPairing(context: Context) {
        getPrefs(context).edit().clear().apply()
    }
}
