const STORAGE_KEY = "bahamutAudioCensus.v3";
const API_STATE_URL = "/api/state";
const PUBLIC_MODE = !new URLSearchParams(location.search).has("admin") && location.hash !== "#admin";
const RECORDS_PAGE_SIZE = 8;

const deviceTypes = [
  "耳道式耳機",
  "耳罩式耳機",
  "真無線耳機",
  "DAC",
  "耳擴",
  "DAC/耳擴一體機",
  "DAP / 隨身播放器",
  "小尾巴",
  "線材",
  "其他",
];

const starterBrandRows = [
  ["Audio-Technica", "鐵三角", ["ATH"]],
  ["Sennheiser", "森海塞爾", ["聲海", "森海"]],
  ["SONY", "索尼", ["Sony"]],
  ["AKG", "", []],
  ["Beyerdynamic", "拜耳動力", ["拜耳"]],
  ["Grado Labs", "", ["Grado"]],
  ["FOSTEX", "", ["Fostex"]],
  ["Yamaha", "山葉", []],
  ["Meze Audio", "", ["Meze"]],
  ["HIFIMAN", "海菲曼", ["HiFiMAN"]],
  ["final", "", ["Final", "Final Audio"]],
  ["MOONDROP", "水月雨", ["Moondrop"]],
  ["Tangzu", "唐族", ["TANGZU"]],
  ["JVC", "傑偉世", ["Victor", "JVC Victor"]],
  ["Xenns", "", []],
  ["See Audio", "", []],
  ["FiiO", "飛傲", ["FIIO", "Fiio"]],
  ["TOPPING", "拓品", ["Topping"]],
  ["SMSL", "雙木三林", ["S.M.S.L"]],
  ["iFi audio", "", ["ifi", "iFi"]],
  ["Schiit Audio", "", ["Schiit"]],
  ["TEAC", "", ["Teac"]],
  ["LUXMAN", "", ["Luxman"]],
  ["Denafrips", "", []],
  ["Astell&Kern", "", ["AK", "A&K"]],
  ["Shanling", "山靈", []],
  ["iBasso Audio", "", ["iBasso"]],
  ["Cayin", "凱音", []],
  ["Hiby", "", ["HiBy"]],
  ["Luxury&Precision", "樂彼", ["L&P"]],
  ["FOCAL", "", ["Focal"]],
  ["Campfire Audio", "", ["Campfire"]],
  ["RME", "", []],
  ["Chord Electronics", "", ["Chord"]],
  ["STAX", "", ["Stax"]],
  ["Shure", "舒爾", []],
].sort((a, b) => a[0].localeCompare(b[0], "zh-Hant"));

const starterBrands = starterBrandRows.map(([englishName, chineseName, aliases], index) => ({
  id: `brand-${index + 1}`,
  englishName,
  chineseName,
  aliases,
  status: "approved",
}));

let state = { brands: starterBrands, entries: [] };
let currentDevices = [];
let lastPost = "";
let editingEntryId = null;
let historyFilterBahamutId = "";
let recordSearchQuery = "";
let recordPage = 1;
let apiAvailable = false;

const els = {
  status: document.querySelector("#connection-status"),
  tabs: document.querySelectorAll(".tab"),
  views: document.querySelectorAll(".view"),
  bahamutId: document.querySelector("#bahamut-id"),
  generalNote: document.querySelector("#general-note"),
  deviceType: document.querySelector("#device-type"),
  brandInput: document.querySelector("#brand-input"),
  brandOptions: document.querySelector("#brand-options"),
  modelInput: document.querySelector("#model-input"),
  deviceNote: document.querySelector("#device-note"),
  addDevice: document.querySelector("#add-device"),
  clearDevice: document.querySelector("#clear-device"),
  deviceList: document.querySelector("#device-list"),
  deviceCount: document.querySelector("#device-count"),
  resetCurrent: document.querySelector("#reset-current"),
  submitEntry: document.querySelector("#submit-entry"),
  historyBahamutId: document.querySelector("#history-bahamut-id"),
  findMyEntries: document.querySelector("#find-my-entries"),
  myEntriesList: document.querySelector("#my-entries-list"),
  editingBadge: document.querySelector("#editing-badge"),
  postOutput: document.querySelector("#post-output"),
  copyPost: document.querySelector("#copy-post"),
  recordSearch: document.querySelector("#record-search"),
  recordsSummary: document.querySelector("#records-summary"),
  recordList: document.querySelector("#record-list"),
  recordPagination: document.querySelector("#record-pagination"),
  recordModal: document.querySelector("#record-modal"),
  recordModalBackdrop: document.querySelector("#record-modal-backdrop"),
  recordModalClose: document.querySelector("#record-modal-close"),
  recordModalMeta: document.querySelector("#record-modal-meta"),
  recordModalCount: document.querySelector("#record-modal-count"),
  recordModalDevices: document.querySelector("#record-modal-devices"),
  recordModalNote: document.querySelector("#record-modal-note"),
  loadSample: document.querySelector("#load-sample"),
  exportCsv: document.querySelector("#export-csv"),
  exportJson: document.querySelector("#export-json"),
  metricEntries: document.querySelector("#metric-entries"),
  metricDevices: document.querySelector("#metric-devices"),
  metricBrands: document.querySelector("#metric-brands"),
  metricPending: document.querySelector("#metric-pending"),
  typeRank: document.querySelector("#type-rank"),
  brandTotalRank: document.querySelector("#brand-total-rank"),
  pendingBrandRank: document.querySelector("#pending-brand-rank"),
  modelRank: document.querySelector("#model-rank"),
  overEarTop10: document.querySelector("#over-ear-top10"),
  iemTop10: document.querySelector("#iem-top10"),
  desktopFrontendTop10: document.querySelector("#desktop-frontend-top10"),
  portableFrontendTop10: document.querySelector("#portable-frontend-top10"),
  pendingBrands: document.querySelector("#pending-brands"),
  brandForm: document.querySelector("#brand-form"),
  brandEn: document.querySelector("#brand-en"),
  brandZh: document.querySelector("#brand-zh"),
  brandAliases: document.querySelector("#brand-aliases"),
  brandTable: document.querySelector("#brand-table"),
};

