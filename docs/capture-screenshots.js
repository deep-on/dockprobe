#!/usr/bin/env node
/**
 * DockWatch Dashboard Screenshot Capture
 * Usage: node docs/capture-screenshots.js [base-url]
 *
 * Requires: npm install puppeteer-core
 * Uses system Chrome at /usr/bin/google-chrome
 */

const puppeteer = require('puppeteer-core');
const path = require('path');

const BASE_URL = process.argv[2] || 'https://localhost:9090';
const AUTH_USER = process.env.AUTH_USER || 'admin';
const AUTH_PASS = process.env.AUTH_PASS || 'changeme';
const CHROME_PATH = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const OUTPUT_DIR = path.join(__dirname, 'screenshots');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function capture() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--ignore-certificate-errors',
      '--disable-gpu',
      '--window-size=1920,1080',
    ],
  });

  const page = await browser.newPage();

  // Set Basic Auth header
  const authHeader = 'Basic ' + Buffer.from(`${AUTH_USER}:${AUTH_PASS}`).toString('base64');
  await page.setExtraHTTPHeaders({ Authorization: authHeader });

  // Navigate and wait for dashboard to load
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 30000 });

  // Wait for data to populate
  await delay(5000);

  // 1. Full page screenshot
  console.log('Capturing dashboard-full.png ...');
  await page.screenshot({
    path: path.join(OUTPUT_DIR, 'dashboard-full.png'),
    fullPage: true,
  });

  // 2. Hero (viewport / above-the-fold)
  console.log('Capturing dashboard-hero.png ...');
  await page.screenshot({
    path: path.join(OUTPUT_DIR, 'dashboard-hero.png'),
    fullPage: false,
  });

  // 3. Host cards section
  console.log('Capturing host-cards.png ...');
  const hostCards = await page.$('#hostCards, .cards');
  if (hostCards) {
    await hostCards.screenshot({ path: path.join(OUTPUT_DIR, 'host-cards.png') });
  } else {
    console.warn('  Host cards selector not found — skipping');
  }

  // 4. Container table section
  console.log('Capturing container-table.png ...');
  const containerTable = await page.$('.container-table, #container-table, table');
  if (containerTable) {
    await containerTable.screenshot({ path: path.join(OUTPUT_DIR, 'container-table.png') });
  } else {
    console.warn('  Container table selector not found — skipping');
  }

  // 5. Charts section
  console.log('Capturing charts.png ...');
  const charts = await page.$('.charts-section, .charts, #charts');
  if (charts) {
    await charts.screenshot({ path: path.join(OUTPUT_DIR, 'charts.png') });
  } else {
    console.warn('  Charts selector not found — skipping');
  }

  await browser.close();
  console.log('Done! Screenshots saved to docs/screenshots/');
}

capture().catch(err => {
  console.error('Screenshot capture failed:', err.message);
  process.exit(1);
});
