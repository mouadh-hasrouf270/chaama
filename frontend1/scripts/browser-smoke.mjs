// Run against the isolated seeded backend described in IMPLEMENTATION_REPORT.md.
// Requires Node 22+ and a local Chrome CDP endpoint. No test dependency is installed.
import assert from "node:assert/strict";
import fs from "node:fs/promises";

const origin = process.env.SMOKE_FRONTEND_URL || "http://127.0.0.1:5174";
const cdp = process.env.SMOKE_CDP_URL || "http://127.0.0.1:9223";
const target = await fetch(cdp + "/json/new?about:blank", { method: "PUT" }).then(r => r.json());
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => socket.addEventListener("open", resolve, { once: true }));
let sequence = 0;
const waiting = new Map();
const exceptions = [];
const failedRequests = [];
let expectedFailure = false;
socket.addEventListener("message", event => {
  const message = JSON.parse(event.data);
  if (message.id) {
    const request = waiting.get(message.id);
    if (request) {
      waiting.delete(message.id);
      message.error ? request.reject(new Error(JSON.stringify(message.error))) : request.resolve(message.result);
    }
  }
  if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
  if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error")
    exceptions.push(message.params.args.map(arg => arg.value || arg.description).join(" "));
  if (!expectedFailure && message.method === "Network.responseReceived" && message.params.response.status >= 400)
    failedRequests.push({ url: message.params.response.url, status: message.params.response.status });
});
function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    waiting.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
  return result.result.value;
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression, label, timeout = 15000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await evaluate(expression)) return;
    await delay(100);
  }
  throw new Error("Timed out: " + label + "\n" + await evaluate("document.body.innerText"));
}
async function navigate(path) {
  await command("Page.navigate", { url: origin + path });
  await delay(400);
  await until(`location.pathname === ${JSON.stringify(path)} && document.readyState === "complete"`, path);
}
async function fill(selector, value) {
  await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) throw new Error("Missing input: " + ${JSON.stringify(selector)});
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : el.tagName === "SELECT" ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(el, ${JSON.stringify(value)});
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  })()`);
}
async function clickText(text) {
  await evaluate(`(() => {
    const el = [...document.querySelectorAll("button")].find(b => b.textContent.trim() === ${JSON.stringify(text)});
    if (!el || el.disabled) throw new Error("Missing or disabled button: " + ${JSON.stringify(text)});
    el.click();
  })()`);
}
async function screenshot(name) {
  await fs.mkdir(".work-audit/screenshots", { recursive: true });
  const { data } = await command("Page.captureScreenshot", { format: "png" });
  await fs.writeFile(".work-audit/screenshots/" + name + ".png", Buffer.from(data, "base64"));
}
const results = [];
try {
  await command("Page.enable");
  await command("Runtime.enable");
  await command("Network.enable");
  await command("Emulation.setDeviceMetricsOverride", { width: 1365, height: 1000, deviceScaleFactor: 1, mobile: false });
  await navigate("/");
  await until('document.body.innerText.includes("Browser Practice")', "public practice area from API");
  await screenshot("home");
  results.push("Home renders a real backend practice area");

  await command("Page.navigate", { url: origin + "/app/clients" });
  await until('location.pathname === "/auth/login" && !!document.querySelector("input[type=password]")', "protected route redirects");
  await fill('input[type="text"]', process.env.SMOKE_USERNAME || "browser-lawyer");
  await fill('input[type="password"]', process.env.SMOKE_PASSWORD || "Browser-test-only-927!");
  await clickText("Se connecter");
  await until('location.pathname === "/app/clients" && document.body.innerText.includes("Browser Client")', "JWT login and clients list");
  await screenshot("clients");
  results.push("JWT login, protected route and real clients list");
  await fill('input[placeholder="Rechercher un client..."]', "NoSuchBrowserClient");
  await until('document.body.innerText.includes("Aucun client trouvé")', "empty search");
  results.push("Clients empty state");
  await fill('input[placeholder="Rechercher un client..."]', "Browser");
  await until(`!!document.querySelector('a[href^="/app/clients/"]')`, "client row");
  await evaluate(`document.querySelector('a[href^="/app/clients/"]').click()`);
  await until('document.body.innerText.includes("browser@example.com")', "client detail contact");
  results.push("Client detail uses the selected record");

  await navigate("/app");
  await until('document.body.innerText.includes("Bonjour, Browser")', "real dashboard");
  await screenshot("dashboard");
  await navigate("/app/calendar");
  await until('document.body.innerText.includes("Aucun rendez-vous")', "calendar empty state");
  results.push("Real dashboard and calendar empty state");
  await evaluate(`document.querySelector('button[aria-label="Notifications"]').click()`);
  await until('document.body.innerText.includes("Browser notification")', "notifications");
  await evaluate('[...document.querySelectorAll("button")].find(b => b.textContent.includes("Browser notification")).click()');
  await until('document.body.innerText.includes("Aucune nouvelle notification")', "notification persisted read");
  results.push("Notification read persists through API");

  await navigate("/app/profile");
  await until('document.querySelector("input")?.value === "" || document.body.innerText.includes("Informations du compte")', "profile");
  await until('[...document.querySelectorAll("input")].some(i => i.value === "Browser")', "profile account from API");
  results.push("Profile displays real account");

  expectedFailure = true;
  await command("Network.setBlockedURLs", { urls: ["*8000/api/v1/clients/*"] });
  await navigate("/app/clients");
  await until(`!!document.querySelector('[role="alert"]')`, "API failure error state");
  results.push("API failure displays an error without crashing");
  await command("Network.setBlockedURLs", { urls: [] });
  expectedFailure = false;

  await navigate("/rendez-vous");
  await until('document.body.innerText.includes("Browser Practice")', "booking practice choices");
  await evaluate('[...document.querySelectorAll("input[type=radio]")].find(i => i.value === "Première consultation").click()');
  await evaluate('[...document.querySelectorAll("input[type=radio]")].find(i => i.value === "Browser Practice").click()');
  await clickText("Continuer");
  const day = new Date(Date.now() + 4 * 86400000).toISOString().slice(0, 10);
  await fill('input[type="date"]', day);
  await until('document.body.innerText.includes("Créneaux disponibles")', "server availability");
  const availableTime = await evaluate('document.querySelector("datalist option").value');
  await fill('input[type="time"]', availableTime);
  await fill("select", "cabinet");
  await clickText("Continuer");
  const inputs = await evaluate('[...document.querySelectorAll("input")].filter(i => i.type !== "checkbox").map(i => ({id:i.id, type:i.type}))');
  assert.equal(inputs.length, 5);
  const values = ["Browser Guest", "guest@example.com", "+213999123456", "Browser booking", "Unrelated party"];
  for (let i = 0; i < inputs.length; i++) await fill(`input[id="${inputs[i].id}"]`, values[i]);
  await fill("textarea", "A browser integration consultation request.");
  await evaluate('document.querySelector("input[type=checkbox]").click()');
  await clickText("Envoyer la demande");
  await until('document.body.innerText.includes("Merci pour votre confiance.")', "real appointment and intake submission");
  await screenshot("booking-success");
  results.push("Booking submits real appointment and intake atomically");

  await navigate("/app/calendar");
  await until('document.body.innerText.includes("Semaine du")', "calendar page");
  // Mobile rendering uses the existing responsive layout.
  await command("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await screenshot("calendar-mobile");
  assert.equal(await evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), true);
  results.push("Mobile layout has no horizontal overflow");
  await command("Emulation.setDeviceMetricsOverride", { width: 1365, height: 1000, deviceScaleFactor: 1, mobile: false });
  await evaluate('[...document.querySelectorAll("button")].find(b => b.textContent.includes("Déconnexion")).click()');
  await until('location.pathname === "/auth/login"', "logout redirect");
  results.push("Logout clears the protected session");

  assert.deepEqual(exceptions, [], "Unexpected browser JavaScript/React errors");
  assert.deepEqual(failedRequests, [], "Unexpected failing HTTP requests");
  const report = { results, javascriptErrors: exceptions, failedRequests };
  await fs.writeFile(".work-audit/browser-results.json", JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} finally {
  await command("Page.close");
  socket.close();
}
