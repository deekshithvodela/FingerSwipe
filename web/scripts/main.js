/**
 * FingerSwipe — Interactive Showcase, Docs Engine & Theme Switcher
 * Author: Deekshith Vodela
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initPaletteSwitcher();
  initMobileNav();
  initDocsSidebar();
  initDocsSearch();
  initGestureSimulator();
  initTabs();
  initCopyButtons();
  initGitHubReleaseData();
  initConfigGenerator();
});

/* =========================================================================
   1. Multi-Palette Switcher (Pine & Mint Default / Velvet Burgundy Accessible Option)
   ========================================================================= */
function initPaletteSwitcher() {
  const paletteToggleBtns = document.querySelectorAll('.palette-toggle-btn');
  const segmentBtns = document.querySelectorAll('.palette-segment-btn');
  const savedPalette = localStorage.getItem('fs_palette');

  // Default is 'pine' unless explicitly set to 'burgundy'
  const initialPalette = savedPalette === 'burgundy' ? 'burgundy' : 'pine';
  setPalette(initialPalette);

  paletteToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const currentPalette = document.documentElement.getAttribute('data-palette') || 'pine';
      const newPalette = currentPalette === 'burgundy' ? 'pine' : 'burgundy';
      setPalette(newPalette);
    });
  });

  segmentBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const chosen = btn.getAttribute('data-palette-choice');
      if (chosen) {
        setPalette(chosen);
      }
    });
  });

  function setPalette(palette) {
    if (palette === 'burgundy') {
      document.documentElement.setAttribute('data-palette', 'burgundy');
    } else {
      document.documentElement.setAttribute('data-palette', 'pine');
    }
    localStorage.setItem('fs_palette', palette);

    // Update navbar buttons accessible labels and indicator
    paletteToggleBtns.forEach(btn => {
      const label = palette === 'burgundy'
        ? 'Switch Color Palette (Currently Velvet Burgundy)'
        : 'Switch Color Palette (Currently Pine & Mint)';
      btn.setAttribute('aria-label', label);
      btn.setAttribute('title', label);
    });

    // Update segmented radio buttons
    segmentBtns.forEach(btn => {
      const choice = btn.getAttribute('data-palette-choice');
      const isActive = choice === palette;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-checked', isActive ? 'true' : 'false');
    });
  }
}

/* =========================================================================
   2. Dual-Theme Switcher (Light Default / Dark Option)
   ========================================================================= */
function initTheme() {
  const themeToggleBtns = document.querySelectorAll('.theme-toggle-btn');
  const savedTheme = localStorage.getItem('theme');

  // Default is light unless user explicitly previously selected dark
  const initialTheme = savedTheme === 'dark' ? 'dark' : 'light';
  setTheme(initialTheme);

  themeToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const newTheme = isDark ? 'light' : 'dark';
      setTheme(newTheme);
    });
  });

  function setTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', theme);
  }
}

/* =========================================================================
   2. Mobile Main Navigation Drawer
   ========================================================================= */
function initMobileNav() {
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  const navLinks = document.getElementById('nav-links');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const isOpen = navLinks.classList.contains('open');
      toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close when link is clicked
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
      });
    });
  }
}

/* =========================================================================
   3. Docs Portal Sidebar Drawer & Scroll-Spy
   ========================================================================= */
