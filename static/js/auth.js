const form = document.querySelector('[data-auth-form]');
const password = document.querySelector('#password');
const confirmPassword = document.querySelector('#confirm_password');

document.querySelectorAll('[data-password-toggle]').forEach((button) => {
  button.addEventListener('click', () => {
    const input = document.querySelector(button.dataset.passwordToggle);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    button.textContent = show ? 'Hide' : 'Show';
  });
});

function showError(input, message) {
  const error = document.querySelector(`[data-error-for="${input.name}"]`);
  input.setAttribute('aria-invalid', Boolean(message));
  if (error) error.textContent = message || '';
  return !message;
}

function passwordScore(value) {
  return [value.length >= 8, /[A-Z]/.test(value), /[0-9]/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
}

if (password) {
  password.addEventListener('input', () => {
    const meter = document.querySelector('[data-strength]');
    const score = passwordScore(password.value);
    if (meter) meter.dataset.level = score;
    if (confirmPassword?.value) showError(confirmPassword, confirmPassword.value === password.value ? '' : 'Passwords do not match.');
  });
  password.addEventListener('keyup', (event) => {
    const warning = document.querySelector('[data-caps-lock]');
    if (warning) warning.hidden = !event.getModifierState('CapsLock');
  });
}

form?.addEventListener('submit', (event) => {
  let valid = true;
  form.querySelectorAll('input[required]').forEach((input) => {
    if (input.type !== 'password' && input.type !== 'checkbox') input.value = input.value.trim();
    let message = input.type === 'checkbox' ? (!input.checked ? 'You must accept this to continue.' : '') : (!input.value ? 'This field is required.' : '');
    if (!message && input.type === 'email' && !input.validity.valid) message = 'Enter a valid email address.';
    if (!message && input.name === 'password' && input.value.length < 6) message = 'Use at least 6 characters.';
    if (!message && input.name === 'confirm_password' && input.value !== password?.value) message = 'Passwords do not match.';
    valid = showError(input, message) && valid;
  });
  if (!valid) { event.preventDefault(); return; }
  const button = form.querySelector('button[type="submit"]');
  if (button) { button.setAttribute('aria-busy', 'true'); button.disabled = true; button.lastChild.textContent = ' Please wait…'; }
});
