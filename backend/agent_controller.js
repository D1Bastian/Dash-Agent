// backend/agent_controller.js
// Core autonomous navigation controller
// Uses Chrome DevTools plugin to drive a headless browser instance.
// Exposes simple REST endpoints for mission execution and status queries.

import express from "express";
import { chromium } from "playwright"; // Assuming Playwright is available via chrome-devtools-plugin
import { MongoClient } from "mongodb";
import { enqueueTelemetry } from "./dynatrace_observe.js"; // placeholder for Dynatrace telemetry helper

const router = express.Router();

// MongoDB connection (reuse existing connection if available)
let mongoClient;
async function getDb() {
  if (!mongoClient) {
    const uri = process.env.MONGO_URI;
    mongoClient = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });
    await mongoClient.connect();
  }
  return mongoClient.db();
}

// Helper to record a mission step
async function recordStep(userId, missionId, step) {
  const db = await getDb();
  await db.collection("missions").updateOne(
    { _id: missionId },
    { $push: { steps: { ...step, timestamp: new Date() } } },
    { upsert: true }
  );
}

// Simple DSL for navigation actions
async function runActions(page, actions) {
  for (const act of actions) {
    const { type, selector, value, timeout = 3000 } = act;
    if (type === "click") {
      await page.click(selector, { timeout });
    } else if (type === "type") {
      await page.fill(selector, value, { timeout });
    } else if (type === "wait") {
      await page.waitForTimeout(value);
    } else if (type === "goto") {
      await page.goto(selector, { waitUntil: "networkidle" });
    }
    // Additional actions can be added later.
  }
}

// POST /api/agent/run
router.post("/run", async (req, res) => {
  try {
    const { userId, missionId, description, actions, autonomous } = req.body;
    // Create a new mission document if not exists
    const db = await getDb();
    await db.collection("missions").updateOne(
      { _id: missionId },
      { $set: { userId, description, status: "running", createdAt: new Date() } },
      { upsert: true }
    );

    // Launch headless browser
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Execute actions
    await runActions(page, actions);
    await page.close();
    await context.close();
    await browser.close();

    // Update mission status
    await db.collection("missions").updateOne({ _id: missionId }, { $set: { status: "completed", completedAt: new Date() } });

    // Send telemetry to Dynatrace
    await enqueueTelemetry({ missionId, userId, status: "completed" });

    res.json({ success: true, missionId, status: "completed" });
  } catch (e) {
    console.error("Agent run error:", e);
    // Record failure in DB
    const { missionId, userId } = req.body;
    const db = await getDb();
    await db.collection("missions").updateOne({ _id: missionId }, { $set: { status: "error", error: e.message } });
    // Telemetry for error
    await enqueueTelemetry({ missionId, userId, status: "error", error: e.message });
    res.status(500).json({ success: false, error: e.message });
  }
});

// GET /api/agent/status/:missionId
router.get("/status/:missionId", async (req, res) => {
  const { missionId } = req.params;
  const db = await getDb();
  const mission = await db.collection("missions").findOne({ _id: missionId });
  if (!mission) return res.status(404).json({ error: "Mission not found" });
  res.json({ missionId, status: mission.status, steps: mission.steps || [] });
});

export default router;
