
/**
 * CampusOps Gmail Notification Service
 * Supabase Edge Function: send-campusops-email
 *
 * Provider: Google Gmail API
 * Authentication: Google OAuth 2.0 Refresh Token
 * Backend authentication: HMAC-SHA256
 */

// ==================================================
// 1. CONFIGURATION
// ==================================================

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-campusops-timestamp, x-campusops-signature",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const encoder = new TextEncoder();

// ==================================================
// 2. APPROVED NOTIFICATION EVENTS
// ==================================================

const ALLOWED_EVENTS = [
  "report_received",
  "report_correlated",
  "booking_confirmed",
  "exam_booking_relocated",
  "work_order_assigned",
  "work_order_reassigned",
  "incident_resolved",
  "approval_requested",
  "approval_decided",
  "incident_sla_warning",
  "incident_sla_breached",
  "custom_email",
  "test_email",
] as const;

type EventType = typeof ALLOWED_EVENTS[number];

interface EmailPayload {
  event_type: EventType;
  entity_code: string;
  recipient_name?: string;
  recipient_email?: string;
  subject?: string;
  body?: string;
}

// ==================================================
// 3. RESPONSE HELPERS
// ==================================================

function jsonResponse(
  data: unknown,
  status = 200,
): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
}

// ==================================================
// 4. INPUT VALIDATION
// ==================================================

function safeText(
  value: unknown,
  fallback = "",
): string {
  if (typeof value !== "string") {
    return fallback;
  }

  return value
    .replace(/[\r\n]/g, " ")
    .trim()
    .slice(0, 200);
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Demo catch-all copy recipient.
 *
 * Every notification is still addressed to its real recipient, but a copy is
 * CC'd to this inbox so the demo can show real mail without relying on the
 * synthetic @campusops.edu addresses.
 *
 * Resolution order: CAMPUSOPS_ALWAYS_CC, then CAMPUSOPS_TEST_RECIPIENT.
 * Returns null when unset/invalid or when it is the primary recipient.
 */
function resolveCopyRecipient(recipient: string): string | null {
  const configured = (
    Deno.env.get("CAMPUSOPS_ALWAYS_CC") ??
    Deno.env.get("CAMPUSOPS_TEST_RECIPIENT") ??
    ""
  ).trim();

  if (!configured || !isValidEmail(configured)) {
    return null;
  }

  if (configured.toLowerCase() === recipient.toLowerCase()) {
    return null;
  }

  return configured;
}

function safeMultilineText(
  value: unknown,
  maxLength = 20_000,
): string {
  if (typeof value !== "string") {
    return "";
  }

  return value
    .replace(/\r\n?/g, "\n")
    .trim()
    .slice(0, maxLength);
}

function isAllowedEvent(value: unknown): value is EventType {
  return (
    typeof value === "string" &&
    ALLOWED_EVENTS.includes(value as EventType)
  );
}

// ==================================================
// 5. HMAC-SHA256 SIGNATURE VERIFICATION
// ==================================================

function toHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function constantTimeEqual(
  a: string,
  b: string,
): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;

  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}

async function verifySignature(
  timestamp: string,
  rawBody: string,
  signature: string,
): Promise<boolean> {
  const secret = Deno.env.get("CAMPUSOPS_WEBHOOK_SECRET");

  if (!secret || !timestamp || !signature) {
    return false;
  }

  const timestampNumber = Number(timestamp);

  if (!Number.isFinite(timestampNumber)) {
    return false;
  }

  // Reject requests older than five minutes.
  if (
    Math.abs(Date.now() / 1000 - timestampNumber) > 300
  ) {
    return false;
  }

  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    {
      name: "HMAC",
      hash: "SHA-256",
    },
    false,
    ["sign"],
  );

  const message = `${timestamp}.${rawBody}`;

  const signatureBuffer = await crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(message),
  );

  const expectedSignature = toHex(
    new Uint8Array(signatureBuffer),
  );

  return constantTimeEqual(
    expectedSignature,
    signature.toLowerCase(),
  );
}

