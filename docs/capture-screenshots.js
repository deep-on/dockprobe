#!/usr/bin/env node
/**
 * DockProbe Dashboard Screenshot Capture
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

  // Replace ALL sensitive content with dummy data
  await page.evaluate(() => {
    const dummyNames = [
      'web-frontend', 'api-server', 'postgres-db', 'redis-cache',
      'nginx-proxy', 'worker-queue', 'mail-service', 'monitoring',
      'auth-service', 'search-engine', 'celery-beat', 'rabbitmq',
      'elasticsearch', 'kibana', 'logstash', 'grafana-agent'
    ];

    // --- Container table: replace names + randomize stats ---
    document.querySelectorAll('#containerBody tr').forEach((row, i) => {
      const cells = row.querySelectorAll('td');
      if (cells[0]) cells[0].textContent = dummyNames[i] || 'service-' + (i + 1);
      // CPU %
      if (cells[2]) cells[2].textContent = (Math.random() * 15).toFixed(1) + '%';
      // Memory
      if (cells[3]) {
        const memMB = (50 + Math.random() * 500).toFixed(1);
        cells[3].textContent = ((memMB / 2048) * 100).toFixed(1) + '% (' + memMB + ' MB)';
      }
      // Net RX
      if (cells[4]) cells[4].textContent = (Math.random() * 100).toFixed(1) + ' MB';
      // Net TX
      if (cells[5]) cells[5].textContent = (Math.random() * 50).toFixed(1) + ' MB';
      // Blk Read
      if (cells[6]) cells[6].textContent = (Math.random() * 200).toFixed(1) + ' MB';
      // Blk Write
      if (cells[7]) cells[7].textContent = (Math.random() * 100).toFixed(1) + ' MB';
      // Restarts
      if (cells[8]) cells[8].textContent = '0';
    });

    // --- Session bar: replace IP and Others ---
    const ipEl = document.getElementById('sessionIp');
    if (ipEl) ipEl.textContent = '192.168.1.100';
    document.querySelectorAll('.session-bar span').forEach(el => {
      if (el.textContent.includes('Others')) {
        el.textContent = 'Others: 192.168.1.101';
      }
    });

    // --- Host cards: replace real host data ---
    const hostCards = document.getElementById('hostCards');
    if (hostCards) {
      const cards = hostCards.querySelectorAll('.card');
      cards.forEach(card => {
        const label = card.querySelector('.label');
        const value = card.querySelector('.value');
        const sub = card.querySelector('.sub');
        if (!label || !value) return;
        const l = label.textContent.trim();
        if (l.includes('CPU Temp')) {
          value.textContent = '42°C';
          value.style.color = 'var(--green)';
        } else if (l.includes('GPU Temp')) {
          value.textContent = '38°C';
          value.style.color = 'var(--green)';
        } else if (l.includes('Disk')) {
          value.textContent = '45%';
          value.style.color = 'var(--text)';
          if (sub) sub.textContent = '180.2 GB / 400.0 GB';
        } else if (l.includes('Load')) {
          value.innerHTML = '0.85 <span style="font-size:13px;color:var(--text2)">4%</span>';
          if (sub) sub.textContent = '5min 0.72 / 15min 0.65';
        }
      });
    }

    // --- Host cards header: replace cores info ---
    document.querySelectorAll('.card .label').forEach(el => {
      if (el.textContent.includes('CORES')) {
        el.textContent = el.textContent.replace(/\d+ CORES/, '8 CORES');
      }
    });

    // --- Docker Disk Usage (#diskGrid): replace real values ---
    const diskGrid = document.getElementById('diskGrid');
    if (diskGrid) {
      const sizes = diskGrid.querySelectorAll('.size');
      const labels = diskGrid.querySelectorAll('.dlabel');
      const dummySizes = ['24.5 GB', '8.2 GB', '312.0 MB', '1.8 GB'];
      const dummyLabels = ['Images (42)', 'Build Cache', 'Volumes (8)', 'Container RW'];
      sizes.forEach((s, i) => { if (dummySizes[i]) s.textContent = dummySizes[i]; });
      labels.forEach((l, i) => { if (dummyLabels[i]) l.textContent = dummyLabels[i]; });
    }

    // --- LOAD AVG label: replace CORES count ---
    document.querySelectorAll('.label').forEach(el => {
      if (el.textContent.includes('CORES')) {
        el.textContent = el.textContent.replace(/\d+ CORES/, '8 CORES');
      }
    });

    // --- Alert history: replace target and message ---
    document.querySelectorAll('#alertBody tr').forEach((row, i) => {
      const cells = row.querySelectorAll('td');
      const name = dummyNames[i % dummyNames.length];
      if (cells[0]) cells[0].textContent = 'Mar 1 ' + (10 + Math.floor(i * 0.5)) + ':' + String(10 + i * 7).padStart(2, '0') + ':00';
      if (cells[2]) cells[2].textContent = name;
      if (cells[3]) cells[3].textContent = 'Container ' + name + ' CPU ' + (82 + i * 3) + '.0% (>80.0% x3)';
    });

    // --- Chart legends: replace with dummy names ---
    if (typeof Chart !== 'undefined') {
      Object.values(Chart.instances || {}).forEach(chart => {
        if (chart.data && chart.data.datasets) {
          chart.data.datasets.forEach((ds, i) => {
            ds.label = dummyNames[i] || 'service-' + (i + 1);
          });
          chart.update('none');
        }
      });
    }

    // --- Connection count ---
    document.querySelectorAll('.session-bar span').forEach(el => {
      const match = el.textContent.match(/(\d+)\s*\/\s*(\d+)/);
      if (match) el.textContent = '2 / 5';
    });

    // --- Updated time ---
    document.querySelectorAll('*').forEach(el => {
      if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
        if (el.textContent.match(/Updated:.*\d{2}:\d{2}:\d{2}/)) {
          el.textContent = 'Updated: 14:32:15';
        }
      }
    });
  });

  await delay(500);

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
