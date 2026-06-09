// backend/vault_load.js
// Placeholder for loading user-specific memory from MongoDB Mission Vault

export async function loadUserVault(userId) {
  try {
    const resp = await fetch(`${process.env.API_BASE}/vault/load`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId })
    });
    if (!resp.ok) throw new Error("Vault load failed");
    const data = await resp.json();
    return data; // Expected to contain user memory/prefs
  } catch (e) {
    console.error("Vault load error:", e);
    return null;
  }
}
