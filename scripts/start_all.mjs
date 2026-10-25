#!/usr/bin/env node
/**
 * EvalForge20 — Full-Stack Development Launcher
 * Starts both backend and frontend development servers with unified graceful termination.
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');
const FRONTEND_DIR = path.resolve(REPO_ROOT, 'frontend');

console.log('[EvalForge20] Starting Full Stack (Backend + Frontend)...');

const backend = spawn('node', ['scripts/start_backend.mjs'], {
  cwd: REPO_ROOT,
  stdio: 'inherit',
});

const frontend = spawn('npm', ['run', 'dev'], {
  cwd: FRONTEND_DIR,
  stdio: 'inherit',
});

function handleExit(sig) {
  console.log(`\n[EvalForge20] Stopping services (${sig})...`);
  try { backend.kill(sig); } catch {}
  try { frontend.kill(sig); } catch {}
  setTimeout(() => process.exit(0), 1000);
}

process.on('SIGINT', () => handleExit('SIGINT'));
process.on('SIGTERM', () => handleExit('SIGTERM'));

backend.on('exit', (code) => {
  if (code !== 0 && code !== null) {
    console.error(`[EvalForge20] Backend exited with code ${code}`);
    try { frontend.kill(); } catch {}
    process.exit(code);
  }
});

frontend.on('exit', (code) => {
  if (code !== 0 && code !== null) {
    console.error(`[EvalForge20] Frontend exited with code ${code}`);
    try { backend.kill(); } catch {}
    process.exit(code);
  }
});
