#!/usr/bin/env node
'use strict';

/**
 * Thin pass-through wrapper: forwards every argument to the real
 * `agent-regress` Python CLI (from the `agent-regress-cli` PyPI package --
 * the distribution name and the console-script name differ, since
 * `agent-regress` on PyPI was blocked as too similar to an unrelated
 * existing project) and relays its stdout, stderr, and exit code unchanged.
 *
 * The actual statistics (scipy Mann-Whitney U, bootstrap CI, Cohen's d)
 * live in Python -- this script does not reimplement any of it. It only
 * finds a way to invoke the Python CLI and gets out of the way.
 *
 * Resolution order:
 *   1. `agent-regress` directly on PATH (installed via `pip install
 *      agent-regress-cli` / `uv tool install agent-regress-cli`, etc.)
 *   2. `uvx --from agent-regress-cli agent-regress` (ephemeral run via uv,
 *      no install required)
 *   3. `pipx run --spec agent-regress-cli agent-regress` (ephemeral run via
 *      pipx, no install required)
 *   4. `python3 -m agent_regress.cli` / `python -m agent_regress.cli`, if
 *      the package is importable but its console-script entry point isn't
 *      on PATH (e.g. a `pip install --user` whose scripts dir was never
 *      added to PATH).
 *   5. None of the above: print an actionable error to stderr and exit 1.
 */

const { spawnSync } = require('node:child_process');

const forwardedArgs = process.argv.slice(2);
const useShell = process.platform === 'win32';

/** Run `command args...`, inheriting stdio, without throwing on ENOENT. */
function run(command, args) {
  return spawnSync(command, args, { stdio: 'inherit', shell: useShell });
}

/** True if `command` exists on PATH and can be spawned at all. */
function commandExists(command) {
  const result = spawnSync(command, ['--version'], {
    stdio: 'ignore',
    shell: useShell,
  });
  return !result.error;
}

/** True if `python` (some working interpreter) has agent_regress importable. */
function pythonHasAgentRegress(pythonCmd) {
  const result = spawnSync(
    pythonCmd,
    ['-m', 'pip', 'show', 'agent-regress-cli'],
    { stdio: 'ignore', shell: useShell }
  );
  return !result.error && result.status === 0;
}

function exitWith(result) {
  if (result.error) {
    console.error(`agent-regress: failed to run: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status === null ? 1 : result.status);
}

function fail() {
  console.error(
    [
      'agent-regress: could not find the agent-regress Python CLI.',
      '',
      'This package (npm `agent-regress-cli`) is a thin wrapper around the',
      'Python `agent-regress-cli` package -- the actual statistics (scipy',
      'Mann-Whitney U, bootstrap CI, Cohen\'s d) run in Python, so it must',
      'be installed separately. Install it with one of:',
      '',
      '  pip install agent-regress-cli',
      '  uv tool install agent-regress-cli',
      '  pipx install agent-regress-cli',
      '',
      'Then re-run this command. Full docs:',
      '  https://github.com/RudrenduPaul/agent-eval',
    ].join('\n')
  );
  process.exit(1);
}

function main() {
  // 1. Direct: `agent-regress` already on PATH.
  if (commandExists('agent-regress')) {
    exitWith(run('agent-regress', forwardedArgs));
    return;
  }

  // 2. Ephemeral via uv. `--from` is required because the PyPI
  // distribution (agent-regress-cli) and the console script
  // (agent-regress) have different names.
  if (commandExists('uvx')) {
    exitWith(
      run('uvx', ['--from', 'agent-regress-cli', 'agent-regress', ...forwardedArgs])
    );
    return;
  }

  // 3. Ephemeral via pipx. `--spec` is required for the same reason.
  if (commandExists('pipx')) {
    exitWith(
      run('pipx', ['run', '--spec', 'agent-regress-cli', 'agent-regress', ...forwardedArgs])
    );
    return;
  }

  // 4. Installed but its console-script entry point isn't on PATH --
  // invoke the module directly instead.
  for (const pythonCmd of ['python3', 'python']) {
    if (commandExists(pythonCmd) && pythonHasAgentRegress(pythonCmd)) {
      exitWith(run(pythonCmd, ['-m', 'agent_regress.cli', ...forwardedArgs]));
      return;
    }
  }

  // 5. Nothing available.
  fail();
}

main();
