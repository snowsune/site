(function () {
  const root = document.getElementById("rumble-now-voting");
  if (!root) return;

  const voteUrl = root.dataset.voteUrl;
  const statusUrl = root.dataset.statusUrl;
  const loggedIn = root.dataset.loggedIn === "1";
  const csrfInput = root.querySelector("[name=csrfmiddlewaretoken]");
  const csrf = csrfInput ? csrfInput.value : "";

  const countdownEl = document.getElementById("rumble-vote-countdown");
  const hintEl = document.getElementById("rumble-vote-hint");
  const leftTally = root.querySelector('[data-tally="left"]');
  const rightTally = root.querySelector('[data-tally="right"]');
  const buttons = Array.from(root.querySelectorAll(".rumble-vote-btn"));

  let endsAtUnix = null;
  let clockSkewMs = 0;
  let pollTimer = null;
  let countdownTimer = null;

  function getCookie(name) {
    const match = document.cookie.match(
      new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)")
    );
    return match ? decodeURIComponent(match[1]) : "";
  }

  function csrfToken() {
    return csrf || getCookie("csrftoken");
  }

  function applyStatus(data) {
    if (!data || data.voting_open === false) {
      if (countdownEl) countdownEl.textContent = "Voting closed! Refresh for the next match!";
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
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
      const rm = m % 60;
      return `Closes in ${h}h ${rm}m`;
    }
    return `Closes in ${m}:${String(s).padStart(2, "0")}`;
  }

  function tickCountdown() {
    if (!countdownEl || endsAtUnix == null) return;
    const nowUnix = Math.floor((Date.now() - clockSkewMs) / 1000);
    const remaining = endsAtUnix - nowUnix;
    countdownEl.textContent = formatRemaining(remaining);
    if (remaining <= 0) {
      buttons.forEach((btn) => {
        btn.disabled = true;
      });
    }
  }

  async function pollStatus() {
    try {
      const resp = await fetch(statusUrl, {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!resp.ok) return;
      const data = await resp.json();
      applyStatus(data);
      tickCountdown();
    } catch (_) {
      /* ignore transient poll errors */
    }
  }

  async function castVote(choice) {
    if (!loggedIn) return;
    buttons.forEach((btn) => {
      btn.disabled = true;
    });
    try {
      const body = new URLSearchParams();
      body.set("choice", choice);
      const resp = await fetch(voteUrl, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken(),
        },
        credentials: "same-origin",
        body: body.toString(),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        if (hintEl) {
          hintEl.textContent = data.error || "Could not cast vote :<";
        }
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
    } catch (_) {
      /* ignore bad boot JSON */
    }
  }

  tickCountdown();
  countdownTimer = setInterval(tickCountdown, 1000);
  pollTimer = setInterval(pollStatus, 4000);
})();
