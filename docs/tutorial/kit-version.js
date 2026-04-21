// Single source of truth for DOE Starter Kit version across all tutorial pages.
// Updated by: python3 execution/stamp_tutorial_version.py vX.Y.Z
(function () {
  var VERSION = 'v1.55.10';
  document.querySelectorAll('.sidebar-version').forEach(function (el) { el.textContent = VERSION; });
  document.querySelectorAll('.hero-badge').forEach(function (el) {
    el.textContent = el.textContent.replace(/v\d+\.\d+\.\d+/, VERSION);
  });
  document.querySelectorAll('.site-footer').forEach(function (el) {
    el.textContent = el.textContent.replace(/v\d+\.\d+\.\d+/, VERSION);
  });
})();
