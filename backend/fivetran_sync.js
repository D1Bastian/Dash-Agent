// backend/fivetran_sync.js
// Placeholder for real-time data pipeline sync using Fivetran

export async function syncWithFivetran(payload) {
  try {
    const resp = await fetch(`${process.env.API_BASE}/sync/fivetran`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) throw new Error("Fivetran sync failed");
    const data = await resp.json();
    return data;
  } catch (e) {
    console.error("Fivetran sync error:", e);
    return null;
  }
}