function initDocsSidebar() {
  const mobileDocsBtn = document.getElementById('mobile-docs-btn');
  const docsSidebar = document.getElementById('docs-sidebar');
  const docsOverlay = document.getElementById('docs-overlay');

  if (mobileDocsBtn && docsSidebar) {
    mobileDocsBtn.addEventListener('click', () => {
      docsSidebar.classList.toggle('open');
      if (docsOverlay) docsOverlay.classList.toggle('open');
    });

    if (docsOverlay) {
      docsOverlay.addEventListener('click', () => {
        docsSidebar.classList.remove('open');
        docsOverlay.classList.remove('open');
      });
    }

    docsSidebar.querySelectorAll('.docs-nav-link').forEach(link => {
      link.addEventListener('click', () => {
        docsSidebar.classList.remove('open');
        if (docsOverlay) docsOverlay.classList.remove('open');
      });
    });
  }

  // Scroll Spy for Docs Sections
  const docsSections = document.querySelectorAll('.docs-section');
  const navLinks = document.querySelectorAll('.docs-nav-link');

  if (docsSections.length > 0 && navLinks.length > 0) {
    window.addEventListener('scroll', () => {
      let currentSectionId = '';
      const scrollPos = window.scrollY + 140;

      docsSections.forEach(section => {
        if (section.offsetTop <= scrollPos) {
          currentSectionId = section.getAttribute('id');
        }
      });

      if (currentSectionId) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${currentSectionId}`) {
            link.classList.add('active');
          }
        });
      }
    }, { passive: true });
  }
}

/* =========================================================================
   4. Docs Client-Side Search Filter
   ========================================================================= */
function initDocsSearch() {
  const searchInput = document.getElementById('docs-search-input');
  if (!searchInput) return;

  const navLinks = document.querySelectorAll('.docs-nav-link');
  const navGroups = document.querySelectorAll('.docs-nav-group');

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();

    navLinks.forEach(link => {
      const text = link.textContent.toLowerCase();
      if (text.includes(query) || !query) {
        link.style.display = 'flex';
      } else {
        link.style.display = 'none';
      }
    });

    // Hide empty groups
    navGroups.forEach(group => {
      const visibleLinks = group.querySelectorAll('.docs-nav-link[style*="display: flex"], .docs-nav-link:not([style*="display: none"])');
      if (query && visibleLinks.length === 0) {
        group.style.display = 'none';
      } else {
        group.style.display = 'block';
      }
    });
  });
}

/* =========================================================================
   5. Interactive 3-Finger Gesture Simulator Engine
   ========================================================================= */
function initGestureSimulator() {
  const surface = document.getElementById('trackpad-surface');
  const pointer = document.getElementById('gesture-pointer');
  const prompt = document.getElementById('trackpad-prompt');
  const axisIndicator = document.getElementById('axis-indicator');

  const osdIcon = document.getElementById('osd-icon');
  const osdLabel = document.getElementById('osd-label');
  const osdVal = document.getElementById('osd-val');
  const osdFill = document.getElementById('osd-progress-fill');

  const volVal = document.getElementById('meter-vol-val');
  const volFill = document.getElementById('meter-vol-fill');
  const brightVal = document.getElementById('meter-bright-val');
  const brightFill = document.getElementById('meter-bright-fill');

  if (!surface) return;

  let isTracking = false;
  let startX = 0;
  let startY = 0;
  let lastX = 0;
  let lastY = 0;
  let lockedAxis = null;
  const lockThreshold = 14;

  let currentVolume = 0.65;
  let currentBrightness = 0.80;

  function updateMeters() {
    if (volVal && volFill) {
      volVal.textContent = `${Math.round(currentVolume * 100)}%`;
      volFill.style.width = `${currentVolume * 100}%`;
    }
    if (brightVal && brightFill) {
      brightVal.textContent = `${Math.round(currentBrightness * 100)}%`;
      brightFill.style.width = `${currentBrightness * 100}%`;
    }
  }

  function triggerOSD(type, value) {
    if (!osdLabel || !osdVal || !osdFill || !osdIcon) return;
    if (type === 'volume') {
      osdLabel.textContent = 'Audio Volume (PipeWire)';
      osdVal.textContent = `${Math.round(value * 100)}%`;
      osdFill.style.width = `${value * 100}%`;
      osdFill.style.background = 'var(--accent-primary)';
      osdIcon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        </svg>
      `;
    } else {
      osdLabel.textContent = 'Display Brightness';
      osdVal.textContent = `${Math.round(value * 100)}%`;
      osdFill.style.width = `${value * 100}%`;
      osdFill.style.background = 'var(--accent-amber)';
      osdIcon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      `;
    }
  }

  function handleStart(clientX, clientY) {
    isTracking = true;
    const rect = surface.getBoundingClientRect();
    startX = clientX - rect.left;
    startY = clientY - rect.top;
    lastX = startX;
    lastY = startY;
    lockedAxis = null;

    if (pointer) {
      pointer.style.left = `${startX}px`;
      pointer.style.top = `${startY}px`;
      pointer.classList.add('active');
    }
    if (prompt) prompt.style.opacity = '0';
    if (axisIndicator) {
      axisIndicator.textContent = 'AXIS: DETECTING...';
      axisIndicator.style.color = 'var(--text-muted)';
    }
  }

  function handleMove(clientX, clientY) {
    if (!isTracking) return;

    const rect = surface.getBoundingClientRect();
    const currentX = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const currentY = Math.max(0, Math.min(rect.height, clientY - rect.top));

    if (pointer) {
      pointer.style.left = `${currentX}px`;
      pointer.style.top = `${currentY}px`;
    }

    const deltaX = currentX - lastX;
    const deltaY = currentY - lastY;
    const totalDeltaX = currentX - startX;
    const totalDeltaY = currentY - startY;

    if (!lockedAxis) {
      if (Math.abs(totalDeltaY) > lockThreshold && Math.abs(totalDeltaY) > Math.abs(totalDeltaX) * 1.2) {
        lockedAxis = 'vertical';
        if (axisIndicator) {
          axisIndicator.textContent = 'LOCKED: VERTICAL [VOLUME]';
          axisIndicator.style.color = 'var(--accent-primary)';
        }
      } else if (Math.abs(totalDeltaX) > lockThreshold && Math.abs(totalDeltaX) > Math.abs(totalDeltaY) * 1.2) {
        lockedAxis = 'horizontal';
        if (axisIndicator) {
          axisIndicator.textContent = 'LOCKED: HORIZONTAL [BRIGHTNESS]';
          axisIndicator.style.color = 'var(--accent-amber)';
        }
      }
    }

    if (lockedAxis === 'vertical') {
      const step = -deltaY * 0.004;
      currentVolume = Math.max(0.0, Math.min(1.0, currentVolume + step));
      triggerOSD('volume', currentVolume);
      updateMeters();
    } else if (lockedAxis === 'horizontal') {
      const step = deltaX * 0.004;
      currentBrightness = Math.max(0.01, Math.min(1.0, currentBrightness + step));
      triggerOSD('brightness', currentBrightness);
      updateMeters();
    }

    lastX = currentX;
    lastY = currentY;
  }

  function handleEnd() {
    if (!isTracking) return;
    isTracking = false;
    if (pointer) pointer.classList.remove('active');
    if (prompt) prompt.style.opacity = '1';
    if (axisIndicator) {
      axisIndicator.textContent = 'AXIS: IDLE';
      axisIndicator.style.color = 'var(--text-faint)';
    }
  }

  surface.addEventListener('pointerdown', (e) => {
    surface.setPointerCapture(e.pointerId);
    handleStart(e.clientX, e.clientY);
  });

  surface.addEventListener('pointermove', (e) => {
    handleMove(e.clientX, e.clientY);
  });

  surface.addEventListener('pointerup', handleEnd);
  surface.addEventListener('pointercancel', handleEnd);

  // Accessibility: Keyboard Arrow Controls
  surface.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      currentVolume = Math.min(1.0, currentVolume + 0.05);
      if (axisIndicator) {
        axisIndicator.textContent = 'KEYBOARD: VERTICAL [VOLUME +]';
        axisIndicator.style.color = 'var(--accent-primary)';
      }
      triggerOSD('volume', currentVolume);
      updateMeters();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      currentVolume = Math.max(0.0, currentVolume - 0.05);
      if (axisIndicator) {
        axisIndicator.textContent = 'KEYBOARD: VERTICAL [VOLUME -]';
        axisIndicator.style.color = 'var(--accent-primary)';
      }
      triggerOSD('volume', currentVolume);
      updateMeters();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      currentBrightness = Math.min(1.0, currentBrightness + 0.05);
      if (axisIndicator) {
        axisIndicator.textContent = 'KEYBOARD: HORIZONTAL [BRIGHTNESS +]';
        axisIndicator.style.color = 'var(--accent-amber)';
      }
      triggerOSD('brightness', currentBrightness);
      updateMeters();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      currentBrightness = Math.max(0.01, currentBrightness - 0.05);
      if (axisIndicator) {
        axisIndicator.textContent = 'KEYBOARD: HORIZONTAL [BRIGHTNESS -]';
        axisIndicator.style.color = 'var(--accent-amber)';
      }
      triggerOSD('brightness', currentBrightness);
      updateMeters();
    }
  });

  updateMeters();
}

/* =========================================================================
   6. Installation & Update Tab Switcher
   ========================================================================= */
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

/* =========================================================================
   7. Copy-to-Clipboard Functionality
   ========================================================================= */
function initCopyButtons() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetId = btn.getAttribute('data-copy-target');
      let textToCopy = '';

      if (targetId) {
        const el = document.getElementById(targetId);
        textToCopy = el ? el.textContent.trim() : '';
      } else {
        const pre = btn.parentElement.querySelector('pre');
        textToCopy = pre ? pre.textContent.trim() : '';
      }

      if (textToCopy) {
        try {
          await navigator.clipboard.writeText(textToCopy);
          const originalHTML = btn.innerHTML;
          btn.classList.add('copied');
          btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Copied!
          `;
          setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = originalHTML;
          }, 2000);
        } catch (err) {
          console.error('Failed to copy', err);
        }
      }
    });
  });
}

