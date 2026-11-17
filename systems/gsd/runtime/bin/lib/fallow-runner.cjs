'use strict';

const fs = require('node:fs');
const path = require('node:path');

function candidateNames() {
  return process.platform === 'win32'
    ? ['fallow.exe', 'fallow.cmd', 'fallow.bat', 'fallow']
    : ['fallow'];
}

function isExecutableFile(filePath) {
  try {
    const stat = fs.statSync(filePath);
    if (!stat.isFile()) return false;
    if (process.platform === 'win32') return true;
    fs.accessSync(filePath, fs.constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function findInPath(envPath) {
  if (!envPath) return null;
  const names = candidateNames();
  const segments = envPath.split(path.delimiter).filter(Boolean);
  for (const segment of segments) {
    for (const name of names) {
      const candidate = path.join(segment, name);
      if (isExecutableFile(candidate)) return candidate;
    }
  }
  return null;
}

function findInNodeModules(cwd) {
  const names = candidateNames();
  const binDir = path.join(cwd, 'node_modules', '.bin');
  for (const name of names) {
    const candidate = path.join(binDir, name);
    if (isExecutableFile(candidate)) return candidate;
  }
  return null;
}

