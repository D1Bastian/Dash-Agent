// backend/elastic_search.js
// Placeholder for querying Elastic partner API for enriched search results

export async function queryElastic(query) {
  try {
    const resp = await fetch(`${process.env.API_BASE}/search/elastic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    if (!resp.ok) throw new Error("Elastic query failed");
    const data = await resp.json();
    return data;
  } catch (e) {
    console.error("Elastic search error:", e);
    return null;
  }
}
