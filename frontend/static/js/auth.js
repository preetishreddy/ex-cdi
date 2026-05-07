document.addEventListener('DOMContentLoaded', () => {

  /* ── Password visibility toggle ─────────────── */
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      const eyeOpen = btn.querySelector('.icon-eye');
      const eyeOff  = btn.querySelector('.icon-eye-off');

      if (input.type === 'password') {
        input.type = 'text';
        eyeOpen.style.display = 'none';
        eyeOff.style.display  = 'block';
      } else {
        input.type = 'password';
        eyeOpen.style.display = 'block';
        eyeOff.style.display  = 'none';
      }
    });
  });

  /* ── Password strength meter (register page) ── */
  const passwordInput = document.getElementById('password');
  const strengthFill  = document.getElementById('strengthFill');
  const strengthLabel = document.getElementById('strengthLabel');
  const requirements  = document.getElementById('requirements');

  if (passwordInput && strengthFill && requirements) {
    const checks = {
      length:    v => v.length >= 8,
      uppercase: v => /[A-Z]/.test(v),
      lowercase: v => /[a-z]/.test(v),
      number:    v => /\d/.test(v),
    };

    const checkIcon = '<svg class="req-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
    const circleIcon = '<svg class="req-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>';

    passwordInput.addEventListener('input', () => {
      const val = passwordInput.value;
      let score = 0;

      Object.entries(checks).forEach(([key, fn]) => {
        const li = requirements.querySelector(`[data-req="${key}"]`);
        const passed = fn(val);
        if (passed) score++;
        li.classList.toggle('met', passed);
        li.querySelector('.req-icon').outerHTML = passed ? checkIcon : circleIcon;
      });

      // Extra point for length > 12
      if (val.length >= 12) score++;

      const levels = [
        { width: '0%',   color: 'transparent',  label: '' },
        { width: '25%',  color: '#ff4d6a',      label: 'Weak' },
        { width: '50%',  color: '#ffaa2c',      label: 'Fair' },
        { width: '75%',  color: '#1e8fff',      label: 'Good' },
        { width: '100%', color: '#00d48a',       label: 'Strong' },
      ];

      const level = val.length === 0 ? levels[0] : levels[Math.min(score, 4)];
      strengthFill.style.width      = level.width;
      strengthFill.style.background = level.color;
      strengthLabel.textContent     = level.label;
      strengthLabel.style.color     = level.color;
    });
  }

  /* ── Basic client-side validation ───────────── */
  const loginForm    = document.getElementById('loginForm');
  const forgotForm   = document.getElementById('forgotForm');
  const registerForm = document.getElementById('registerForm');

  function showAlert(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
  }

  function hideAlerts() {
    document.querySelectorAll('.alert').forEach(a => a.style.display = 'none');
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  if (loginForm) {
    loginForm.addEventListener('submit', e => {
      hideAlerts();
      const email = loginForm.querySelector('#email').value.trim();
      const pass  = loginForm.querySelector('#password').value;

      if (!email || !isValidEmail(email)) {
        e.preventDefault();
        showAlert('loginAlert', 'Please enter a valid work email address.');
        return;
      }
      if (!pass) {
        e.preventDefault();
        showAlert('loginAlert', 'Please enter your password.');
      }
    });
  }

  if (forgotForm) {
    forgotForm.addEventListener('submit', e => {
      hideAlerts();
      const email = forgotForm.querySelector('#email').value.trim();

      if (!email || !isValidEmail(email)) {
        e.preventDefault();
        showAlert('resetError', 'Please enter a valid work email address.');
      }
      // On real success the backend would redirect or you'd show:
      // showAlert('resetSuccess', 'If an account exists, a reset link has been sent.');
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', e => {
      hideAlerts();
      const name    = registerForm.querySelector('#full_name').value.trim();
      const email   = registerForm.querySelector('#email').value.trim();
      const role    = registerForm.querySelector('#role') ? registerForm.querySelector('#role').value : '';
      const dept    = registerForm.querySelector('#department') ? registerForm.querySelector('#department').value : '';
      const pass    = registerForm.querySelector('#password').value;
      const confirm = registerForm.querySelector('#confirm_password').value;

      if (!name) {
        e.preventDefault();
        showAlert('registerAlert', 'Please enter your full name.');
        return;
      }
      if (!email || !isValidEmail(email)) {
        e.preventDefault();
        showAlert('registerAlert', 'Please enter a valid work email address.');
        return;
      }
      if (!role) {
        e.preventDefault();
        showAlert('registerAlert', 'Please select your role.');
        return;
      }
      if (!dept) {
        e.preventDefault();
        showAlert('registerAlert', 'Please select your department.');
        return;
      }
      if (pass.length < 8) {
        e.preventDefault();
        showAlert('registerAlert', 'Password must be at least 8 characters.');
        return;
      }
      if (pass !== confirm) {
        e.preventDefault();
        showAlert('registerAlert', 'Passwords do not match.');
      }
    });
  }

});