// ==================================================
// 6. BASE64 AND MIME HELPERS
// ==================================================

function base64Utf8(value: string): string {
  const bytes = encoder.encode(value);

  let binary = "";

  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(
      ...bytes.subarray(i, i + 0x8000),
    );
  }

  return btoa(binary);
}

function base64Url(value: string): string {
  return base64Utf8(value)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function wrapBase64(value: string): string {
  return value.match(/.{1,76}/g)?.join("\r\n") ?? value;
}

// ==================================================
// 7. CAMPUSOPS EMAIL TEMPLATES
// ==================================================

function createEmail(
  eventType: EventType,
  recipientName: string,
  entityCode: string,
): { subject: string; body: string } {
  const greeting = recipientName
    ? `Hello ${recipientName},`
    : "Hello,";

  const templates: Record<
    EventType,
    { subject: string; body: string }
  > = {
    report_received: {
      subject: `Report received - ${entityCode}`,
      body:
        "Your report has been successfully received by CampusOps.",
    },

    report_correlated: {
      subject: `Related report update - ${entityCode}`,
      body:
        "Your report has been linked with a related incident in CampusOps.",
    },

    booking_confirmed: {
      subject: `Booking confirmed - ${entityCode}`,
      body:
        "Your room booking has been confirmed.",
    },

    exam_booking_relocated: {
      subject: `Exam booking relocated - ${entityCode}`,
      body:
        "Your exam room booking has been relocated. Please check CampusOps for updated details.",
    },

    work_order_assigned: {
      subject: `Work order assigned - ${entityCode}`,
      body:
        "A new work order has been assigned to you.",
    },

    work_order_reassigned: {
      subject: `Work order reassigned - ${entityCode}`,
      body:
        "A work order assignment has been updated.",
    },

    incident_resolved: {
      subject: `Incident resolved - ${entityCode}`,
      body:
        "The reported incident has been marked as resolved.",
    },

    approval_requested: {
      subject: `Approval required - ${entityCode}`,
      body:
        "An item requiring your approval has been submitted.",
    },

    approval_decided: {
      subject: `Approval update - ${entityCode}`,
      body:
        "A decision has been recorded for your approval request.",
    },

    incident_sla_warning: {
      subject: `SLA warning - ${entityCode}`,
      body:
        "An incident is approaching its configured SLA deadline. Please review it.",
    },

    incident_sla_breached: {
      subject: `SLA breached - ${entityCode}`,
      body:
        "An incident has exceeded its configured SLA deadline. Please take the required action.",
    },

    custom_email: {
      // Replaced by the caller-supplied subject/body in the request handler.
      subject: `CampusOps notification - ${entityCode}`,
      body:
        "You have a new CampusOps notification.",
    },

    test_email: {
      subject: "CampusOps Gmail integration test",
      body:
        "Congratulations! Your CampusOps Supabase Edge Function successfully sent an email using the Gmail API.",
    },
  };

  const template = templates[eventType];

  return {
    subject: template.subject,
    body: [
      greeting,
      "",
      template.body,
      "",
      `Reference: ${entityCode}`,
      "",
      "Regards,",
      "CampusOps Notification System",
    ].join("\n"),
  };
}

// ==================================================
// 8. GOOGLE OAUTH ACCESS TOKEN
// ==================================================

async function getGoogleAccessToken(): Promise<string> {
  const clientId = Deno.env.get("GOOGLE_CLIENT_ID");
  const clientSecret = Deno.env.get("GOOGLE_CLIENT_SECRET");
  const refreshToken = Deno.env.get("GOOGLE_REFRESH_TOKEN");

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error(
      "Google OAuth credentials are not configured.",
    );
  }

  const response = await fetch(
    "https://oauth2.googleapis.com/token",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      }),
    },
  );

  const responseText = await response.text();

  let data: Record<string, unknown>;

  try {
    data = JSON.parse(responseText);
  } catch {
    console.error("GOOGLE_OAUTH_INVALID_RESPONSE");

    throw new Error(
      "Google OAuth returned an invalid response.",
    );
  }

  if (
    !response.ok ||
    typeof data.access_token !== "string"
  ) {
    console.error(
      "GOOGLE_OAUTH_FAILURE",
      JSON.stringify({
        status: response.status,
        error: data.error ?? "unknown_error",
        description:
          data.error_description ?? "No description",
      }),
    );

    throw new Error(
      "Google OAuth token refresh failed.",
    );
  }

  return data.access_token;
}

