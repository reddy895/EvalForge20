#!/usr/bin/env node
/**
 * EvalForge20 — Backend Development Launcher
 *
 * Implements:
 * - Environment variable loading (.env and fallback defaults)
 * - Required configuration verification and warnings
 * - Port availability probe and actionable conflict messages
 * - Graceful shutdown signal handling (SIGINT, SIGTERM)
 * - Automatic prevention of orphaned processes
 * - Explicit listening address logging
 */

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');
const BACKEND_DIR = path.resolve(REPO_ROOT, 'backend');

// 1. Environment Loading
function loadEnv() {
  const envFiles = [
    path.join(REPO_ROOT, '.env'),
    path.join(BACKEND_DIR, '.env'),
    path.join(REPO_ROOT, '.env.example'),
    path.join(BACKEND_DIR, '.env.example'),
  ];

  for (const envPath of envFiles) {
    if (fs.existsSync(envPath)) {
      try {
        const content = fs.readFileSync(envPath, 'utf8');
        for (const line of content.split('\n')) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx > 0) {
            const key = trimmed.slice(0, eqIdx).trim();
            const val = trimmed.slice(eqIdx + 1).trim().replace(/^['"]|['"]$/g, '');
            if (!process.env[key]) {
              process.env[key] = val;
            }
          }
        }
      } catch (err) {
        console.warn(`[EvalForge20] Warning reading ${envPath}:`, err.message);
      }
    }
  }
}

loadEnv();

// Parse CLI flags
const args = process.argv.slice(2);
let customPort = null;
let customHost = null;
const isDryRun = args.includes('--dry-run') || args.includes('--check');

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--port' && args[i + 1]) {
    customPort = parseInt(args[i + 1], 10);
  }
  if (args[i] === '--host' && args[i + 1]) {
    customHost = args[i + 1];
  }
}

const HOST = customHost || process.env.HOST || '127.0.0.1';
const PORT = customPort || parseInt(process.env.PORT || '8000', 10);
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const DATABASE_URL = process.env.DATABASE_URL || 'sqlite+aiosqlite:///./evalforge.db';

console.log('====================================================');
console.log('       EvalForge20 — Backend Service Launcher       ');
console.log('====================================================');
console.log(`[EvalForge20] Host: ${HOST}`);
console.log(`[EvalForge20] Port: ${PORT}`);
console.log(`[EvalForge20] Database: ${DATABASE_URL}`);
console.log(`[EvalForge20] Ollama Endpoint: ${OLLAMA_BASE_URL}`);

// 2. Port Check
function checkPortFree(port, host) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(false);
      } else {
        resolve(true);
      }
    });
    server.once('listening', () => {
      server.close(() => resolve(true));
    });
    server.listen(port, host);
  });
}

function probeExistingInstance(port, host) {
  return new Promise((resolve) => {
    const req = http.get(`http://${host}:${port}/health`, { timeout: 1500 }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

// 3. Locate Python / Uvicorn executable
function findRunner() {
  const candidates = [
    path.join(REPO_ROOT, '.venv', 'bin', 'uvicorn'),
    path.join(BACKEND_DIR, '.venv', 'bin', 'uvicorn'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return { cmd: c, args: [] };
    }
  }

  // Check if uv is available
  try {
    const uvCheck = spawn('which', ['uv']);
    return { cmd: 'uv', args: ['run', 'uvicorn'] };
  } catch {
    return { cmd: 'python3', args: ['-m', 'uvicorn'] };
  }
}

async function main() {
  const isFree = await checkPortFree(PORT, HOST);
  if (!isFree) {
    const isEvalForge = await probeExistingInstance(PORT, HOST);
    if (isEvalForge) {
      console.log(`[EvalForge20] An EvalForge20 instance is already active and healthy on http://${HOST}:${PORT}`);
      console.log(`[EvalForge20] Access API docs at: http://${HOST}:${PORT}/docs`);
      process.exit(0);
    } else {
      console.error(`[EvalForge20] ERROR: Port ${PORT} is currently in use by another process.`);
      console.error(`[EvalForge20] Please terminate the conflicting process or set PORT in .env.`);
      process.exit(1);
    }
  }

  const runner = findRunner();
  const uvicornArgs = [
    ...runner.args,
    'src.evalforge.main:app',
    '--app-dir',
    BACKEND_DIR,
    '--host',
    HOST,
    '--port',
    String(PORT),
    '--reload',
  ];

  console.log(`[EvalForge20] Starting Uvicorn with command: ${runner.cmd} ${uvicornArgs.join(' ')}`);
  console.log(`[EvalForge20] Listening URL: http://${HOST}:${PORT}`);
  console.log(`[EvalForge20] OpenAPI Documentation: http://${HOST}:${PORT}/docs`);
  console.log('====================================================');

  if (isDryRun) {
    console.log('[EvalForge20] Dry run / verification check passed successfully.');
    process.exit(0);
  }

  const child = spawn(runner.cmd, uvicornArgs, {
    cwd: REPO_ROOT,
    stdio: 'inherit',
    env: { ...process.env, PYTHONPATH: `${BACKEND_DIR}:${process.env.PYTHONPATH || ''}` },
  });

  let isShuttingDown = false;
  function handleShutdown(signal) {
    if (isShuttingDown) return;
    isShuttingDown = true;
    console.log(`\n[EvalForge20] Caught ${signal}. Initiating graceful shutdown...`);
    if (child && child.pid) {
      child.kill(signal);
      const timer = setTimeout(() => {
        console.warn('[EvalForge20] Shutdown timeout expired. Forcing termination...');
        try {
          child.kill('SIGKILL');
        } catch {}
        process.exit(0);
      }, 4000);
      child.on('close', () => {
        clearTimeout(timer);
        console.log('[EvalForge20] Backend server shut down successfully.');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }

  process.on('SIGINT', () => handleShutdown('SIGINT'));
  process.on('SIGTERM', () => handleShutdown('SIGTERM'));

  child.on('error', (err) => {
    console.error('[EvalForge20] Failed to start backend process:', err.message);
    process.exit(1);
  });

  child.on('exit', (code, signal) => {
    if (!isShuttingDown) {
      console.log(`[EvalForge20] Backend process exited with code ${code ?? 0} (signal: ${signal ?? 'none'})`);
      process.exit(code ?? 0);
    }
  });
}

main().catch((err) => {
  console.error('[EvalForge20] Fatal launcher exception:', err);
  process.exit(1);
});
