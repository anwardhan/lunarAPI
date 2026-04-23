const state = {
  dashboard: null,
  selectedTripId: null,
};

const elements = {
  loginPanel: document.getElementById("loginPanel"),
  portalApp: document.getElementById("portalApp"),
  stateMessage: document.getElementById("stateMessage"),
  loginForm: document.getElementById("loginForm"),
  loginError: document.getElementById("loginError"),
  passwordInput: document.getElementById("passwordInput"),
  logoutButton: document.getElementById("logoutButton"),
  tripCountLabel: document.getElementById("tripCountLabel"),
  tripList: document.getElementById("tripList"),
  tripDetailHeader: document.getElementById("tripDetailHeader"),
  tripMetrics: document.getElementById("tripMetrics"),
  routePanel: document.getElementById("routePanel"),
  tripPhotoGrid: document.getElementById("tripPhotoGrid"),
  recentPhotoGrid: document.getElementById("recentPhotoGrid"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await response.json();
  }

  if (!response.ok) {
    const message = payload?.detail || "Request failed";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return payload;
}

function setVisibility({ showLogin = false, showApp = false, showMessage = false, message = "" }) {
  elements.loginPanel.classList.toggle("hidden", !showLogin);
  elements.portalApp.classList.toggle("hidden", !showApp);
  elements.stateMessage.classList.toggle("hidden", !showMessage);
  elements.logoutButton.classList.toggle("hidden", !showApp);
  if (showMessage) {
    elements.stateMessage.textContent = message;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDateTime(value) {
  if (!value) return "Not set";
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDistance(value) {
  if (value == null) return "Not reported";
  return `${(value / 1000).toFixed(1)} km`;
}

function renderTripList() {
  const trips = state.dashboard?.trips || [];
  elements.tripCountLabel.textContent = `${trips.length} ${trips.length === 1 ? "trip" : "trips"}`;

  if (!trips.length) {
    elements.tripList.innerHTML = `<div class="state-panel">No trips have been synced yet.</div>`;
    return;
  }

  elements.tripList.innerHTML = trips
    .map((trip) => {
      const isActive = trip.trip_id === state.selectedTripId;
      const submissionCount = trip.sticker_submission_count + trip.odometer_submission_count;
      return `
        <button class="trip-card ${isActive ? "active" : ""}" type="button" data-trip-id="${escapeHtml(trip.trip_id)}">
          <div class="trip-card-header">
            <span class="trip-card-title">${escapeHtml(trip.driver.display_name || trip.driver.driver_id)}</span>
            <span class="pill ${trip.status === "active" ? "" : "pending"}">${escapeHtml(trip.status)}</span>
          </div>
          <div class="trip-card-subtitle">${escapeHtml(trip.driver.email || trip.driver.driver_id)}</div>
          <div class="trip-card-meta">
            <span class="meta-text">${escapeHtml(formatDateTime(trip.started_at))}</span>
            <span class="meta-text">${trip.point_count} points</span>
          </div>
          <div class="badge-row">
            <div class="badge">
              <strong>${escapeHtml(formatDistance(trip.total_distance_meters || trip.device_distance_meters))}</strong>
              <span>Distance</span>
            </div>
            <div class="badge">
              <strong>${submissionCount}</strong>
              <span>Photos</span>
            </div>
          </div>
        </button>
      `;
    })
    .join("");

  elements.tripList.querySelectorAll("[data-trip-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedTripId = button.getAttribute("data-trip-id");
      renderTripList();
      await loadTripDetail(state.selectedTripId);
    });
  });
}

function renderTripMetrics(trip) {
  const metrics = [
    { label: "Status", value: trip.status },
    { label: "Distance", value: formatDistance(trip.total_distance_meters || trip.device_distance_meters) },
    { label: "Points", value: String(trip.point_count) },
    { label: "Photos", value: String(trip.sticker_submission_count + trip.odometer_submission_count) },
    { label: "Started", value: formatDateTime(trip.started_at) },
    { label: "Ended", value: formatDateTime(trip.ended_at) },
  ];

  elements.tripMetrics.innerHTML = metrics
    .map(
      (metric) => `
        <div class="metric">
          <strong>${escapeHtml(metric.value)}</strong>
          <span>${escapeHtml(metric.label)}</span>
        </div>
      `
    )
    .join("");
}

function buildRoutePath(points) {
  if (points.length < 2) return "";

  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLng = Math.min(...longitudes);
  const maxLng = Math.max(...longitudes);
  const latRange = Math.max(maxLat - minLat, 0.00001);
  const lngRange = Math.max(maxLng - minLng, 0.00001);

  return points
    .map((point, index) => {
      const x = 20 + ((point.longitude - minLng) / lngRange) * 560;
      const y = 20 + ((maxLat - point.latitude) / latRange) * 130;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

function renderRoute(points) {
  if (!points.length) {
    elements.routePanel.innerHTML = `<div class="route-empty">No route points were uploaded for this trip.</div>`;
    return;
  }

  const pathData = buildRoutePath(points);
  if (!pathData) {
    elements.routePanel.innerHTML = `
      <div class="route-shell">
        <div class="route-empty">This trip only has a single recorded point.</div>
        <div class="route-summary">
          <span>First point: ${escapeHtml(formatDateTime(points[0].recorded_at))}</span>
        </div>
      </div>
    `;
    return;
  }

  elements.routePanel.innerHTML = `
    <div class="route-shell">
      <svg class="route-chart" viewBox="0 0 600 170" preserveAspectRatio="none" aria-label="Trip route">
        <rect x="0" y="0" width="600" height="170" fill="transparent"></rect>
        <path d="${pathData}" fill="none" stroke="#0b8f7a" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path>
        <circle cx="${pathData.split(" ")[1]}" cy="${pathData.split(" ")[2]}" r="6" fill="#102033"></circle>
      </svg>
      <div class="route-summary">
        <span>${points.length} points</span>
        <span>First point: ${escapeHtml(formatDateTime(points[0].recorded_at))}</span>
        <span>Last point: ${escapeHtml(formatDateTime(points[points.length - 1].recorded_at))}</span>
      </div>
    </div>
  `;
}

function photoCard(photo) {
  const image = photo.image_url
    ? `<img src="${escapeHtml(photo.image_url)}" alt="${escapeHtml(photo.kind)} photo for ${escapeHtml(photo.driver.display_name || photo.driver.driver_id)}" loading="lazy" />`
    : `<div class="photo-placeholder">Image file is not available on this server.</div>`;

  return `
    <article class="photo-card">
      ${image}
      <div class="photo-copy">
        <div class="photo-title">
          <span>${escapeHtml(photo.kind === "sticker" ? "Sticker" : "Odometer")}</span>
          <span class="pill ${photo.review_status === "pending_review" ? "pending" : ""}">${escapeHtml(photo.review_status)}</span>
        </div>
        <div class="meta-text">${escapeHtml(photo.driver.display_name || photo.driver.driver_id)}</div>
        <div class="meta-text">${escapeHtml(formatDateTime(photo.submitted_at))}</div>
        <div class="meta-text">${escapeHtml(photo.trip_id || "No linked trip")}</div>
      </div>
    </article>
  `;
}

function renderPhotoGrid(element, photos, emptyMessage) {
  if (!photos.length) {
    element.innerHTML = `<div class="state-panel">${escapeHtml(emptyMessage)}</div>`;
    return;
  }
  element.innerHTML = photos.map(photoCard).join("");
}

async function loadTripDetail(tripId) {
  const detail = await api(`/portal/api/trips/${encodeURIComponent(tripId)}`);
  const trip = detail.trip;

  elements.tripDetailHeader.innerHTML = `
    <p class="eyebrow">Trip Detail</p>
    <h2>${escapeHtml(trip.driver.display_name || trip.driver.driver_id)}</h2>
    <div class="detail-meta">
      <span class="meta-text">${escapeHtml(trip.driver.email || trip.driver.driver_id)}</span>
      <span class="pill ${trip.status === "active" ? "" : "pending"}">${escapeHtml(trip.status)}</span>
    </div>
  `;

  renderTripMetrics(trip);
  renderRoute(detail.points);
  renderPhotoGrid(elements.tripPhotoGrid, detail.photos, "No sticker or odometer photos are linked to this trip.");
}

async function loadDashboard() {
  try {
    state.dashboard = await api("/portal/api/dashboard");
  } catch (error) {
    if (error.status === 401) {
      setVisibility({ showLogin: true, showApp: false, showMessage: false });
      return;
    }
    if (error.status === 503) {
      setVisibility({
        showLogin: false,
        showApp: false,
        showMessage: true,
        message: error.message,
      });
      return;
    }
    throw error;
  }

  setVisibility({ showLogin: false, showApp: true, showMessage: false });
  renderTripList();
  renderPhotoGrid(
    elements.recentPhotoGrid,
    state.dashboard.recent_photos || [],
    "No sticker or odometer submissions have been uploaded yet."
  );

  if (!state.dashboard.trips.length) {
    elements.tripDetailHeader.innerHTML = `<p class="eyebrow">Trip Detail</p><h2>No trips yet</h2>`;
    elements.tripMetrics.innerHTML = "";
    renderRoute([]);
    renderPhotoGrid(elements.tripPhotoGrid, [], "Trip photos will appear here once trips and submissions are synced.");
    return;
  }

  if (!state.selectedTripId || !state.dashboard.trips.some((trip) => trip.trip_id === state.selectedTripId)) {
    state.selectedTripId = state.dashboard.trips[0].trip_id;
  }
  renderTripList();
  await loadTripDetail(state.selectedTripId);
}

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.loginError.classList.add("hidden");

  try {
    await api("/portal/login", {
      method: "POST",
      body: JSON.stringify({ password: elements.passwordInput.value }),
    });
    elements.passwordInput.value = "";
    await loadDashboard();
  } catch (error) {
    elements.loginError.textContent = error.message;
    elements.loginError.classList.remove("hidden");
  }
});

elements.logoutButton.addEventListener("click", async () => {
  await fetch("/portal/logout", { method: "POST" });
  state.dashboard = null;
  state.selectedTripId = null;
  setVisibility({ showLogin: true, showApp: false, showMessage: false });
});

window.addEventListener("load", async () => {
  try {
    await loadDashboard();
  } catch (error) {
    setVisibility({
      showLogin: false,
      showApp: false,
      showMessage: true,
      message: error.message || "Portal failed to load.",
    });
  }
});