// ==================================================
// 9. SEND EMAIL USING GMAIL API
// ==================================================

async function sendGmail(
  recipient: string,
  subject: string,
  body: string,
): Promise<string | null> {
  const sender = Deno.env.get("GOOGLE_SENDER_EMAIL");

  if (!sender || !isValidEmail(sender)) {
    throw new Error(
      "GOOGLE_SENDER_EMAIL is missing or invalid.",
    );
  }

  // Obtain access token exactly once.
  const accessToken = await getGoogleAccessToken();

  // Keep the real recipient in To: and CC the configured demo inbox.
  const copyRecipient = resolveCopyRecipient(recipient);

  // Construct RFC 2822 MIME email.
  const mimeHeaders = [
    `From: CampusOps <${sender}>`,
    `To: ${recipient}`,
  ];

  if (copyRecipient) {
    mimeHeaders.push(`Cc: ${copyRecipient}`);
  }

  mimeHeaders.push(
    `Subject: =?UTF-8?B?${base64Utf8(subject)}?=`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrapBase64(base64Utf8(body)),
  );

  const mimeMessage = mimeHeaders.join("\r\n");

  const encodedMessage = base64Url(mimeMessage);

  // Send the email through Gmail API.
  const gmailResponse = await fetch(
    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        raw: encodedMessage,
      }),
    },
  );

  const responseText = await gmailResponse.text();

  let result: Record<string, unknown>;

  try {
    result = JSON.parse(responseText);
  } catch {
    console.error(
      "GMAIL_API_INVALID_RESPONSE",
      JSON.stringify({
        status: gmailResponse.status,
      }),
    );

    throw new Error(
      "Gmail returned an invalid response.",
    );
  }

  // Log Google's actual API error without exposing tokens.
  if (!gmailResponse.ok) {
    console.error(
      "GMAIL_API_FAILURE",
      JSON.stringify({
        status: gmailResponse.status,
        google_error: result,
      }),
    );

    throw new Error(
      `Gmail API request failed with HTTP ${gmailResponse.status}.`,
    );
  }

  console.log(
    "GMAIL_API_SUCCESS",
    JSON.stringify({
      message_id: result.id ?? null,
      thread_id: result.threadId ?? null,
      cc: copyRecipient,
    }),
  );

  return typeof result.id === "string"
    ? result.id
    : null;
}

// ==================================================
// 10. MAIN SUPABASE EDGE FUNCTION
// ==================================================

