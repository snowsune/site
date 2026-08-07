(function () {
  const root = document.getElementById("rumble-now-voting");
  if (!root) return;

  const voteUrl = root.dataset.voteUrl;
  const streamUrl = root.dataset.streamUrl;
  const loggedIn = root.dataset.loggedIn === "1";
  const csrf = root.querySelector("[name=csrfmiddlewaretoken]")?.value || "";

  const countdownEl = document.getElementById("rumble-vote-countdown");
  const hintEl = document.getElementById("rumble-vote-hint");
  const leftTally = root.querySelector('[data-tally="left"]');
  const rightTally = root.querySelector('[data-tally="right"]');
  const buttons = Array.from(root.querySelectorAll(".rumble-vote-btn"));

  let endsAtUnix = null;
  let clockSkewMs = 0;
  let source = null;

  function applyStatus(data) {
    if (!data || data.voting_open === false) {
      if (countdownEl) {
        countdownEl.textContent = "Voting closed! Refresh for the next match!";
      }
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
      if (source) {
        source.close();
        source = null;
      }
      return;
    }

    if (typeof data.votes_left === "number" && leftTally) {
      leftTally.textContent = String(data.votes_left);
    }
    if (typeof data.votes_right === "number" && rightTally) {
      rightTally.textContent = String(data.votes_right);
    }

    if (data.ends_at_unix) {
      endsAtUnix = data.ends_at_unix;
      if (data.server_now_unix) {
        clockSkewMs = Date.now() - data.server_now_unix * 1000;
      }
    }

    buttons.forEach((btn) => {
      const selected = data.my_choice && btn.dataset.choice === data.my_choice;
      btn.classList.toggle("is-selected", Boolean(selected));
      btn.textContent = selected ? "Your vote!" : "Vote";
      btn.disabled = false;
    });

    if (hintEl && loggedIn && data.my_choice) {
      hintEl.textContent = "Got it! You can switch until it closes~";
    }
  }

  function formatRemaining(seconds) {
    if (seconds <= 0) return "Closing…";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m >= 60) {
      const h = Math.floor(m / 60);
      return `Closes in ${h}h ${m % 60}m`;
    }
    return `Closes in ${m}:${String(s).padStart(2, "0")}`;
  }

  function tickCountdown() {
    if (!countdownEl || endsAtUnix == null) return;
    const remaining =
      endsAtUnix - Math.floor((Date.now() - clockSkewMs) / 1000);
    countdownEl.textContent = formatRemaining(remaining);
    if (remaining <= 0) {
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
    }
  }

  function startStream() {
    if (!streamUrl || typeof EventSource === "undefined") return;
    source = new EventSource(streamUrl);
    source.addEventListener("status", (event) => {
      try {
        applyStatus(JSON.parse(event.data));
        tickCountdown();
      } catch (_) {}
    });
  }

  async function castVote(choice) {
    if (!loggedIn) return;
    buttons.forEach((btn) => {
      btn.disabled = true;
    });
    try {
      const body = new URLSearchParams({ choice });
      const resp = await fetch(voteUrl, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrf,
        },
        credentials: "same-origin",
        cache: "no-store",
        body,
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        if (hintEl) hintEl.textContent = data.error || "Could not cast vote :<";
        buttons.forEach((btn) => {
          btn.disabled = false;
        });
        return;
      }
      applyStatus(data);
      tickCountdown();
    } catch (_) {
      if (hintEl) hintEl.textContent = "Could not cast vote :<";
      buttons.forEach((btn) => {
        btn.disabled = false;
      });
    }
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => castVote(btn.dataset.choice));
  });

  const boot = document.getElementById("vote-status-data");
  if (boot) {
    try {
      applyStatus(JSON.parse(boot.textContent));
    } catch (_) {}
  }

  tickCountdown();
  setInterval(tickCountdown, 1000);
  startStream();
})();
