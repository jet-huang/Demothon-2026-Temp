const tripsEl = document.getElementById("trips");

function toast(msg) {
  let el = document.querySelector(".toast");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2400);
}

function tripCard(trip) {
  const card = document.createElement("article");
  card.className = "trip-card";
  // Build the mobile URL from the page's own origin so it works regardless of
  // how KIOSK_HOST_URL is configured server-side.
  const mobileHref = `${window.location.origin}/m/${encodeURIComponent(trip.traveler_id)}`;
  card.innerHTML = `
    <h2>${trip.summary.destination_city}</h2>
    <div class="trip-meta">
      <div><strong>Dates:</strong> ${trip.summary.start_date} → ${trip.summary.end_date}</div>
      <div><strong>Outbound:</strong> ${trip.summary.outbound_flight} (${trip.summary.origin_iata} → ${trip.summary.destination_iata})</div>
      <div><strong>Return:</strong> ${trip.summary.return_flight} (${trip.summary.destination_iata} → ${trip.summary.origin_iata})</div>
    </div>
    <div class="trip-qr" role="link" tabindex="0" title="Open the phone-frame for this trip">${trip.qr_svg}</div>
    <a class="trip-open-link" href="${mobileHref}" target="_blank" rel="noopener">Open in this browser →</a>
    <button class="chaos-btn" data-trip="${trip.trip_id}">Make something happen.</button>
  `;
  const qrEl = card.querySelector(".trip-qr");
  const openMobile = () => window.open(mobileHref, "_blank", "noopener");
  qrEl.addEventListener("click", openMobile);
  qrEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openMobile();
    }
  });
  card.querySelector(".chaos-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    onChaos(e.target, trip.trip_id);
  });
  return card;
}

async function onChaos(btn, tripId) {
  btn.disabled = true;
  try {
    const r = await fetch(`/api/trips/${encodeURIComponent(tripId)}/chaos`, { method: "POST" });
    if (!r.ok) {
      const body = await r.json().catch(() => ({ detail: r.statusText }));
      toast(body.detail || `error ${r.status}`);
      btn.disabled = false;
      return;
    }
    toast("Delay injected. Watch the phone.");
    setTimeout(() => { btn.disabled = false; }, 30_000);
  } catch (err) {
    toast(`network error: ${err}`);
    btn.disabled = false;
  }
}

async function bootSession() {
  const r = await fetch("/api/session", { method: "POST" });
  if (!r.ok) {
    tripsEl.textContent = "Failed to generate session.";
    return;
  }
  const trips = await r.json();
  tripsEl.innerHTML = "";
  trips.forEach((trip) => tripsEl.appendChild(tripCard(trip)));
}

bootSession();