Deno.serve(async (req: Request): Promise<Response> => {
  // CORS preflight.
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: corsHeaders,
    });
  }

  if (req.method !== "POST") {
    return jsonResponse(
      { error: "Method not allowed." },
      405,
    );
  }

  try {
    // Read exact request body for signature verification.
    const rawBody = await req.text();

    if (rawBody.length > 32_000) {
      return jsonResponse(
        { error: "Request body is too large." },
        413,
      );
    }

    // ----------------------------------------------
    // 10.1 VERIFY BACKEND SIGNATURE
    // ----------------------------------------------

    const timestamp =
      req.headers.get("x-campusops-timestamp") ?? "";

    const signature =
      req.headers.get("x-campusops-signature") ?? "";

    const validSignature = await verifySignature(
      timestamp,
      rawBody,
      signature,
    );

    if (!validSignature) {
      return jsonResponse(
        { error: "Invalid or expired request signature." },
        401,
      );
    }

    // ----------------------------------------------
    // 10.2 PARSE REQUEST BODY
    // ----------------------------------------------

    let payload: EmailPayload;

    try {
      payload = JSON.parse(rawBody);
    } catch {
      return jsonResponse(
        { error: "Invalid JSON request body." },
        400,
      );
    }

    if (
      !payload ||
      typeof payload !== "object" ||
      Array.isArray(payload)
    ) {
      return jsonResponse(
        { error: "Invalid request payload." },
        400,
      );
    }

    // ----------------------------------------------
    // 10.3 VALIDATE EVENT TYPE
    // ----------------------------------------------

    if (!isAllowedEvent(payload.event_type)) {
      return jsonResponse(
        { error: "Unsupported notification event." },
        400,
      );
    }

    const eventType = payload.event_type;

    const entityCode = safeText(
      payload.entity_code,
      eventType === "test_email" ? "TEST-001" : "",
    );

    const recipientName = safeText(
      payload.recipient_name,
    );

    if (!entityCode) {
      return jsonResponse(
        { error: "entity_code is required." },
        400,
      );
    }

    // ----------------------------------------------
    // 10.4 RESOLVE RECIPIENT
    // ----------------------------------------------

    let recipientEmail: string;

    if (eventType === "test_email") {
      // Test email is restricted to a fixed recipient.
      const testRecipient = Deno.env.get(
        "CAMPUSOPS_TEST_RECIPIENT",
      );

      if (
        !testRecipient ||
        !isValidEmail(testRecipient)
      ) {
        return jsonResponse(
          {
            error:
              "Test recipient is not configured correctly.",
          },
          500,
        );
      }

      recipientEmail = testRecipient;
    } else {
      // Normal events require a trusted signed backend request.
      recipientEmail = safeText(
        payload.recipient_email,
      );

      if (!isValidEmail(recipientEmail)) {
        return jsonResponse(
          { error: "A valid recipient email is required." },
          400,
        );
      }
    }

    // ----------------------------------------------
    // 10.5 BUILD EMAIL
    // ----------------------------------------------

    const email = createEmail(
      eventType,
      recipientName,
      entityCode,
    );

    // The backend outbox sends the exact subject/body it queued.
    if (eventType === "custom_email") {
      const customSubject = safeText(payload.subject);
      const customBody = safeMultilineText(payload.body);

      if (!customSubject || !customBody) {
        return jsonResponse(
          {
            error:
              "custom_email requires a subject and body.",
          },
          400,
        );
      }

      email.subject = customSubject;
      email.body = customBody;
    }

    // ----------------------------------------------
    // 10.6 SEND EMAIL
    // ----------------------------------------------

    const gmailMessageId = await sendGmail(
      recipientEmail,
      email.subject,
      email.body,
    );

    // ----------------------------------------------
    // 10.7 SUCCESS RESPONSE
    // ----------------------------------------------

    console.log(
      "CAMPUSOPS_EMAIL_SENT",
      JSON.stringify({
        event_type: eventType,
        entity_code: entityCode,
        gmail_message_id: gmailMessageId,
      }),
    );

    return jsonResponse({
      success: true,
      message: "Email sent successfully.",
      event_type: eventType,
      entity_code: entityCode,
      gmail_message_id: gmailMessageId,
    });
  } catch (error) {
    console.error(
      "CAMPUSOPS_EMAIL_FAILURE",
      JSON.stringify({
        message:
          error instanceof Error
            ? error.message
            : "Unknown error",
      }),
    );

    return jsonResponse(
      {
        success: false,
        error:
          "Email delivery failed. Check function logs.",
      },
      500,
    );
  }
});
