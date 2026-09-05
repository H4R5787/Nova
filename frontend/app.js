/**
 * Nova Playground UI Controller
 */

const PRESETS = {
  loop_scoping: `// Loop Scoping & Per-Iteration Isolation Challenge
// Nova isolates each iteration frame, allowing closures to capture
// their specific iteration state rather than the mutated counter.

let mut closures = [];
let mut i = 0;

while (i < 4) {
    let iteration = i;
    let cb = fn() {
        return iteration;
    };
    push(closures, cb);
    i = i + 1;
}

print("=== Loop Scoping Verification ===");
let mut idx = 0;
while (idx < len(closures)) {
    let f = closures[idx];
    print("Iteration closure", idx, "evaluates to:", f());
    idx = idx + 1;
}

if (closures[0]() == 0 && closures[1]() == 1 && closures[2]() == 2 && closures[3]() == 3) {
    print("SUCCESS: Per-iteration environment isolation verified!");
}
`,

  fibonacci: `// Fibonacci in Nova
fn fibonacci(n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

print("=== Recursive Fibonacci ===");
let mut i = 0;
while (i <= 8) {
    print("fib(" + str(i) + ") =", fibonacci(i));
    i = i + 1;
}
`,

  closures: `// First-Class Functions & Lexical Closures
fn make_bank_account(initial_balance) {
    let mut balance = initial_balance;
    return fn(deposit_amount) {
        balance = balance + deposit_amount;
        return balance;
    };
}

let alice_account = make_bank_account(100);
let bob_account = make_bank_account(500);

print("Alice deposits 50:", alice_account(50));   // 150
print("Alice deposits 25:", alice_account(25));   // 175
print("Bob deposits 100:", bob_account(100));     // 600
print("Alice balance unchanged:", alice_account(0)); // 175
`,

  immutability: `// Immutability Safety Check
let immutable_var = "Nova Language";
print("Original:", immutable_var);

// Attempting to reassign will trigger runtime safety check:
// Uncomment below to see error:
// immutable_var = "Attempted Mutation";

let mut mutable_counter = 0;
mutable_counter = mutable_counter + 1;
print("Mutable counter incremented:", mutable_counter);
`
};

document.addEventListener('DOMContentLoaded', () => {
  const codeEditor = document.getElementById('codeEditor');
  const lineNumbers = document.getElementById('lineNumbers');
  const consoleOutput = document.getElementById('consoleOutput');
  const astOutput = document.getElementById('astOutput');
  const scopeOutput = document.getElementById('scopeOutput');
  const runBtn = document.getElementById('runBtn');
  const clearBtn = document.getElementById('clearBtn');
  const presetSelect = document.getElementById('presetSelect');
  const tabButtons = document.querySelectorAll('.tab-button');
  const execTimeEl = document.getElementById('execTime');
  const lineCountEl = document.getElementById('lineCount');

  // Update line numbers
  function updateLineNumbers() {
    const lines = codeEditor.value.split('\n');
    lineCountEl.textContent = `${lines.length} lines`;
    lineNumbers.innerHTML = lines.map((_, i) => i + 1).join('<br>');
  }

  codeEditor.addEventListener('input', updateLineNumbers);
  codeEditor.addEventListener('scroll', () => {
    lineNumbers.scrollTop = codeEditor.scrollTop;
  });

  // Handle Tab key in editor
  codeEditor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = codeEditor.selectionStart;
      const end = codeEditor.selectionEnd;
      codeEditor.value = codeEditor.value.substring(0, start) + '    ' + codeEditor.value.substring(end);
      codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
      updateLineNumbers();
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runCode();
    }
  });

  // Tab switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      document.getElementById(tabId).classList.add('active');
    });
  });

  // Load Preset
  presetSelect.addEventListener('change', (e) => {
    const key = e.target.value;
    if (PRESETS[key]) {
      codeEditor.value = PRESETS[key];
      updateLineNumbers();
    }
  });

  function log(text, type = 'output') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = text;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  function renderScope(scopeSnapshot) {
    scopeOutput.innerHTML = '';
    if (!scopeSnapshot) return;

    let current = scopeSnapshot;
    let depth = 0;
    while (current) {
      const frameDiv = document.createElement('div');
      frameDiv.className = 'scope-frame';

      const title = document.createElement('div');
      title.className = 'scope-frame-title';
      title.textContent = `Frame: ${current.scope} (Depth: ${depth})`;
      frameDiv.appendChild(title);

      const table = document.createElement('table');
      table.className = 'scope-table';
      table.innerHTML = `
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Value</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          ${Object.entries(current.bindings).map(([id, meta]) => `
            <tr>
              <td><strong>${id}</strong></td>
              <td><code>${meta.value}</code></td>
              <td><span class="${meta.mutable ? 'pill-mut' : 'pill-immut'}">${meta.mutable ? 'mut' : 'immutable'}</span></td>
            </tr>
          `).join('')}
        </tbody>
      `;

      if (Object.keys(current.bindings).length === 0) {
        table.innerHTML = '<tbody><tr><td colspan="3" style="color: #64748b; font-style: italic;">No local bindings in this frame</td></tr></tbody>';
      }

      frameDiv.appendChild(table);
      scopeOutput.appendChild(frameDiv);

      current = current.parent;
      depth++;
    }
  }

  function runCode() {
    consoleOutput.innerHTML = '';
    log('Running Nova engine...', 'system');

    const source = codeEditor.value;
    const startTime = performance.now();

    try {
      const result = window.Nova.run(source, (line) => {
        log(line, 'output');
      });

      const elapsed = (performance.now() - startTime).toFixed(2);
      execTimeEl.textContent = `${elapsed} ms`;

      if (result.result !== null && result.result !== undefined) {
        log(`=> ${JSON.stringify(result.result)}`, 'result');
      }

      // Populate AST tree view
      astOutput.textContent = JSON.stringify(result.ast, null, 2);

      // Populate Scope Inspector
      renderScope(result.scope);

    } catch (err) {
      const elapsed = (performance.now() - startTime).toFixed(2);
      execTimeEl.textContent = `${elapsed} ms`;
      log(err.message || String(err), 'error');
    }
  }

  runBtn.addEventListener('click', runCode);
  clearBtn.addEventListener('click', () => {
    consoleOutput.innerHTML = '';
  });

  // Initialize with loop scoping demo
  codeEditor.value = PRESETS.loop_scoping;
  updateLineNumbers();
  runCode();
});
