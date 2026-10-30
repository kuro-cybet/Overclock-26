
import crypto from "node:crypto";

const url =
  "https://pcmjjphqnjrebauyerdy.supabase.co/functions/v1/send-campusops-email";

const secret = process.env.CAMPUSOPS_WEBHOOK_SECRET;
const anonKey = process.env.SUPABASE_ANON_KEY;

if (!secret || !anonKey) {
  throw new Error("Missing required environment variables");
}

const payload = {
  event_type: "test_email",
  entity_code: "TEST-001",
  recipient_name: "CampusOps Test User",
};

const body = JSON.stringify(payload);
const timestamp = Math.floor(Date.now() / 1000).toString();

const signature = crypto
  .createHmac("sha256", secret)
  .update(`${timestamp}.${body}`)
  .digest("hex");

const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    apikey: anonKey,
    Authorization: `Bearer ${anonKey}`,
    "x-campusops-timestamp": timestamp,
    "x-campusops-signature": signature,
  },
  body,
});

console.log("HTTP Status:", response.status);
console.log("Response:", await response.text());
