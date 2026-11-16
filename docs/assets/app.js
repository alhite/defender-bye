// Tabs + "latest release" download link. No framework, no build step.
(function () {
  const tabs = document.querySelectorAll("nav.tabs button");
  const panels = document.querySelectorAll(".panel");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((b) => b.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });

  const REPO = "alhite/defender-bye";
  const links = document.querySelectorAll("[data-download-latest]");
  if (links.length === 0) return;

  fetch(`https://api.github.com/repos/${REPO}/releases/latest`)
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((release) => {
      const asset = (release.assets || []).find((a) => a.name.endsWith(".exe"));
      const url = asset ? asset.browser_download_url : release.html_url;
      const label = asset ? `${release.tag_name}` : null;
      links.forEach((a) => {
        a.href = url;
        if (label) {
          const tag = a.querySelector("[data-version]");
          if (tag) tag.textContent = label;
        }
      });
    })
    .catch(() => {
      // Fallback: plain link to the releases page, already set in the HTML href.
    });
})();