/* =========================================================================
   8. Dynamic GitHub Releases API Fetcher
   ========================================================================= */
async function initGitHubReleaseData() {
  const repo = 'deekshithvodela/FingerSwipe';
  const tagEl = document.getElementById('release-tag');
  const starCountEl = document.getElementById('star-count');
  const debDownloadBtn = document.getElementById('btn-download-deb');
  const tarDownloadBtn = document.getElementById('btn-download-tar');
  const debSizeEl = document.getElementById('deb-file-size');
  const tarSizeEl = document.getElementById('tar-file-size');

  const defaultVersion = 'v1.1.0';

  try {
    const repoRes = await fetch(`https://api.github.com/repos/${repo}`);
    if (repoRes.ok) {
      const repoData = await repoRes.json();
      if (starCountEl && repoData.stargazers_count !== undefined) {
        starCountEl.textContent = `★ ${repoData.stargazers_count}`;
      }
    }

    const releaseRes = await fetch(`https://api.github.com/repos/${repo}/releases/latest`);
    if (releaseRes.ok) {
      const releaseData = await releaseRes.json();
      const tagName = releaseData.tag_name || defaultVersion;
      if (tagEl) tagEl.textContent = tagName;

      if (releaseData.assets && releaseData.assets.length > 0) {
        const debAsset = releaseData.assets.find(a => a.name.endsWith('.deb'));
        const tarAsset = releaseData.assets.find(a => a.name.endsWith('.tar.gz'));

        if (debAsset && debDownloadBtn) {
          debDownloadBtn.href = debAsset.browser_download_url;
          if (debSizeEl) debSizeEl.textContent = `${(debAsset.size / 1024).toFixed(1)} KB`;
        }

        if (tarAsset && tarDownloadBtn) {
          tarDownloadBtn.href = tarAsset.browser_download_url;
          if (tarSizeEl) tarSizeEl.textContent = `${(tarAsset.size / 1024).toFixed(1)} KB`;
        }
      }
    }
  } catch (e) {
    // Graceful offline fallback
  }
}