init();

async function init() {
  document.body.classList.toggle("is-admin", !PUBLIC_MODE);
  state = await loadState();
  deviceTypes.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    els.deviceType.append(option);
  });

  bindEvents();
  renderAll();
  await saveState();
}

function bindEvents() {
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => showView(tab.dataset.view));
  });

  els.addDevice.addEventListener("click", addCurrentDevice);
  els.clearDevice.addEventListener("click", clearDeviceInputs);
  els.resetCurrent.addEventListener("click", resetCurrentEntry);
  els.submitEntry.addEventListener("click", submitEntry);
  els.findMyEntries.addEventListener("click", findMyEntries);
  els.copyPost.addEventListener("click", copyPost);
  els.recordSearch.addEventListener("input", () => {
    recordSearchQuery = els.recordSearch.value.trim();
    recordPage = 1;
    renderRecords();
  });
  els.recordModalClose.addEventListener("click", closeRecordModal);
  els.recordModalBackdrop.addEventListener("click", closeRecordModal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.recordModal.hidden) closeRecordModal();
  });
  els.loadSample.addEventListener("click", loadSample);
  els.exportCsv.addEventListener("click", exportCsv);
  els.exportJson.addEventListener("click", exportJson);
  els.brandForm.addEventListener("submit", addApprovedBrand);
}

async function loadState() {
  try {
    const response = await fetch(API_STATE_URL, { cache: "no-store" });
    if (!response.ok) throw new Error("API unavailable");
    const parsed = await response.json();
    apiAvailable = true;
    updateConnectionStatus();
    return normalizeState(parsed);
  } catch {
    apiAvailable = false;
    updateConnectionStatus();
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { brands: starterBrands, entries: [] };
    try {
      return normalizeState(JSON.parse(raw));
    } catch {
      return { brands: starterBrands, entries: [] };
    }
  }
}

async function saveState(options = {}) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  if (!apiAvailable) return;

  try {
    if (!options.replace) {
      const latest = await fetch(API_STATE_URL, { cache: "no-store" });
      if (latest.ok) {
        state = mergeStates(normalizeState(await latest.json()), state);
      }
    }

    const response = await fetch(API_STATE_URL, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    if (!response.ok) throw new Error("Save failed");
  } catch {
    apiAvailable = false;
    updateConnectionStatus();
  }
}

function mergeStates(baseState, incomingState) {
  return {
    brands: mergeBrandLists(baseState.brands, incomingState.brands),
    entries: mergeEntryLists(baseState.entries, incomingState.entries),
  };
}

function mergeBrandLists(baseBrands, incomingBrands) {
  const byKey = new Map();
  [...baseBrands, ...incomingBrands].forEach((brand) => {
    const key = brand.id || normalize(brand.englishName);
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, { ...brand, aliases: [...(brand.aliases || [])] });
      return;
    }
    byKey.set(key, {
      ...existing,
      ...brand,
      chineseName: brand.chineseName || existing.chineseName,
      aliases: uniqueValues([...(existing.aliases || []), ...(brand.aliases || [])]),
      status: brand.status || existing.status,
    });
  });
  return [...byKey.values()];
}

function mergeEntryLists(baseEntries, incomingEntries) {
  const byId = new Map();
  [...baseEntries, ...incomingEntries].forEach((entry) => {
    const existing = byId.get(entry.id);
    if (!existing) {
      byId.set(entry.id, entry);
      return;
    }
    const existingTime = new Date(existing.updatedAt || existing.createdAt).getTime();
    const entryTime = new Date(entry.updatedAt || entry.createdAt).getTime();
    byId.set(entry.id, entryTime >= existingTime ? entry : existing);
  });
  return [...byId.values()];
}

