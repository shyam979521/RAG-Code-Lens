const sidebar = document.querySelector('.sidebar');
const collapseButton = document.querySelector('[data-sidebar-collapse]');
const mobileButton = document.querySelector('[data-mobile-menu]');
const dashboardContent = document.querySelector('[data-dashboard-content]');
const placeholder = document.querySelector('[data-placeholder-screen]');
const placeholderTitle = document.querySelector('[data-placeholder-title]');
const placeholderDescription = document.querySelector('[data-placeholder-description]');
const breadcrumb = document.querySelector('[data-breadcrumb]');

collapseButton?.addEventListener('click', () => document.body.classList.toggle('sidebar-collapsed'));
mobileButton?.addEventListener('click', () => sidebar?.classList.toggle('open'));
document.querySelectorAll('[data-placeholder]').forEach((item) => item.addEventListener('click', () => {
  const { placeholder: title, description } = item.dataset;
  dashboardContent.hidden = true;
  placeholder.classList.add('visible');
  placeholderTitle.textContent = title;
  placeholderDescription.textContent = description;
  breadcrumb.textContent = title;
  document.querySelectorAll('.side-link').forEach((link) => link.classList.remove('active'));
  item.classList.add('active');
  sidebar?.classList.remove('open');
}));
document.querySelectorAll('[data-dashboard-link]').forEach((item) => item.addEventListener('click', () => {
  dashboardContent.hidden = false;
  placeholder.classList.remove('visible');
  breadcrumb.textContent = 'Dashboard';
  document.querySelectorAll('.side-link').forEach((link) => link.classList.remove('active'));
  item.classList.add('active');
  sidebar?.classList.remove('open');
}));
document.querySelectorAll('.delete-project-btn, .delete-file-btn').forEach((button) => button.addEventListener('click', (event) => {
  if (!window.confirm(button.dataset.confirm || 'Delete this item? This cannot be undone.')) event.preventDefault();
}));
