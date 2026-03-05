#!/usr/bin/env node
/**
 * DockProbe Dashboard Demo Video Capture
 * Captures sequential frames of dashboard interaction, then assembles into GIF.
 *
 * Usage: node docs/capture-demo-video.js
 * Output: docs/screenshots/demo.gif
 *
 * Requires: npm install puppeteer-core (in docs/)
 * Uses: ImageMagick (convert) for GIF assembly
 */

const puppeteer = require('puppeteer-core');
const path = require('path');
const { execSync } = require('child_process');
const fs = require('fs');

const BASE_URL = process.argv[2] || 'https://localhost:9090';
const AUTH_USER = process.env.AUTH_USER || 'admin';
const AUTH_PASS = process.env.AUTH_PASS || 'changeme';
const CHROME_PATH = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const FRAME_DIR = path.join(__dirname, 'screenshots', 'frames');
const OUTPUT = path.join(__dirname, 'screenshots', 'demo.gif');

const DUMMY_NAMES = [
  'web-frontend', 'api-server', 'postgres-db', 'redis-cache',
  'nginx-proxy', 'worker-queue', 'mail-service', 'monitoring',
  'auth-service', 'search-engine', 'celery-beat', 'rabbitmq',
  'elasticsearch', 'kibana', 'logstash', 'grafana-agent'
];

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function sanitize(page) {
  await page.evaluate((names) => {
    // Container names
    document.querySelectorAll('#containerBody tr').forEach((row, i) => {
      const cells = row.querySelectorAll('td');
      if (cells[0]) cells[0].textContent = names[i] || 'service-' + (i + 1);
      if (cells[2]) cells[2].textContent = (Math.random() * 15).toFixed(1) + '%';
      if (cells[3]) {
        const m = (50 + Math.random() * 500).toFixed(1);
        cells[3].textContent = ((m / 2048) * 100).toFixed(1) + '% (' + m + ' MB)';
      }
      if (cells[4]) cells[4].textContent = (Math.random() * 100).toFixed(1) + ' MB';
      if (cells[5]) cells[5].textContent = (Math.random() * 50).toFixed(1) + ' MB';
      if (cells[6]) cells[6].textContent = (Math.random() * 200).toFixed(1) + ' MB';
      if (cells[7]) cells[7].textContent = (Math.random() * 100).toFixed(1) + ' MB';
      if (cells[8]) cells[8].textContent = '0';
    });

    // Session bar
    const ipEl = document.getElementById('sessionIp');
    if (ipEl) ipEl.textContent = '192.168.1.100';
    document.querySelectorAll('.session-bar span').forEach(el => {
      if (el.textContent.includes('Others')) el.textContent = 'Others: 192.168.1.101';
    });

    // Host cards
    const hostCards = document.getElementById('hostCards');
    if (hostCards) {
      hostCards.querySelectorAll('.card').forEach(card => {
        const label = card.querySelector('.label');
        const value = card.querySelector('.value');
        const sub = card.querySelector('.sub');
        if (!label || !value) return;
        const l = label.textContent.trim();
        if (l.includes('CPU Temp')) { value.textContent = '42°C'; value.style.color = 'var(--green)'; }
        else if (l.includes('GPU Temp')) { value.textContent = '38°C'; value.style.color = 'var(--green)'; }
        else if (l.includes('Disk')) { value.textContent = '45%'; if (sub) sub.textContent = '180.2 GB / 400.0 GB'; }
        else if (l.includes('Load')) { value.innerHTML = '0.85 <span style="font-size:13px;color:var(--text2)">4%</span>'; if (sub) sub.textContent = '5min 0.72 / 15min 0.65'; }
      });
    }

    // Docker disk
    const diskGrid = document.getElementById('diskGrid');
    if (diskGrid) {
      const sizes = diskGrid.querySelectorAll('.size');
      const labels = diskGrid.querySelectorAll('.dlabel');
      ['24.5 GB', '8.2 GB', '312.0 MB', '1.8 GB'].forEach((v, i) => { if (sizes[i]) sizes[i].textContent = v; });
      ['Images (42)', 'Build Cache', 'Volumes (8)', 'Container RW'].forEach((v, i) => { if (labels[i]) labels[i].textContent = v; });
    }

    // Alerts
    document.querySelectorAll('#alertBody tr').forEach((row, i) => {
      const cells = row.querySelectorAll('td');
      const name = names[i % names.length];
      if (cells[0]) cells[0].textContent = 'Mar 1 ' + (10 + Math.floor(i * 0.5)) + ':' + String(10 + i * 7).padStart(2, '0') + ':00';
      if (cells[2]) cells[2].textContent = name;
      if (cells[3]) cells[3].textContent = 'Container ' + name + ' CPU ' + (82 + i * 3) + '.0% (>80.0% x3)';
    });

    // Chart legends
    if (typeof Chart !== 'undefined') {
      Object.values(Chart.instances || {}).forEach(chart => {
        if (chart.data && chart.data.datasets) {
          chart.data.datasets.forEach((ds, i) => { ds.label = names[i] || 'service-' + (i + 1); });
          chart.update('none');
        }
      });
    }
  }, DUMMY_NAMES);
}