function updateConnectionStatus() {
  if (apiAvailable) {
    els.status.textContent = "已連線到主辦端，送出的資料會集中保存。";
    els.status.classList.remove("is-warning");
    return;
  }
  els.status.textContent = "目前是本機模式。若要給其他人填寫，請用 server.py 啟動。";
  els.status.classList.add("is-warning");
}

function normalizeState(raw) {
  const parsed = raw && typeof raw === "object" ? raw : {};
  return {
    brands: mergeStarterBrands(Array.isArray(parsed.brands) ? parsed.brands : []),
    entries: Array.isArray(parsed.entries) ? parsed.entries.map(normalizeEntry).filter(Boolean) : [],
  };
}

function normalizeEntry(entry) {
  if (!entry || !Array.isArray(entry.devices)) return null;
  return {
    id: entry.id || createId(),
    bahamutId: entry.bahamutId || "",
    generalNote: entry.generalNote || "",
    devices: entry.devices.map((device) => ({
      id: device.id || createId(),
      type: normalizeDeviceType(device.type),
      brandId: device.brandId,
      brandName: device.brandName || "未命名品牌",
      model: device.model || "",
      note: device.note || "",
    })),
    createdAt: entry.createdAt || new Date().toISOString(),
    updatedAt: entry.updatedAt || entry.createdAt || new Date().toISOString(),
  };
}

function normalizeDeviceType(type) {
  return deviceTypes.includes(type) ? type : "其他";
}

function mergeStarterBrands(existingBrands) {
  const byName = new Map();

  existingBrands.forEach((brand) => {
    if (!brand || !brand.englishName) return;
    byName.set(normalize(brand.englishName), {
      id: brand.id || createId(),
      englishName: brand.englishName,
      chineseName: brand.chineseName || "",
      aliases: Array.isArray(brand.aliases) ? brand.aliases : [],
      status: brand.status || "approved",
    });
  });

  starterBrands.forEach((starter) => {
    const key = normalize(starter.englishName);
    const existing = byName.get(key);
    if (!existing) {
      byName.set(key, { ...starter });
      return;
    }
    byName.set(key, {
      ...starter,
      ...existing,
      chineseName: existing.chineseName || starter.chineseName,
      aliases: uniqueValues([...(existing.aliases || []), ...(starter.aliases || [])]),
      status: existing.status || "approved",
    });
  });

  return [...byName.values()];
}

function renderAll() {
  renderBrandOptions();
  renderCurrentDevices();
  renderEditingBadge();
  renderMyEntriesList([]);
  renderRecords();
  renderStats();
  renderAdmin();
}

function showView(name) {
  if (name === "admin" && PUBLIC_MODE) return;
  els.tabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.view === name));
  els.views.forEach((view) => view.classList.toggle("is-active", view.id === `view-${name}`));
  if (name === "records") renderRecords();
  if (name === "stats") renderStats();
  if (name === "admin") renderAdmin();
}

function approvedBrands() {
  return state.brands.filter((brand) => brand.status === "approved");
}

function pendingBrands() {
  return state.brands.filter((brand) => brand.status === "pending");
}

