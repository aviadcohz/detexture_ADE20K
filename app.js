/* ── ADE20k Textures Crops Gallery App ── */

let galleryData = null;
let filteredEntries = [];
let currentPage = 1;
let currentMode = 'crops'; // 'crops' or 'refined'
let groupBySource = false;
const PER_PAGE = 48;

let entryIndex = {};

// ── Data Loading ──
async function loadGallery() {
  if (galleryData) return galleryData;
  try {
    const resp = await fetch('gallery.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
    galleryData = await resp.json();
    entryIndex = {};
    for (const e of galleryData.entries) {
      entryIndex[e.crop_name] = e;
    }
    return galleryData;
  } catch (err) {
    console.error('Failed to load gallery.json:', err);
    document.getElementById('gallery-grid').innerHTML =
      `<p style="color:red;padding:2rem;">Error loading gallery data: ${err.message}</p>`;
    throw err;
  }
}

// ── Init ──
async function initGallery(mode) {
  try {
  currentMode = mode;
  const data = await loadGallery();
  filteredEntries = [...data.entries];

  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const groupToggle = document.getElementById('group-toggle');

  searchInput.addEventListener('input', debounce(() => {
    currentPage = 1;
    applyFilters();
  }, 250));

  sortSelect.addEventListener('change', () => {
    currentPage = 1;
    applyFilters();
  });

  groupToggle.addEventListener('click', () => {
    groupBySource = !groupBySource;
    groupToggle.classList.toggle('active', groupBySource);
    currentPage = 1;
    applyFilters();
  });

  document.getElementById('gallery-grid').addEventListener('click', handleGalleryClick);
  applyFilters();
  } catch (err) {
    console.error('initGallery error:', err);
    const grid = document.getElementById('gallery-grid');
    if (grid && !grid.innerHTML.includes('Error')) {
      grid.innerHTML = `<p style="color:red;padding:2rem;">Gallery init failed: ${err.message}</p>`;
    }
  }
}

// ── Event Delegation ──
function handleGalleryClick(e) {
  const lbTarget = e.target.closest('[data-lightbox]');
  if (lbTarget) {
    e.stopPropagation();
    openLightbox(lbTarget.getAttribute('data-lightbox'), lbTarget.getAttribute('data-caption') || '');
    return;
  }
  const card = e.target.closest('.crop-card');
  if (card && card.dataset.cropName) {
    toggleDetail(card);
  }
}

// ── Expand/Collapse Detail ──
function toggleDetail(card) {
  const cropName = card.dataset.cropName;
  const existing = card.querySelector('.card-detail');

  if (existing) {
    existing.remove();
    card.classList.remove('expanded');
    return;
  }

  const grid = document.getElementById('gallery-grid');
  const prevExpanded = grid.querySelector('.crop-card.expanded');
  if (prevExpanded) {
    const prevDetail = prevExpanded.querySelector('.card-detail');
    if (prevDetail) prevDetail.remove();
    prevExpanded.classList.remove('expanded');
  }

  const entry = entryIndex[cropName];
  if (!entry) return;

  card.classList.add('expanded');
  const detail = document.createElement('div');
  detail.className = 'card-detail';
  detail.innerHTML = renderDetail(entry);
  card.appendChild(detail);
}

// ── Bbox helper: source_box is [y1, x1, y2, x2] ──
function bboxStyle(box, ow, oh) {
  if (!box || box.length < 4) return '';
  const y1 = box[0], x1 = box[1], y2 = box[2], x2 = box[3];
  const left = (x1 / ow * 100).toFixed(2);
  const top = (y1 / oh * 100).toFixed(2);
  const width = ((x2 - x1) / ow * 100).toFixed(2);
  const height = ((y2 - y1) / oh * 100).toFixed(2);
  return `left:${left}%;top:${top}%;width:${width}%;height:${height}%`;
}

// ── Inline bbox overlay HTML ──
function bboxOverlayHtml(e, imgSrc, caption) {
  const style = bboxStyle(e.source_box, e.overlay_w || 256, e.overlay_h || 256);
  return `
    <div class="bbox-container">
      <img src="${h(imgSrc)}" alt="overlay" loading="lazy"
           data-lightbox="${h(imgSrc)}" data-caption="${h(caption)}">
      <div class="bbox-rect" style="${style}"></div>
    </div>`;
}

function renderDetail(e) {
  const bal = e.balance.map(b => Math.round(b * 100));

  return `
    <div class="detail-masks">
      <div class="detail-masks-col">
        <div class="col-label">Raw</div>
        <div class="detail-masks-row">
          <div>
            ${bboxOverlayHtml(e, e.overlay, 'Overlay: ' + e.source_transition)}
            <div class="img-label">Overlay</div>
          </div>
          <div>
            <img src="${h(e.crop_image)}" alt="Raw crop" data-lightbox="${h(e.crop_image)}" data-caption="Raw crop">
            <div class="img-label">Crop</div>
          </div>
          <div>
            <img src="${h(e.mask_a)}" alt="Mask A" data-lightbox="${h(e.mask_a)}" data-caption="Raw Mask A: ${h(e.texture_a)}">
            <div class="img-label" style="color:var(--red-a)">Mask A</div>
          </div>
          <div>
            <img src="${h(e.mask_b)}" alt="Mask B" data-lightbox="${h(e.mask_b)}" data-caption="Raw Mask B: ${h(e.texture_b)}">
            <div class="img-label" style="color:var(--blue-b)">Mask B</div>
          </div>
        </div>
      </div>
      <div class="detail-masks-col">
        <div class="col-label">Refined (${e.scale_factor}x + SDF)</div>
        <div class="detail-masks-row">
          <div>
            ${bboxOverlayHtml(e, e.overlay, 'Overlay: ' + e.source_transition)}
            <div class="img-label">Overlay</div>
          </div>
          <div>
            <img src="${h(e.refined_image)}" alt="Refined crop" data-lightbox="${h(e.refined_image)}" data-caption="Refined crop (${e.scale_factor}x)">
            <div class="img-label">Crop</div>
          </div>
          <div>
            <img src="${h(e.refined_mask_a)}" alt="Refined Mask A" data-lightbox="${h(e.refined_mask_a)}" data-caption="Refined Mask A (SDF): ${h(e.texture_a)}">
            <div class="img-label" style="color:var(--red-a)">Mask A</div>
          </div>
          <div>
            <img src="${h(e.refined_mask_b)}" alt="Refined Mask B" data-lightbox="${h(e.refined_mask_b)}" data-caption="Refined Mask B (SDF): ${h(e.texture_b)}">
            <div class="img-label" style="color:var(--blue-b)">Mask B</div>
          </div>
        </div>
      </div>
    </div>
    <div class="detail-grid mt-1">
      <div>
        <div class="detail-section-title">Crop visualization</div>
        <img src="${h(e.crop_viz)}" alt="Crop viz" loading="lazy"
             style="width:100%; border-radius:8px;"
             data-lightbox="${h(e.crop_viz)}" data-caption="Crop visualization: ${h(e.crop_name)}">
      </div>
    </div>
    <div class="detail-meta">
      <span><strong>A:</strong> ${h(e.texture_a)}</span>
      <span><strong>B:</strong> ${h(e.texture_b)}</span>
      <span><strong>Size:</strong> ${e.crop_width}&times;${e.crop_height} &rarr; ${e.refined_width}&times;${e.refined_height}</span>
      <span><strong>Balance:</strong> ${bal[0]}/${bal[1]}</span>
      ${e.crop_score ? `<span><strong>Score:</strong> ${e.crop_score.toFixed(4)}</span>` : ''}
      <span><strong>Source:</strong> ${h(e.source_image_id)}</span>
    </div>`;
}

// ── Filter & Sort ──
function applyFilters() {
  const query = (document.getElementById('search-input').value || '').toLowerCase().trim();
  const sortVal = document.getElementById('sort-select').value;

  let entries = galleryData.entries;
  if (query) {
    const terms = query.split(/\s+/);
    entries = entries.filter(e => {
      const text = (e.texture_a + ' ' + e.texture_b + ' ' + e.source_image_id).toLowerCase();
      return terms.every(t => text.includes(t));
    });
  }

  entries = [...entries];
  switch (sortVal) {
    case 'source':
      entries.sort((a, b) => a.source_image_id.localeCompare(b.source_image_id) || a.crop_name.localeCompare(b.crop_name));
      break;
    case 'size-desc':
      if (currentMode === 'refined') {
        entries.sort((a, b) => Math.min(b.refined_width, b.refined_height) - Math.min(a.refined_width, a.refined_height));
      } else {
        entries.sort((a, b) => Math.min(b.crop_width, b.crop_height) - Math.min(a.crop_width, a.crop_height));
      }
      break;
    case 'size-asc':
      if (currentMode === 'refined') {
        entries.sort((a, b) => Math.min(a.refined_width, a.refined_height) - Math.min(b.refined_width, b.refined_height));
      } else {
        entries.sort((a, b) => Math.min(a.crop_width, a.crop_height) - Math.min(b.crop_width, b.crop_height));
      }
      break;
    case 'balance':
      entries.sort((a, b) => {
        const ba = Math.min(a.balance[0], a.balance[1]);
        const bb = Math.min(b.balance[0], b.balance[1]);
        return bb - ba;
      });
      break;
    case 'score':
      entries.sort((a, b) => (b.crop_score || 0) - (a.crop_score || 0));
      break;
    case 'alpha':
      entries.sort((a, b) => a.texture_a.localeCompare(b.texture_a));
      break;
  }

  filteredEntries = entries;
  updateStats();
  renderPage();
}

// ── Stats ──
function updateStats() {
  document.getElementById('shown-count').textContent = filteredEntries.length;
  document.getElementById('total-count').textContent = galleryData.entries.length;
  const sizes = filteredEntries.map(e =>
    currentMode === 'refined'
      ? Math.min(e.refined_width, e.refined_height)
      : Math.min(e.crop_width, e.crop_height)
  );
  const avg = sizes.length ? Math.round(sizes.reduce((a, b) => a + b, 0) / sizes.length) : 0;
  document.getElementById('avg-size').textContent = avg;
}

// ── Render ──
function renderPage() {
  const grid = document.getElementById('gallery-grid');
  const totalPages = Math.ceil(filteredEntries.length / PER_PAGE);
  const start = (currentPage - 1) * PER_PAGE;
  const pageEntries = filteredEntries.slice(start, start + PER_PAGE);

  if (groupBySource) {
    grid.innerHTML = renderGrouped(pageEntries);
  } else {
    grid.innerHTML = pageEntries.map(e =>
      currentMode === 'refined' ? renderRefinedCard(e) : renderCropCard(e)
    ).join('');
  }
  renderPagination(totalPages);
}

function h(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderCropCard(e) {
  const shortSource = e.source_image_id.replace('training_ADE_train_', '');
  const bal = e.balance.map(b => Math.round(b * 100));
  return `
    <div class="crop-card" data-crop-name="${h(e.crop_name)}">
      <div class="card-source">
        <img src="${h(e.source_thumb)}" alt="source" loading="lazy"
             data-lightbox="${h(e.source_thumb)}" data-caption="Source: ${h(e.source_image_id)}">
        <div>
          <div class="source-id">ADE ${h(shortSource)}</div>
          <div>${h(e.source_transition.split('_').pop())}</div>
        </div>
      </div>
      <div class="card-overlay-row">
        <div class="card-overlay-item">
          ${bboxOverlayHtml(e, e.overlay, 'Overlay: ' + e.source_transition)}
          <div class="card-overlay-label">Overlay</div>
        </div>
        <div class="card-overlay-item">
          ${bboxOverlayHtml(e, e.trans_image, 'Source: ' + e.source_transition)}
          <div class="card-overlay-label">Source</div>
        </div>
      </div>
      <div class="card-images">
        <img src="${h(e.crop_image)}" alt="crop" loading="lazy"
             data-lightbox="${h(e.crop_image)}" data-caption="Crop: ${h(e.crop_name)}">
        <img src="${h(e.mask_a)}" alt="mask A" loading="lazy"
             data-lightbox="${h(e.mask_a)}" data-caption="Mask A: ${h(e.texture_a)}">
        <img src="${h(e.mask_b)}" alt="mask B" loading="lazy"
             data-lightbox="${h(e.mask_b)}" data-caption="Mask B: ${h(e.texture_b)}">
      </div>
      <div class="card-labels">
        <span>Crop</span>
        <span style="color:var(--red-a)">Mask A</span>
        <span style="color:var(--blue-b)">Mask B</span>
      </div>
      <div class="card-text">
        <div class="desc"><span class="tag tag-a">A</span><span class="txt" title="${h(e.texture_a)}">${h(e.texture_a)}</span></div>
        <div class="desc"><span class="tag tag-b">B</span><span class="txt" title="${h(e.texture_b)}">${h(e.texture_b)}</span></div>
      </div>
      <div class="card-meta">
        <span>${e.crop_width}&times;${e.crop_height}px</span>
        <span>Balance: ${bal[0]}/${bal[1]}</span>
        ${e.crop_score ? `<span>Score: ${e.crop_score.toFixed(4)}</span>` : ''}
      </div>
      <div class="expand-indicator">Click to expand details</div>
    </div>`;
}

function renderRefinedCard(e) {
  const shortSource = e.source_image_id.replace('training_ADE_train_', '');
  const bal = e.balance.map(b => Math.round(b * 100));
  return `
    <div class="crop-card" data-crop-name="${h(e.crop_name)}">
      <div class="card-source">
        <img src="${h(e.source_thumb)}" alt="source" loading="lazy"
             data-lightbox="${h(e.source_thumb)}" data-caption="Source: ${h(e.source_image_id)}">
        <div>
          <div class="source-id">ADE ${h(shortSource)}</div>
          <div>${e.crop_width}&times;${e.crop_height} &rarr; ${e.refined_width}&times;${e.refined_height} (${e.scale_factor}&times;)</div>
        </div>
      </div>
      <div class="card-overlay-row">
        <div class="card-overlay-item">
          ${bboxOverlayHtml(e, e.overlay, 'Overlay: ' + e.source_transition)}
          <div class="card-overlay-label">Overlay</div>
        </div>
        <div class="card-overlay-item">
          ${bboxOverlayHtml(e, e.trans_image, 'Source: ' + e.source_transition)}
          <div class="card-overlay-label">Source</div>
        </div>
      </div>
      <div class="card-comparison" style="position:relative;">
        <div class="col">
          <div class="col-header">Raw</div>
          <div class="img-row">
            <img src="${h(e.crop_image)}" alt="raw crop" loading="lazy"
                 data-lightbox="${h(e.crop_image)}" data-caption="Raw crop">
            <img src="${h(e.mask_a)}" alt="raw mask A" loading="lazy"
                 data-lightbox="${h(e.mask_a)}" data-caption="Raw Mask A: ${h(e.texture_a)}">
            <img src="${h(e.mask_b)}" alt="raw mask B" loading="lazy"
                 data-lightbox="${h(e.mask_b)}" data-caption="Raw Mask B: ${h(e.texture_b)}">
          </div>
          <div class="img-labels">
            <span>Crop</span><span style="color:var(--red-a)">A</span><span style="color:var(--blue-b)">B</span>
          </div>
        </div>
        <div class="col">
          <div class="col-header">Refined</div>
          <div class="img-row">
            <img src="${h(e.refined_image)}" alt="refined crop" loading="lazy"
                 data-lightbox="${h(e.refined_image)}" data-caption="Refined crop (${e.scale_factor}x)">
            <img src="${h(e.refined_mask_a)}" alt="refined mask A" loading="lazy"
                 data-lightbox="${h(e.refined_mask_a)}" data-caption="Refined Mask A (SDF): ${h(e.texture_a)}">
            <img src="${h(e.refined_mask_b)}" alt="refined mask B" loading="lazy"
                 data-lightbox="${h(e.refined_mask_b)}" data-caption="Refined Mask B (SDF): ${h(e.texture_b)}">
          </div>
          <div class="img-labels">
            <span>Crop</span><span style="color:var(--red-a)">A</span><span style="color:var(--blue-b)">B</span>
          </div>
        </div>
        <div class="arrow-sep">&rarr;</div>
      </div>
      <div class="card-text">
        <div class="desc"><span class="tag tag-a">A</span><span class="txt" title="${h(e.texture_a)}">${h(e.texture_a)}</span></div>
        <div class="desc"><span class="tag tag-b">B</span><span class="txt" title="${h(e.texture_b)}">${h(e.texture_b)}</span></div>
      </div>
      <div class="card-meta">
        <span>${e.crop_width}&times;${e.crop_height} &rarr; ${e.refined_width}&times;${e.refined_height}</span>
        <span>Balance: ${bal[0]}/${bal[1]}</span>
      </div>
      <div class="expand-indicator">Click to expand details</div>
    </div>`;
}

function renderGrouped(entries) {
  const groups = new Map();
  for (const e of entries) {
    if (!groups.has(e.source_image_id)) groups.set(e.source_image_id, []);
    groups.get(e.source_image_id).push(e);
  }

  let html = '';
  for (const [srcId, items] of groups) {
    const shortId = srcId.replace('training_ADE_train_', '');
    const thumb = items[0].source_thumb;
    html += `
      <div class="source-group-header">
        <img src="${h(thumb)}" alt="source" loading="lazy"
             data-lightbox="${h(thumb)}" data-caption="${h(srcId)}">
        <div class="info">
          <h3>ADE ${h(shortId)}</h3>
          <p>${items.length} crop${items.length > 1 ? 's' : ''} from this image</p>
        </div>
      </div>`;
    html += items.map(e =>
      currentMode === 'refined' ? renderRefinedCard(e) : renderCropCard(e)
    ).join('');
  }
  return html;
}

// ── Pagination ──
function renderPagination(totalPages) {
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) { pag.innerHTML = ''; return; }

  let html = '';
  html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="goPage(${currentPage - 1})">&laquo; Prev</button>`;
  const pages = getPageNumbers(currentPage, totalPages, 7);
  for (const p of pages) {
    if (p === '...') {
      html += `<span class="page-info">&hellip;</span>`;
    } else {
      html += `<button class="${p === currentPage ? 'active' : ''}" onclick="goPage(${p})">${p}</button>`;
    }
  }
  html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="goPage(${currentPage + 1})">Next &raquo;</button>`;
  html += `<span class="page-info">Page ${currentPage} of ${totalPages}</span>`;
  pag.innerHTML = html;
}

function getPageNumbers(current, total, maxButtons) {
  if (total <= maxButtons) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [1];
  let start = Math.max(2, current - 2);
  let end = Math.min(total - 1, current + 2);
  if (start > 2) pages.push('...');
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < total - 1) pages.push('...');
  pages.push(total);
  return pages;
}

function goPage(page) {
  const totalPages = Math.ceil(filteredEntries.length / PER_PAGE);
  currentPage = Math.max(1, Math.min(page, totalPages));
  renderPage();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Lightbox ──
function openLightbox(src, caption) {
  const lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox-caption').textContent = caption || '';
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  const lb = document.getElementById('lightbox');
  lb.classList.remove('open');
  document.getElementById('lightbox-img').src = '';
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', () => {
  const lb = document.getElementById('lightbox');
  if (lb) lb.addEventListener('click', (e) => { if (e.target === lb) closeLightbox(); });
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

// ── Utilities ──
function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}
