// Run ONLY against a disposable backend database with a trusted staff fixture.
// SMOKE_FRONTEND_URL, SMOKE_API_URL, SMOKE_CDP_URL, SMOKE_USERNAME and
// SMOKE_PASSWORD must be supplied. Uses Chrome CDP and Node's built-in WebSocket.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const required = ['SMOKE_FRONTEND_URL', 'SMOKE_API_URL', 'SMOKE_CDP_URL', 'SMOKE_USERNAME', 'SMOKE_PASSWORD'];
for (const key of required) assert.ok(process.env[key], `Missing ${key}; use an isolated test database.`);
const origin = process.env.SMOKE_FRONTEND_URL;
const api = process.env.SMOKE_API_URL;
const target = await fetch(process.env.SMOKE_CDP_URL + '/json/new?about:blank', { method: 'PUT' }).then(r => r.json());
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => socket.addEventListener('open', resolve, { once: true }));
let sequence = 0;
const pending = new Map();
const exceptions = [];
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
  }
  if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
});
function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression, label) {
  const end = Date.now() + 15000;
  while (Date.now() < end) {
    if (await evaluate(expression)) return;
    await delay(100);
  }
  throw new Error(`${label}\n${await evaluate('document.body.innerText')}`);
}
async function navigate(route) {
  await command('Page.navigate', { url: origin + route });
  await until(`location.pathname === ${JSON.stringify(route)} && document.readyState === 'complete'`, route);
}
async function click(text) {
  await evaluate(`(() => {
    const button = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(text)});
    if (!button || button.disabled) throw new Error('Missing or disabled: ' + ${JSON.stringify(text)});
    button.click();
  })()`);
}
async function fill(selector, value) {
  await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) throw new Error('Missing input: ' + ${JSON.stringify(selector)});
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, ${JSON.stringify(value)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  })()`);
}
async function screenshot(name) {
  const directory = path.join(os.tmpdir(), 'ch2ma-booking-check', 'screenshots');
  await fs.mkdir(directory, { recursive: true });
  const result = await command('Page.captureScreenshot', { format: 'png' });
  await fs.writeFile(path.join(directory, name + '.png'), Buffer.from(result.data, 'base64'));
}
try {
  await command('Page.enable');
  await command('Runtime.enable');
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  const config = await fetch(api + '/v1/public/booking-config/').then(r => r.json());
  const areas = await fetch(api + '/v1/public/practice-areas/').then(r => r.json());
  const area = areas[0];
  let date = config.min_date;
  let slots = [];
  for (let offset = 0; offset < 10; offset++) {
    const day = new Date(config.min_date + 'T12:00:00Z');
    day.setUTCDate(day.getUTCDate() + offset);
    date = day.toISOString().slice(0, 10);
    slots = await fetch(`${api}/v1/appointments/availability/?date=${date}&specialty=${area.slug}`).then(r => r.json());
    if (slots.length >= 2) break;
  }
  assert.ok(slots.length >= 2);
  await navigate('/rendez-vous');
  await until('document.querySelectorAll("input[type=radio]").length > 3', 'Practice choices loaded');
  await evaluate('document.querySelector("input[type=radio]").click()');
  await evaluate(`[...document.querySelectorAll('input[type=radio]')].find(el => el.value === ${JSON.stringify(area.name)}).click()`);
  await click('Continuer');
  await until(`!!document.querySelector('section[aria-label="Calendrier de réservation"]')`, 'Calendar visible');
  if (date.slice(0, 7) !== config.min_date.slice(0, 7)) await evaluate(`document.querySelector('button[aria-label="Mois suivant"]').click()`);
  await evaluate(`document.querySelector('button[aria-label="${date}"]').click()`);
  const slotTime = slots[0].start_at.slice(11, 16);
  await until(`document.body.innerText.includes(${JSON.stringify(slotTime)})`, 'Available slots loaded');
  await screenshot('booking-calendar-mobile');
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'), true, 'No mobile horizontal overflow');
  await click(slotTime);
  await fill('select', 'telephone');
  await click('Continuer');
  await until('!!document.querySelector("input[type=email]")', 'Contact step');
  await click('Envoyer la demande');
  await until('document.body.innerText.includes("Indiquez votre nom complet.")', 'Empty submit shows field errors instead of a silently disabled button');
  assert.equal(await evaluate('document.activeElement.name'), 'name', 'Focus moves to first invalid field');
  await fill('input[placeholder="Votre nom"]', 'Browser Booking');
  await fill('input[type=email]', 'browser-booking@example.com');
  await fill('input[type=tel]', '+213555123456');
  await fill('input[placeholder="En quelques mots"]', 'Browser consultation');
  await fill('textarea', 'Court');
  await click('Envoyer la demande');
  assert.equal(await evaluate('document.activeElement.name'), 'details', 'Short description receives focus');
  assert.ok(await evaluate('document.body.innerText.includes("au moins 10 caractères")'), 'Description requirement is visible');
  await screenshot('booking-validation-mobile');
  await fill('textarea', 'Une consultation de test via le navigateur.');
  await click('Envoyer la demande');
  assert.equal(await evaluate('document.activeElement.name'), 'consent', 'Missing consent explained');
  await evaluate('document.querySelector("#booking-consent").click()');
  await command('Network.enable');
  await command('Network.setBlockedURLs', { urls: [api + '/v1/public/bookings/'] });
  await click('Envoyer la demande');
  await until('!!document.querySelector("#booking-submit-error")', 'Network error shown at the submit button');
  assert.equal(await evaluate('document.querySelector("input[type=email]").value'), 'browser-booking@example.com', 'Network failure retains contact data');
  await command('Network.setBlockedURLs', { urls: [] });
  // Simulate another visitor taking the selected slot before this form submits.
  const rival = await fetch(api + '/v1/public/bookings/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
    practice_area: area.id, start_at: slots[0].start_at, consultation_type: 'OFFICE', full_name: 'Competing Booking',
    email: 'competing@example.com', phone: '+213555123456', legal_topic: 'Test', description: 'Concurrent browser test request', consent: true,
  }) });
  assert.equal(rival.status, 201);
  await click('Envoyer la demande');
  await until(`!!document.querySelector('section[aria-label="Calendrier de réservation"]') && !!document.querySelector('[role=alert]')`, 'Conflict returns to calendar');
  await until(`![...document.querySelectorAll('button')].some(b => b.textContent.trim() === ${JSON.stringify(slotTime)})`, 'Taken slot disappears');
  await click(slots[1].start_at.slice(11, 16));
  await click('Continuer');
  assert.equal(await evaluate('document.querySelector("input[type=email]").value'), 'browser-booking@example.com', 'Contact retained after conflict');
  await click('Envoyer la demande');
  await until('document.body.innerText.includes("Votre demande est enregistrée")', 'Persisted booking receipt');
  await screenshot('booking-receipt-mobile');
  assert.ok(await evaluate(`[...document.querySelectorAll('a')].some(a => a.textContent === 'Retour à l’accueil' && a.getAttribute('href') === '/')`), 'Receipt links back to homepage');

  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await navigate('/auth/login');
  await until('!!document.querySelector("input[type=password]")', 'Login form');
  await fill('input[type=text]', process.env.SMOKE_USERNAME);
  await fill('input[type=password]', process.env.SMOKE_PASSWORD);
  await click('Se connecter');
  await until('location.pathname === "/app" && document.body.innerText.includes("Browser Booking")', 'Dashboard receives persisted appointment');
  await screenshot('booking-dashboard');
  await evaluate(`document.querySelector('a[href="/app/calendar?date=${date}"]').click()`);
  await until(`location.pathname === '/app/calendar' && location.search === '?date=${date}'`, 'Dashboard opens appointment week');
  await until('!!document.querySelector("input[type=date]")', 'Calendar date control');
  assert.equal(await evaluate('document.querySelector("input[type=date]").value'), date, 'Appointment date selected');
  await until('document.body.innerText.includes("Browser Booking")', 'Appointment in calendar');
  const ownCard = `[...document.querySelectorAll('li')].find(el => el.textContent.includes('Browser Booking'))`;
  await evaluate(`${ownCard}.querySelector('details').open = true`);
  await evaluate(`[...${ownCard}.querySelectorAll('button')].find(b => b.textContent === 'Confirmer').click()`);
  await until(`${ownCard}?.textContent.includes('Confirmé')`, 'Confirmation persisted');
  await screenshot('booking-office-calendar');
  await evaluate(`[...${ownCard}.querySelectorAll('button')].find(b => b.textContent === 'Annuler').click()`);
  await click('Oui, annuler');
  await until('!document.body.innerText.includes("Browser Booking")', 'Cancelled booking removed');
  const available = await fetch(`${api}/v1/appointments/availability/?date=${date}&specialty=${area.slug}`).then(r => r.json());
  assert.ok(available.some(slot => slot.start_at === slots[1].start_at), 'Cancellation releases slot');
  await navigate('/app');
  await until('document.body.innerText.includes("Competing Booking")', 'Dashboard reloaded');
  assert.equal(await evaluate('document.body.innerText.includes("Browser Booking")'), false, 'Cancelled appointment removed from dashboard');
  await navigate('/');
  await until('document.querySelector("#expertises")?.textContent.includes("Consultation générale")', 'Homepage expertise loaded');
  assert.ok(await evaluate('document.body.innerText.includes("1 250") && document.body.innerText.includes("980") && document.body.innerText.includes("Chiffres de démonstration")'), 'Illustrative stats clearly labeled');
  await evaluate('document.querySelector("#expertises").scrollIntoView()');
  await delay(900);
  await screenshot('homepage-expertise-desktop');
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await evaluate('document.querySelector("#expertises").scrollIntoView()');
  await delay(200);
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'), true, 'Homepage has no mobile overflow');
  await screenshot('homepage-expertise-mobile');
  await evaluate(`document.querySelector('section[aria-label="Le cabinet en chiffres — données de démonstration"]').scrollIntoView()`);
  await delay(900);
  await screenshot('homepage-stats-mobile');
  assert.deepEqual(exceptions, [], 'No runtime exceptions');
  console.log('PASS: validation feedback, short description, consent, network retry, mobile calendar, conflict recovery, persisted receipt, login, dashboard, confirmation, cancellation, slot release and responsive homepage stats/expertise.');
} finally {
  await command('Page.close');
  socket.close();
}