function displayBrand(brand) {
  if (!brand) return "";
  return brand.chineseName ? `${brand.englishName} ${brand.chineseName}` : brand.englishName;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function normalizeBrandKey(value) {
  return normalize(value).replace(/[\s\-_.・．。&＋+]+/g, "");
}

function uniqueValues(values) {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
}

function findBrand(query) {
  const needle = normalize(query);
  const brandKey = normalizeBrandKey(query);
  if (!needle) return null;

  return state.brands.find((brand) => {
    if (["rejected", "merged"].includes(brand.status)) return false;
    const values = [brand.englishName, brand.chineseName, displayBrand(brand), ...(brand.aliases || [])];
    return values.some((value) => normalize(value) === needle || normalizeBrandKey(value) === brandKey);
  });
}

function renderBrandOptions() {
  els.brandOptions.replaceChildren();
  approvedBrands()
    .sort((a, b) => displayBrand(a).localeCompare(displayBrand(b), "zh-Hant"))
    .forEach((brand) => {
      const option = document.createElement("option");
      option.value = displayBrand(brand);
      els.brandOptions.append(option);
    });
}

async function addCurrentDevice() {
  const brandText = els.brandInput.value.trim();
  const model = els.modelInput.value.trim();

  if (!brandText || !model) {
    alert("請填寫品牌與型號。");
    return;
  }

  let brand = findBrand(brandText);
  if (!brand) brand = createPendingBrand(brandText);

  currentDevices.push({
    id: createId(),
    type: els.deviceType.value,
    brandId: brand.id,
    brandName: displayBrand(brand),
    model,
    note: els.deviceNote.value.trim(),
  });

  await saveState();
  renderBrandOptions();
  renderCurrentDevices();
  renderAdmin();
  clearDeviceInputs();
}

function createPendingBrand(rawName) {
  const existing = findBrand(rawName);
  if (existing) return existing;

  const brand = {
    id: createId(),
    englishName: rawName,
    chineseName: "",
    aliases: [rawName],
    status: "pending",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  state.brands.push(brand);
  return brand;
}

function clearDeviceInputs() {
  els.brandInput.value = "";
  els.modelInput.value = "";
  els.deviceNote.value = "";
  els.brandInput.focus();
}

function renderCurrentDevices() {
  els.deviceList.replaceChildren();
  els.deviceCount.textContent = currentDevices.length;

  const template = document.querySelector("#device-item-template");
  currentDevices.forEach((device) => {
    const item = template.content.cloneNode(true);
    item.querySelector(".device-name").textContent = `${device.brandName} ${device.model}`;
    item.querySelector(".device-meta").textContent = [device.type, device.note].filter(Boolean).join(" / ");
    item.querySelector("button").addEventListener("click", () => {
      currentDevices = currentDevices.filter((candidate) => candidate.id !== device.id);
      renderCurrentDevices();
    });
    els.deviceList.append(item);
  });
}

function resetCurrentEntry() {
  currentDevices = [];
  els.bahamutId.value = "";
  els.generalNote.value = "";
  editingEntryId = null;
  lastPost = "";
  els.postOutput.value = "";
  renderCurrentDevices();
  renderEditingBadge();
}

async function submitEntry() {
  const bahamutId = els.bahamutId.value.trim();
  if (!bahamutId) {
    alert("請填寫巴哈 ID。");
    return;
  }
  if (!currentDevices.length) {
    alert("請至少新增一項設備。");
    return;
  }

  const now = new Date().toISOString();
  const entry = {
    id: editingEntryId || createId(),
    bahamutId,
    generalNote: els.generalNote.value.trim(),
    devices: currentDevices.map((device) => ({ ...device })),
    createdAt: now,
    updatedAt: now,
  };

  if (editingEntryId) {
    const index = state.entries.findIndex((candidate) => candidate.id === editingEntryId);
    if (index >= 0) {
      entry.createdAt = state.entries[index].createdAt;
      state.entries[index] = entry;
    } else {
      state.entries.push(entry);
    }
  } else {
    state.entries.push(entry);
  }

  await saveState();
  lastPost = buildPost(entry);
  els.postOutput.value = lastPost;
  historyFilterBahamutId = bahamutId;
  els.historyBahamutId.value = bahamutId;
  editingEntryId = null;
  currentDevices = [];
  renderCurrentDevices();
  renderEditingBadge();
  renderMyEntriesList(getEntriesByBahamutId(historyFilterBahamutId));
  renderRecords();
  renderStats();
  renderAdmin();
  showView("post");
}

function findMyEntries() {
  const bahamutId = els.historyBahamutId.value.trim();
  historyFilterBahamutId = bahamutId;
  renderMyEntriesList(bahamutId ? getEntriesByBahamutId(bahamutId) : []);
}

function getEntriesByBahamutId(bahamutId) {
  return state.entries
    .filter((entry) => normalize(entry.bahamutId) === normalize(bahamutId))
    .sort((a, b) => new Date(b.updatedAt || b.createdAt) - new Date(a.updatedAt || a.createdAt));
}

function renderMyEntriesList(entries) {
  els.myEntriesList.replaceChildren();

  entries.forEach((entry) => {
    const item = document.createElement("article");
    item.className = "history-item";
    const timeText = new Date(entry.updatedAt || entry.createdAt).toLocaleString("zh-TW", { hour12: false });

    item.innerHTML = `
      <p><strong></strong> | <span class="history-count"></span></p>
      <p class="history-time"></p>
      <div class="history-actions">
        <button class="ghost-button history-edit" type="button">載入編輯</button>
        <button class="danger-button history-delete" type="button">刪除</button>
      </div>
    `;

    item.querySelector("strong").textContent = entry.bahamutId;
    item.querySelector(".history-count").textContent = `${entry.devices.length} 項設備`;
    item.querySelector(".history-time").textContent = timeText;
    item.querySelector(".history-edit").addEventListener("click", () => loadEntryForEdit(entry.id));
    item.querySelector(".history-delete").addEventListener("click", () => deleteEntry(entry.id));
    els.myEntriesList.append(item);
  });
}

function getRecordGroups() {
  const query = normalize(recordSearchQuery);
  const byBahamutId = new Map();

  state.entries.forEach((entry) => {
    const key = normalize(entry.bahamutId);
    if (!key || (query && !key.includes(query))) return;

    const existing = byBahamutId.get(key);
    if (!existing) {
      byBahamutId.set(key, {
        id: key,
        bahamutId: entry.bahamutId,
        generalNote: entry.generalNote || "",
        devices: [...entry.devices],
        createdAt: entry.createdAt || entry.updatedAt,
        updatedAt: entry.updatedAt || entry.createdAt,
        entryCount: 1,
      });
      return;
    }

    existing.devices.push(...entry.devices);
    existing.generalNote = mergeNotes(existing.generalNote, entry.generalNote);
    existing.entryCount += 1;

    if (new Date(entry.createdAt || entry.updatedAt) > new Date(existing.createdAt || existing.updatedAt)) {
      existing.createdAt = entry.createdAt || entry.updatedAt;
    }
    if (new Date(entry.updatedAt || entry.createdAt) > new Date(existing.updatedAt || existing.createdAt)) {
      existing.updatedAt = entry.updatedAt || entry.createdAt;
    }
  });

  return [...byBahamutId.values()]
    .map((group) => ({ ...group, devices: uniqueDevices(group.devices) }))
    .sort((a, b) => new Date(b.createdAt || b.updatedAt) - new Date(a.createdAt || a.updatedAt));
}

function mergeNotes(left, right) {
  return uniqueValues([...(left || "").split("\n"), right]).join("\n");
}

function uniqueDevices(devices) {
  const byKey = new Map();
  devices.forEach((device) => {
    const key = [device.type, device.brandName, device.model, device.note].map(normalize).join("|");
    if (!byKey.has(key)) byKey.set(key, { ...device });
  });
  return [...byKey.values()];
}

function formatEntryTime(entry) {
  const value = entry.createdAt || entry.updatedAt;
  if (!value) return "未記錄";
  return new Date(value).toLocaleString("zh-TW", { hour12: false });
}

function renderRecords() {
  const groups = getRecordGroups();
  const totalPages = Math.max(1, Math.ceil(groups.length / RECORDS_PAGE_SIZE));
  recordPage = Math.min(Math.max(recordPage, 1), totalPages);

  const start = (recordPage - 1) * RECORDS_PAGE_SIZE;
  const pageGroups = groups.slice(start, start + RECORDS_PAGE_SIZE);

  els.recordsSummary.textContent = groups.length
    ? `共 ${groups.length} 位使用者，第 ${recordPage} / ${totalPages} 頁`
    : recordSearchQuery
      ? "找不到符合的巴哈 ID。"
      : "目前還沒有任何紀錄。";

  els.recordList.replaceChildren();
  pageGroups.forEach((group) => {
    els.recordList.append(createRecordCard(group));
  });

  renderRecordPagination(totalPages);
}

function createRecordCard(entry) {
  const card = document.createElement("article");
  card.className = "record-card";

  const title = document.createElement("div");
  title.className = "record-card-title";

  const identity = document.createElement("div");
  const name = document.createElement("h3");
  name.textContent = entry.bahamutId || "未填寫";
  const meta = document.createElement("p");
  meta.textContent = `提交時間：${formatEntryTime(entry)}`;
  identity.append(name, meta);

  const viewButton = document.createElement("button");
  viewButton.className = "primary-button";
  viewButton.type = "button";
  viewButton.textContent = "查看";
  viewButton.addEventListener("click", () => openRecordModal(entry));

  title.append(identity, viewButton);

  const count = document.createElement("p");
  count.className = "record-count";
  count.textContent = `設備數：${entry.devices.length}`;

  card.append(title, count);

  return card;
}

function openRecordModal(entry) {
  els.recordModalMeta.textContent = `${entry.bahamutId}｜提交時間：${formatEntryTime(entry)}`;
  els.recordModalCount.textContent = `設備數：${entry.devices.length}`;

  els.recordModalDevices.replaceChildren();
  entry.devices.forEach((device) => {
    const item = document.createElement("li");
    const note = device.note ? `（${device.note}）` : "";
    item.textContent = `${device.type}｜${device.brandName} ${device.model}${note}`;
    els.recordModalDevices.append(item);
  });

  if (entry.generalNote) {
    els.recordModalNote.hidden = false;
    els.recordModalNote.textContent = `備註：${entry.generalNote}`;
  } else {
    els.recordModalNote.hidden = true;
    els.recordModalNote.textContent = "";
  }

  els.recordModal.hidden = false;
  document.body.classList.add("modal-open");
}

function closeRecordModal() {
  els.recordModal.hidden = true;
  document.body.classList.remove("modal-open");
}

function renderRecordPagination(totalPages) {
  els.recordPagination.replaceChildren();
  if (totalPages <= 1) return;

  const previous = document.createElement("button");
  previous.className = "ghost-button";
  previous.type = "button";
  previous.textContent = "上一頁";
  previous.disabled = recordPage === 1;
  previous.addEventListener("click", () => {
    recordPage -= 1;
    renderRecords();
  });

  const pageText = document.createElement("span");
  pageText.textContent = `${recordPage} / ${totalPages}`;

  const next = document.createElement("button");
  next.className = "ghost-button";
  next.type = "button";
  next.textContent = "下一頁";
  next.disabled = recordPage === totalPages;
  next.addEventListener("click", () => {
    recordPage += 1;
    renderRecords();
  });

  els.recordPagination.append(previous, pageText, next);
}

function loadEntryForEdit(entryId) {
  const entry = state.entries.find((candidate) => candidate.id === entryId);
  if (!entry) return;

  editingEntryId = entry.id;
  els.bahamutId.value = entry.bahamutId;
  els.generalNote.value = entry.generalNote || "";
  currentDevices = entry.devices.map((device) => ({ ...device, id: device.id || createId() }));
  renderCurrentDevices();
  renderEditingBadge();
  showView("form");
}

async function deleteEntry(entryId) {
  const entry = state.entries.find((candidate) => candidate.id === entryId);
  if (!entry) return;

  const confirmed = window.confirm(`確定要刪除 ${entry.bahamutId} 的這筆紀錄嗎？`);
  if (!confirmed) return;

  state.entries = state.entries.filter((candidate) => candidate.id !== entryId);
  await saveState({ replace: true });

  if (editingEntryId === entryId) resetCurrentEntry();
  renderMyEntriesList(historyFilterBahamutId ? getEntriesByBahamutId(historyFilterBahamutId) : []);
  renderRecords();
  renderStats();
  renderAdmin();
}

function renderEditingBadge() {
  if (!editingEntryId) {
    els.editingBadge.hidden = true;
    els.editingBadge.textContent = "";
    els.submitEntry.textContent = "送出並產生貼文";
    return;
  }

  const entry = state.entries.find((candidate) => candidate.id === editingEntryId);
  els.editingBadge.hidden = false;
  els.editingBadge.textContent = entry ? `正在編輯：${entry.bahamutId}` : "正在編輯舊資料";
  els.submitEntry.textContent = "儲存修改並更新貼文";
}

function buildPost(entry) {
  const groups = groupBy(entry.devices, (device) => device.type);
  const lines = ["2026 巴哈耳機普查", "", `巴哈 ID：${entry.bahamutId}`, ""];

  deviceTypes.forEach((type) => {
    const devices = groups.get(type) || [];
    if (!devices.length) return;
    lines.push(`${type}：`);
    devices.forEach((device) => {
      const note = device.note ? `（${device.note}）` : "";
      lines.push(`- ${device.brandName} ${device.model}${note}`);
    });
    lines.push("");
  });

  if (entry.generalNote) {
    lines.push("備註：");
    lines.push(entry.generalNote);
    lines.push("");
  }

  return lines.join("\n").trim();
}

async function copyPost() {
  if (!els.postOutput.value.trim()) {
    alert("目前沒有可複製的貼文。");
    return;
  }

  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(els.postOutput.value);
  } else {
    els.postOutput.focus();
    els.postOutput.select();
    document.execCommand("copy");
    window.getSelection().removeAllRanges();
  }

  els.copyPost.textContent = "已複製";
  window.setTimeout(() => {
    els.copyPost.textContent = "複製貼文";
  }, 1200);
}

function groupBy(items, keyGetter) {
  const map = new Map();
  items.forEach((item) => {
    const key = keyGetter(item);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  });
  return map;
}

function flattenDevices() {
  return state.entries.flatMap((entry) =>
    entry.devices.map((device) => ({
      ...device,
      bahamutId: entry.bahamutId,
      createdAt: entry.createdAt,
      updatedAt: entry.updatedAt,
    })),
  );
}

function getBrandById(id) {
  return state.brands.find((brand) => brand.id === id);
}

function isApprovedDevice(device) {
  const brand = getBrandById(device.brandId);
  return !brand || brand.status === "approved";
}

function rankBy(items, keyGetter) {
  const counts = new Map();
  items.forEach((item) => {
    const key = keyGetter(item);
    if (!key) return;
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  return [...counts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-Hant"))
    .slice(0, 10);
}

function renderStats() {
  const devices = flattenDevices();
  const approvedDevices = devices.filter(isApprovedDevice);
  els.metricEntries.textContent = state.entries.length;
  els.metricDevices.textContent = devices.length;
  els.metricBrands.textContent = approvedBrands().length;
  els.metricPending.textContent = pendingBrands().length;

  renderRank(els.typeRank, rankBy(devices, (device) => device.type));
  renderRank(els.brandTotalRank, rankBy(approvedDevices, (device) => device.brandName));
  renderPendingBrandRank();
  renderRank(els.modelRank, rankBy(approvedDevices, (device) => `${device.brandName} ${device.model}`));
  renderCategoryTop10(approvedDevices);
}

function renderPendingBrandRank() {
  const rows = pendingBrands()
    .map((brand) => ({
      label: displayBrand(brand),
      count: flattenDevices().filter((device) => device.brandId === brand.id).length,
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-Hant"));

  renderRank(els.pendingBrandRank, rows);
}

function renderCategoryTop10(devices) {
  renderRank(
    els.overEarTop10,
    rankBy(devices.filter((device) => device.type === "耳罩式耳機"), (device) => device.brandName),
  );
  renderRank(
    els.iemTop10,
    rankBy(devices.filter((device) => device.type === "耳道式耳機"), (device) => device.brandName),
  );
  renderRank(
    els.desktopFrontendTop10,
    rankBy(devices.filter((device) => isDesktopFrontend(device.type)), (device) => device.brandName),
  );
  renderRank(
    els.portableFrontendTop10,
    rankBy(devices.filter((device) => isPortableFrontend(device.type)), (device) => device.brandName),
  );
}

function isDesktopFrontend(type) {
  return ["DAC", "耳擴", "DAC/耳擴一體機"].includes(type);
}

function isPortableFrontend(type) {
  return ["DAP / 隨身播放器", "小尾巴"].includes(type);
}

function renderRank(container, rows) {
  container.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("p");
    empty.textContent = "尚無資料";
    container.append(empty);
    return;
  }

  const max = Math.max(...rows.map((row) => row.count));
  rows.forEach((row) => {
    const wrapper = document.createElement("div");
    wrapper.className = "rank-row";
    wrapper.innerHTML = `
      <div>
        <strong></strong>
        <div class="rank-bar"><span></span></div>
      </div>
      <span></span>
    `;
    wrapper.querySelector("strong").textContent = row.label;
    wrapper.querySelector(".rank-bar span").style.width = `${(row.count / max) * 100}%`;
    wrapper.querySelector("span:last-child").textContent = row.count;
    container.append(wrapper);
  });
}

function renderAdmin() {
  renderPendingBrands();
  renderBrandTable();
}

function renderPendingBrands() {
  els.pendingBrands.replaceChildren();
  const brands = pendingBrands();
  if (!brands.length) {
    const empty = document.createElement("p");
    empty.textContent = "目前沒有待確認品牌。";
    els.pendingBrands.append(empty);
    return;
  }

  brands
    .sort((a, b) => new Date(b.createdAt || b.updatedAt || 0) - new Date(a.createdAt || a.updatedAt || 0))
    .forEach((brand) => {
    const card = document.createElement("article");
    card.className = "admin-card";
    card.innerHTML = `
      <div>
        <strong></strong>
        <span class="pill">pending</span>
      </div>
      <label class="field">
        <span>正式英文名稱</span>
        <input class="pending-en" />
      </label>
      <label class="field">
        <span>中文名稱</span>
        <input class="pending-zh" />
      </label>
      <label class="field">
        <span>Alias</span>
        <input class="pending-aliases" />
      </label>
      <label class="field">
        <span>合併到既有品牌</span>
        <select class="pending-merge">
          <option value="">審核為新品牌</option>
        </select>
      </label>
      <div class="admin-card-actions">
        <button class="primary-button approve" type="button">核准</button>
        <button class="danger-button reject" type="button">拒絕</button>
      </div>
    `;
    card.querySelector("strong").textContent = brand.englishName;
    card.querySelector(".pending-en").value = brand.englishName;
    card.querySelector(".pending-zh").value = brand.chineseName;
    card.querySelector(".pending-aliases").value = (brand.aliases || []).join(", ");
    const mergeSelect = card.querySelector(".pending-merge");
    approvedBrands()
      .sort((a, b) => displayBrand(a).localeCompare(displayBrand(b), "zh-Hant"))
      .forEach((approvedBrand) => {
        const option = document.createElement("option");
        option.value = approvedBrand.id;
        option.textContent = displayBrand(approvedBrand);
        mergeSelect.append(option);
      });
    card.querySelector(".approve").addEventListener("click", () => approvePendingBrand(brand.id, card));
    card.querySelector(".reject").addEventListener("click", () => rejectPendingBrand(brand.id));
      els.pendingBrands.append(card);
    });
}

async function approvePendingBrand(id, card) {
  const brand = state.brands.find((candidate) => candidate.id === id);
  if (!brand) return;
  const mergeTargetId = card.querySelector(".pending-merge").value;
  if (mergeTargetId) {
    await mergePendingBrand(brand, mergeTargetId);
    return;
  }

  brand.englishName = card.querySelector(".pending-en").value.trim() || brand.englishName;
  brand.chineseName = card.querySelector(".pending-zh").value.trim();
  brand.aliases = splitAliases(card.querySelector(".pending-aliases").value);
  brand.status = "approved";
  brand.updatedAt = new Date().toISOString();
  refreshDeviceBrandNames(brand);
  await saveState();
  renderBrandOptions();
  renderCurrentDevices();
  renderStats();
  renderAdmin();
}

async function mergePendingBrand(brand, targetId) {
  const target = state.brands.find((candidate) => candidate.id === targetId && candidate.status === "approved");
  if (!target) return;

  target.aliases = uniqueValues([...(target.aliases || []), brand.englishName, brand.chineseName, ...(brand.aliases || [])]);
  state.entries.forEach((entry) => {
    entry.devices.forEach((device) => {
      if (device.brandId === brand.id) {
        device.brandId = target.id;
        device.brandName = displayBrand(target);
      }
    });
  });
  currentDevices.forEach((device) => {
    if (device.brandId === brand.id) {
      device.brandId = target.id;
      device.brandName = displayBrand(target);
    }
  });
  brand.status = "merged";
  brand.updatedAt = new Date().toISOString();
  await saveState();
  renderBrandOptions();
  renderCurrentDevices();
  renderStats();
  renderAdmin();
}

async function rejectPendingBrand(id) {
  const brand = state.brands.find((candidate) => candidate.id === id);
  if (!brand) return;
  brand.status = "rejected";
  brand.updatedAt = new Date().toISOString();
  await saveState();
  renderStats();
  renderAdmin();
}

function refreshDeviceBrandNames(brand) {
  const nextName = displayBrand(brand);
  state.entries.forEach((entry) => {
    entry.devices.forEach((device) => {
      if (device.brandId === brand.id) device.brandName = nextName;
    });
  });
  currentDevices.forEach((device) => {
    if (device.brandId === brand.id) device.brandName = nextName;
  });
}

async function addApprovedBrand(event) {
  event.preventDefault();
  const englishName = els.brandEn.value.trim();
  if (!englishName) return;

  const existing = findBrand(englishName);
  if (existing) {
    alert("品牌已存在。");
    return;
  }

  state.brands.push({
    id: createId(),
    englishName,
    chineseName: els.brandZh.value.trim(),
    aliases: splitAliases(els.brandAliases.value),
    status: "approved",
  });
  await saveState();
  els.brandForm.reset();
  renderBrandOptions();
  renderStats();
  renderAdmin();
}

function splitAliases(value) {
  return uniqueValues(String(value || "").split(","));
}

function renderBrandTable() {
  els.brandTable.replaceChildren();
  approvedBrands()
    .sort((a, b) => displayBrand(a).localeCompare(displayBrand(b), "zh-Hant"))
    .forEach((brand) => {
      const row = document.createElement("article");
      row.className = "brand-row";
      row.innerHTML = `
        <strong></strong>
        <span></span>
      `;
      row.querySelector("strong").textContent = displayBrand(brand);
      row.querySelector("span").textContent = (brand.aliases || []).join(", ") || "無 alias";
      els.brandTable.append(row);
    });
}

function exportCsv() {
  const header = ["巴哈ID", "送出時間", "更新時間", "設備類型", "品牌", "型號", "備註"];
  const rows = flattenDevices().map((device) => [
    device.bahamutId,
    device.createdAt,
    device.updatedAt,
    device.type,
    device.brandName,
    device.model,
    device.note || "",
  ]);
  downloadFile("bahamut-audio-census.csv", `\uFEFF${toCsv([header, ...rows])}`, "text/csv;charset=utf-8");
}

function toCsv(rows) {
  return rows
    .map((row) =>
      row
        .map((cell) => {
          const value = String(cell ?? "").replaceAll('"', '""');
          return `"${value}"`;
        })
        .join(","),
    )
    .join("\n");
}

function exportJson() {
  downloadFile("bahamut-audio-census.json", JSON.stringify(state, null, 2), "application/json;charset=utf-8");
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function loadSample() {
  const jvc = findBrand("JVC");
  const sennheiser = findBrand("Sennheiser");
  const fiio = findBrand("FiiO");

  els.bahamutId.value = "sample_user";
  els.generalNote.value = "主力系統放在桌上，耳道主要外出使用。";
  currentDevices = [
    {
      id: createId(),
      type: "耳道式耳機",
      brandId: jvc.id,
      brandName: displayBrand(jvc),
      model: "HA-FW02",
      note: "",
    },
    {
      id: createId(),
      type: "耳罩式耳機",
      brandId: sennheiser.id,
      brandName: displayBrand(sennheiser),
      model: "HD800S",
      note: "常用平衡線",
    },
    {
      id: createId(),
      type: "DAC/耳擴一體機",
      brandId: fiio.id,
      brandName: displayBrand(fiio),
      model: "K9 Pro",
      note: "",
    },
  ];
  renderCurrentDevices();
}

function createId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
