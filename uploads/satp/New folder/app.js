/* ===============================
   App.js - Main Application Logic
   =============================== */

// ==== Navigation Toggle ====
document.addEventListener('DOMContentLoaded', function() {
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle) {
    navToggle.addEventListener('click', function() {
      navLinks.classList.toggle('active');
    });

    // Close menu when link is clicked
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.addEventListener('click', function() {
        navLinks.classList.remove('active');
      });
    });
  }

  // Set active link based on current page
  setActiveNavLink();
});

// Set active navigation link
function setActiveNavLink() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

// ==== Form Validation ====
const formValidation = {
  email: function(value) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(value);
  },
  password: function(value) {
    return value.length >= 6;
  },
  text: function(value) {
    return value.trim().length > 0;
  },
  number: function(value) {
    return !isNaN(value) && value > 0;
  }
};

// Validate form field
function validateField(input) {
  const type = input.getAttribute('data-validate') || input.type;
  const value = input.value;
  const errorElement = input.nextElementSibling;

  if (!errorElement || !errorElement.classList.contains('error-message')) {
    return true;
  }

  let isValid = true;
  let errorMsg = '';

  if (type === 'email' && value && !formValidation.email(value)) {
    isValid = false;
    errorMsg = 'Please enter a valid email address';
  } else if (type === 'password' && value && !formValidation.password(value)) {
    isValid = false;
    errorMsg = 'Password must be at least 6 characters';
  } else if (type === 'text' && input.hasAttribute('required') && !formValidation.text(value)) {
    isValid = false;
    errorMsg = 'This field is required';
  }

  if (!isValid) {
    input.classList.add('error');
    errorElement.textContent = errorMsg;
    errorElement.classList.add('show');
  } else {
    input.classList.remove('error');
    errorElement.classList.remove('show');
  }

  return isValid;
}

// Attach validation to form inputs
document.querySelectorAll('input[data-validate], input[required]').forEach(input => {
  input.addEventListener('blur', function() {
    validateField(this);
  });

  input.addEventListener('input', function() {
    if (this.classList.contains('error')) {
      validateField(this);
    }
  });
});

// Form submission handler
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function(e) {
    e.preventDefault();

    let isFormValid = true;
    this.querySelectorAll('input[data-validate], input[required]').forEach(input => {
      if (!validateField(input)) {
        isFormValid = false;
      }
    });

    if (isFormValid) {
      // Handle form submission
      const formType = this.getAttribute('data-form-type') || 'default';
      handleFormSubmit(this, formType);
    }
  });
});

// Handle form submission
function handleFormSubmit(form, formType) {
  // Get form data
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  // Log form data (in production, this would send to backend)
  console.log('Form submitted:', formType, data);

  // Show success message
  showAlert('Form submitted successfully!', 'success');

  // Optional: Reset form
  form.reset();

  // In production, you would send data to backend here
  // Example: fetch('/api/submit-form', { method: 'POST', body: formData })
}

// ==== Alert Messages ====
function showAlert(message, type = 'info') {
  const alertContainer = document.getElementById('alert-container') || createAlertContainer();
  const alert = document.createElement('div');
  alert.className = `alert ${type}`;
  alert.textContent = message;

  alertContainer.appendChild(alert);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    alert.remove();
  }, 5000);
}

function createAlertContainer() {
  const container = document.createElement('div');
  container.id = 'alert-container';
  container.style.position = 'fixed';
  container.style.top = '70px';
  container.style.right = '20px';
  container.style.zIndex = '9999';
  container.style.maxWidth = '400px';
  document.body.appendChild(container);
  return container;
}

// ==== Achievement Upload ====
const fileUpload = {
  init: function() {
    const uploadBtn = document.getElementById('upload-file-btn');
    const fileInput = document.getElementById('file-input');

    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener('click', () => fileInput.click());

      fileInput.addEventListener('change', (e) => {
        this.handleFileSelect(e);
      });
    }
  },

  handleFileSelect: function(e) {
    const files = e.target.files;
    if (files.length > 0) {
      const file = files[0];
      const fileList = document.getElementById('selected-files');

      if (fileList) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item card mt-2';
        fileItem.innerHTML = `
          <strong>${file.name}</strong>
          <small>${(file.size / 1024).toFixed(2)} KB</small>
          <button type="button" class="btn mt-1" onclick="this.parentElement.remove()">Remove</button>
        `;
        fileList.appendChild(fileItem);
      }

      showAlert(`File "${file.name}" selected successfully!`, 'success');
    }
  }
};

// Initialize file upload
fileUpload.init();

// ==== Leaderboard Sort ====
function sortLeaderboard(column) {
  const table = document.getElementById('leaderboard-table');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const isAscending = !table.getAttribute('data-sort-asc');

  table.setAttribute('data-sort-asc', isAscending);

  let columnIndex = 0;
  switch(column) {
    case 'rank': columnIndex = 0; break;
    case 'name': columnIndex = 1; break;
    case 'points': columnIndex = 3; break;
  }

  rows.sort((a, b) => {
    let aVal = a.querySelectorAll('td')[columnIndex].textContent.trim();
    let bVal = b.querySelectorAll('td')[columnIndex].textContent.trim();

    if (column === 'points') {
      aVal = parseInt(aVal.replace(/,/g, '')) || 0;
      bVal = parseInt(bVal.replace(/,/g, '')) || 0;
    }

    if (isAscending) {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  rows.forEach(row => tbody.appendChild(row));
}

// ==== Search & Filter ====
function filterTableBySearch(searchInputId, tableId, columnIndex = 0) {
  const searchInput = document.getElementById(searchInputId);
  const table = document.getElementById(tableId);

  if (searchInput && table) {
    searchInput.addEventListener('keyup', function() {
      const searchTerm = this.value.toLowerCase();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach(row => {
        const cellText = row.querySelectorAll('td')[columnIndex]?.textContent.toLowerCase();
        if (cellText && cellText.includes(searchTerm)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }
}

// ==== Local Storage Helpers ====
const storage = {
  set: function(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  },

  get: function(key) {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  },

  remove: function(key) {
    localStorage.removeItem(key);
  },

  clear: function() {
    localStorage.clear();
  }
};

// ==== Session Management ====
function setUserSession(userData) {
  storage.set('user', userData);
}

function getUserSession() {
  return storage.get('user');
}

function clearUserSession() {
  storage.remove('user');
  window.location.href = 'student-login/index.html';
}

// Check if user is logged in
function checkUserLogin(requiredRole = null) {
  const user = getUserSession();

  if (!user) {
    window.location.href = '/student-login/index.html';
    return false;
  }

  if (requiredRole && user.role !== requiredRole) {
    window.location.href = '/dashboard/index.html';
    return false;
  }

  return true;
}

// Update user dashboard display
function updateUserDisplay() {
  const user = getUserSession();
  const userDisplay = document.getElementById('user-display');
  const logoutBtn = document.getElementById('logout-btn');

  if (user && userDisplay) {
    userDisplay.textContent = `Welcome, ${user.name}!`;
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', clearUserSession);
  }
}

updateUserDisplay();

// ==== Export for use in HTML ====
window.app = {
  validateField,
  showAlert,
  sortLeaderboard,
  filterTableBySearch,
  setUserSession,
  getUserSession,
  clearUserSession,
  checkUserLogin,
  storage
};
