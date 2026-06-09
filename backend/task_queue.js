// backend/task_queue.js
// Simple BullMQ task queue that processes autonomous missions by calling the agent controller.

import { Queue, Worker, QueueScheduler, FlowProducer } from "bullmq";
import IORedis from "ioredis";
import fetch from "node-fetch"; // for calling internal endpoint

const connection = new IORedis(process.env.REDIS_URL || "redis://127.0.0.1:6379");

// Queue for agent missions
export const agentQueue = new Queue("agent-tasks", { connection });
export const agentScheduler = new QueueScheduler("agent-tasks", { connection });

// Worker that runs the mission by invoking the local agent controller endpoint
const agentWorker = new Worker(
  "agent-tasks",
  async (job) => {
    const { payload } = job.data; // payload contains mission fields
    // Call the internal agent controller directly via HTTP (assuming same process runs on same host)
    const resp = await fetch(`${process.env.API_BASE || "http://127.0.0.1:8000"}/api/agent/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const err = await resp.text();
      throw new Error(`Agent run failed: ${err}`);
    }
    return await resp.json();
  },
  { connection, concurrency: 2 }
);

agentWorker.on("completed", (job, result) => {
  console.log(`✅ Mission ${job.id} completed`, result);
});

agentWorker.on("failed", (job, err) => {
  console.error(`❌ Mission ${job.id} failed`, err);
});

export default { agentQueue, agentWorker };
