document.addEventListener("DOMContentLoaded", () => {
  // 1) Give all your FastAPI forms a common class, e.g. "ajax-form"
  //    <form class="ajax-form" action="/farmer/breeding" method="post">…</form>
  //    <form class="ajax-form" action="/farmer/gestation" method="post">…</form>
  //    etc.

  document.querySelectorAll("form.ajax-form").forEach(form => {
    form.addEventListener("submit", async e => {
      e.preventDefault();

      const data = new FormData(form);
      const body = new URLSearchParams();
      for (let [k, v] of data.entries()) body.append(k, v);

      try {
        const resp = await fetch(form.action, {
          method: form.method.toUpperCase(),
          headers: { "Accept": "application/json" },
          body
        });

        if (!resp.ok) {
          let err = await resp.json().catch(() => null);
          throw new Error(err?.detail || resp.statusText);
        }

        const result = await resp.json();
        // pick a friendly title based on endpoint or form.dataset
        const title = form.dataset.successTitle || "Saved!";
        const msg   = form.dataset.successMsg   || "Your data was recorded.";

        await Swal.fire({ icon: "success", title, text: msg });

        // Reset or reload
        form.reset();
        // if you want to keep that form open, don't reload; otherwise:
        // window.location.reload();
      }
      catch (error) {
        await Swal.fire({ icon: "error", title: "Error", text: error.message });
      }
    });
  });
});

function openDatePicker(id) {
  const input = document.getElementById(id);
  if (input) {
    if (typeof input.showPicker === 'function') {
      input.showPicker();
    } else {
      input.focus();
    }
  }
}