async function captureFrame(page, frameNum) {
  const filename = path.join(FRAME_DIR, `frame_${String(frameNum).padStart(4, '0')}.png`);
  await page.screenshot({ path: filename, fullPage: false });
}

async function record() {
  // Prepare frame directory
  if (fs.existsSync(FRAME_DIR)) fs.rmSync(FRAME_DIR, { recursive: true });
  fs.mkdirSync(FRAME_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--disable-gpu', '--window-size=1280,720'],
  });

  const page = await browser.newPage();
  const authHeader = 'Basic ' + Buffer.from(`${AUTH_USER}:${AUTH_PASS}`).toString('base64');
  await page.setExtraHTTPHeaders({ Authorization: authHeader });
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 30000 });
  await delay(3000);

  // Sanitize data
  await sanitize(page);
  await delay(500);

  let frame = 0;

  // Scene 1: Dashboard overview (hold 2s = 6 frames at ~3fps effective)
  console.log('Scene 1: Dashboard overview...');
  for (let i = 0; i < 8; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  // Scene 2: Scroll down to container table (smooth scroll)
  console.log('Scene 2: Scroll to containers...');
  for (let i = 0; i < 12; i++) {
    await page.evaluate(() => window.scrollBy(0, 40));
    await delay(150);
    await captureFrame(page, frame++);
  }

  // Scene 3: Hold on container table (1.5s)
  console.log('Scene 3: Container table...');
  for (let i = 0; i < 6; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  // Scene 4: Click CPU column to sort
  console.log('Scene 4: Sort by CPU...');
  const cpuHeader = await page.$('#containerTable th:nth-child(3)');
  if (cpuHeader) {
    await cpuHeader.click();
    await delay(300);
    await sanitize(page);
    await delay(200);
  }
  for (let i = 0; i < 6; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  // Scene 5: Scroll to charts
  console.log('Scene 5: Scroll to charts...');
  for (let i = 0; i < 16; i++) {
    await page.evaluate(() => window.scrollBy(0, 50));
    await delay(150);
    await captureFrame(page, frame++);
  }

  // Scene 6: Hold on charts (2s)
  console.log('Scene 6: Charts view...');
  for (let i = 0; i < 8; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  // Scene 7: Scroll to Docker Disk + Alerts
  console.log('Scene 7: Scroll to Disk & Alerts...');
  for (let i = 0; i < 14; i++) {
    await page.evaluate(() => window.scrollBy(0, 50));
    await delay(150);
    await captureFrame(page, frame++);
  }

  // Scene 8: Hold on alerts (1.5s)
  console.log('Scene 8: Alert history...');
  for (let i = 0; i < 6; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  // Scene 9: Scroll back to top
  console.log('Scene 9: Back to top...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await delay(300);
  for (let i = 0; i < 6; i++) {
    await captureFrame(page, frame++);
    await delay(250);
  }

  await browser.close();
  console.log(`Captured ${frame} frames.`);

  // Assemble GIF with ImageMagick
  console.log('Assembling GIF...');
  try {
    execSync(
      `convert -delay 15 -loop 0 -resize 960x540 "${FRAME_DIR}/frame_*.png" "${OUTPUT}"`,
      { stdio: 'inherit', timeout: 120000 }
    );
    console.log(`Done! Output: ${OUTPUT}`);

    // Cleanup frames
    fs.rmSync(FRAME_DIR, { recursive: true });
    console.log('Frames cleaned up.');
  } catch (err) {
    console.error('GIF assembly failed:', err.message);
    console.log(`Frames are preserved at ${FRAME_DIR}`);
  }
}

record().catch(err => {
  console.error('Recording failed:', err.message);
  process.exit(1);
});