/* =========================================================================
   9. Interactive Configuration YAML Generator
   ========================================================================= */
function initConfigGenerator() {
  const curveInput = document.getElementById('cfg-curve');
  const deadZoneInput = document.getElementById('cfg-deadzone');
  const deadZoneVal = document.getElementById('val-deadzone');
  const smoothingInput = document.getElementById('cfg-smoothing');
  const smoothingVal = document.getElementById('val-smoothing');
  const sensitivityInput = document.getElementById('cfg-sensitivity');
  const sensitivityVal = document.getElementById('val-sensitivity');
  const lockThreshInput = document.getElementById('cfg-axis-lock');
  const lockThreshVal = document.getElementById('val-axis-lock');
  const volStepInput = document.getElementById('cfg-vol-step');
  const volStepVal = document.getElementById('val-vol-step');
  const brightStepInput = document.getElementById('cfg-bright-step');
  const brightStepVal = document.getElementById('val-bright-step');
  const outputCode = document.getElementById('cfg-output-yaml');

  if (!outputCode) return;

  function updateYAML() {
    const curve = curveInput ? curveInput.value : 'linear';
    const deadZone = deadZoneInput ? parseFloat(deadZoneInput.value).toFixed(2) : '0.00';
    const smoothing = smoothingInput ? parseFloat(smoothingInput.value).toFixed(2) : '1.00';
    const sensitivity = sensitivityInput ? parseFloat(sensitivityInput.value).toFixed(2) : '1.00';
    const lockThresh = lockThreshInput ? parseFloat(lockThreshInput.value).toFixed(1) : '2.0';
    const volStep = volStepInput ? (parseFloat(volStepInput.value) / 100).toFixed(2) : '0.01';
    const brightStep = brightStepInput ? (parseFloat(brightStepInput.value) / 100).toFixed(2) : '0.01';

    if (deadZoneVal) deadZoneVal.textContent = deadZone;
    if (smoothingVal) smoothingVal.textContent = smoothing;
    if (sensitivityVal) sensitivityVal.textContent = sensitivity;
    if (lockThreshVal) lockThreshVal.textContent = lockThresh;
    if (volStepVal) volStepVal.textContent = `${Math.round(parseFloat(volStep) * 100)}%`;
    if (brightStepVal) brightStepVal.textContent = `${Math.round(parseFloat(brightStep) * 100)}%`;

    outputCode.textContent = `engine:
  dead_zone: ${deadZone}
  smoothing: ${smoothing}
  sensitivity: ${sensitivity}
  curve: ${curve}
  axis_lock_threshold: ${lockThresh}

volume:
  enabled: true
  axis: vertical
  minimum: 0.0
  maximum: 1.0
  step: ${volStep}
  threshold: 4.0

brightness:
  enabled: true
  axis: horizontal
  minimum: 0.01
  maximum: 1.0
  step: ${brightStep}
  threshold: 4.0

logging:
  level: INFO
  json: false`;
  }

  [curveInput, deadZoneInput, smoothingInput, sensitivityInput, lockThreshInput, volStepInput, brightStepInput].forEach(input => {
    if (input) input.addEventListener('input', updateYAML);
  });

  updateYAML();
}
