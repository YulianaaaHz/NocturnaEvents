document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toast").forEach(toast => {
    setTimeout(() => toast.remove(), 4500);
  });

  const tabs = [...document.querySelectorAll(".admin-tab")];
  const panels = [...document.querySelectorAll(".admin-panel")];

  if (tabs.length) {
    const activate = (name) => {
      tabs.forEach(tab => tab.classList.toggle("active", tab.dataset.tab === name));
      panels.forEach(panel => panel.classList.toggle("active", panel.id === "tab-" + name));
    };

    tabs.forEach(tab => {
      tab.addEventListener("click", () => {
        activate(tab.dataset.tab);
        history.replaceState(null, "", "#" + tab.dataset.tab);
      });
    });

    const hash = location.hash.slice(1);
    if (hash && tabs.some(tab => tab.dataset.tab === hash)) {
      activate(hash);
    }
  }

  document.querySelectorAll(".range-input").forEach(input => {
    const output = document.querySelector(`.range-value[data-for="${input.id}"]`);
    if (!output) return;

    const suffix = input.id === "hero_text_width" ? "px" : "%";
    const update = () => output.textContent = input.value + suffix;
    input.addEventListener("input", update);
    update();
  });
});
