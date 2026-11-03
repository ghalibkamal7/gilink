(() => {
  const form = document.getElementById('urlForm');
  const menuToggle = document.getElementById('menuToggle');
  const primaryNav = document.getElementById('primaryNav');
  let recentLinks = [];

  if (menuToggle && primaryNav) {
    menuToggle.addEventListener('click', () => {
      const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
      menuToggle.setAttribute('aria-expanded', String(!expanded));
      menuToggle.setAttribute('aria-label', expanded ? 'Open menu' : 'Close menu');
      primaryNav.classList.toggle('is-open', !expanded);
    });
    primaryNav.addEventListener('click', (event) => {
      if (event.target instanceof Element && event.target.closest('a, button')) {
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.setAttribute('aria-label', 'Open menu');
        primaryNav.classList.remove('is-open');
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.setAttribute('aria-label', 'Open menu');
        primaryNav.classList.remove('is-open');
        menuToggle.focus();
      }
    });
  }

  if (form) {
    const urlInput = document.getElementById('urlInput');
    const urlControl = document.getElementById('urlControl');
    const pasteButton = document.getElementById('pasteBtn');
    const fetchButton = document.getElementById('fetchBtn');
    const formError = document.getElementById('formError');
    const mediaCard = document.getElementById('mediaCard');
    const mediaTitle = document.getElementById('mediaTitle');
    const mediaPlatform = document.getElementById('mediaPlatform');
    const mediaByline = document.getElementById('mediaByline');
    const mediaThumb = document.getElementById('mediaThumb');
    const thumbnailFallback = document.getElementById('thumbnailFallback');
    const formatPresets = document.getElementById('formatPresets');
    const formatCount = document.getElementById('formatCount');
    const errorCard = document.getElementById('errorCard');
    const errorMessage = document.getElementById('errorMessage');
    const downloadStatus = document.getElementById('downloadStatus');

    const setFormError = (message) => {
      formError.textContent = message;
      formError.hidden = !message;
      urlControl.classList.toggle('invalid', Boolean(message));
      urlInput.setAttribute('aria-invalid', String(Boolean(message)));
    };

    const setLoading = (loading) => {
      fetchButton.disabled = loading;
      fetchButton.classList.toggle('is-loading', loading);
      fetchButton.setAttribute('aria-busy', String(loading));
    };

    const showError = (message) => {
      errorMessage.textContent = message;
      errorCard.hidden = false;
    };

    const renderHistory = () => {
      const historyModal = document.getElementById('historyModal');
      const historyList = document.getElementById('historyList');
      if (!historyModal || !historyList) return;
      historyList.replaceChildren();
      if (!recentLinks.length) {
        const empty = document.createElement('p');
        empty.className = 'history-empty';
        empty.textContent = 'Links you check will appear here until you close or refresh this page.';
        historyList.append(empty);
        return;
      }
      recentLinks.forEach((item) => {
        const button = document.createElement('button');
        button.className = 'history-item';
        button.type = 'button';
        const title = document.createElement('strong');
        title.textContent = item.title;
        const detail = document.createElement('span');
        detail.textContent = `${item.platform} · ${item.url}`;
        button.append(title, detail);
        button.addEventListener('click', () => {
          urlInput.value = item.url;
          historyModal.close();
          form.requestSubmit();
        });
        historyList.append(button);
      });
    };

    const rememberLink = (item) => {
      recentLinks = [item, ...recentLinks.filter((entry) => entry.url !== item.url)].slice(0, 10);
      renderHistory();
    };

    const buildFormatButton = (preset, url) => {
      const button = document.createElement('button');
      button.className = 'format-button';
      button.type = 'button';
      const main = document.createElement('span');
      main.className = 'format-main';
      const icon = document.createElement('span');
      icon.className = 'format-icon';
      const isAudio = preset.is_audio === true || preset.type === 'audio' || preset.ext === 'mp3';
      icon.textContent = isAudio ? 'AUDIO' : 'VIDEO';
      const name = document.createElement('span');
      name.className = 'format-name';
      name.textContent = preset.name || preset.quality || (isAudio ? 'Audio' : 'Video');
      main.append(icon, name);

      const detail = document.createElement('span');
      detail.className = 'format-info';
      const info = [preset.ext?.toUpperCase(), preset.size].filter((value) => value && value !== 'Unknown size');
      detail.textContent = info.join(' · ');
      const arrow = document.createElement('span');
      arrow.className = 'format-arrow';
      arrow.setAttribute('aria-hidden', 'true');
      arrow.textContent = '↓';
      button.append(main, detail, arrow);
      button.setAttribute('aria-label', `Download ${name.textContent}${info.length ? `, ${info.join(', ')}` : ''}`);
      button.addEventListener('click', () => downloadMedia(url, preset.id, isAudio, button));
      return button;
    };

    const setDownloadStatus = (message, failed = false) => {
      downloadStatus.textContent = message;
      downloadStatus.classList.toggle('is-error', failed);
      downloadStatus.hidden = !message;
    };

    const parseFilename = (disposition, fallback) => {
      const encoded = /filename\*=UTF-8''([^;]+)/i.exec(disposition || '');
      if (encoded) {
        try {
          return decodeURIComponent(encoded[1]);
        } catch {
          return fallback;
        }
      }
      const plain = /filename="?([^";]+)"?/i.exec(disposition || '');
      return plain?.[1] || fallback;
    };

    const downloadMedia = async (url, formatSpec, isAudio, button) => {
      button.disabled = true;
      setDownloadStatus('Preparing your download…');
      try {
        const query = new URLSearchParams({
          url,
          format_spec: formatSpec,
          is_audio: String(isAudio),
        });
        const response = await fetch(`/api/download?${query}`);
        if (!response.ok) {
          const error = await response.json().catch(() => null);
          throw new Error(error?.detail || 'This file could not be downloaded. Try another format or link.');
        }

        const filenameFallback = isAudio ? 'audio-download.bin' : 'video-download.bin';
        const filename = parseFilename(response.headers.get('content-disposition'), filenameFallback);
        const chunks = [];
        const total = Number(response.headers.get('content-length')) || 0;
        let received = 0;
        if (!response.body) throw new Error('The download stream is unavailable. Please try again.');
        const reader = response.body.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          received += value.byteLength;
          const downloaded = (received / (1024 * 1024)).toFixed(1);
          const totalText = total ? ` of ${(total / (1024 * 1024)).toFixed(1)} MB` : '';
          setDownloadStatus(`Downloading… ${downloaded} MB${totalText}`);
        }

        const mediaType = response.headers.get('content-type')?.split(';', 1)[0] || 'application/octet-stream';
        const blobUrl = URL.createObjectURL(new Blob(chunks, { type: mediaType }));
        const anchor = document.createElement('a');
        anchor.href = blobUrl;
        anchor.download = filename;
        anchor.hidden = true;
        document.body.append(anchor);
        anchor.click();
        anchor.remove();
        window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
        setDownloadStatus('Download ready. Check your browser’s downloads.');
      } catch (error) {
        setDownloadStatus(error instanceof Error ? error.message : 'The download failed. Please try again.', true);
      } finally {
        button.disabled = false;
      }
    };

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setFormError('');
      errorCard.hidden = true;
      mediaCard.hidden = true;
      setDownloadStatus('');
      const url = urlInput.value.trim();
      try {
        const parsed = new URL(url);
        if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) {
          throw new Error('Enter a complete link beginning with http:// or https://.');
        }
      } catch {
        setFormError('Enter a valid link beginning with http:// or https://.');
        urlInput.focus();
        return;
      }

      setLoading(true);
      try {
        const response = await fetch('/api/info', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
          throw new Error(result.error || 'This link could not be checked. Try another public link.');
        }

        const info = result.data;
        mediaTitle.textContent = info.title || 'Untitled media';
        mediaPlatform.textContent = info.platform || 'Media';
        mediaByline.textContent = [info.uploader, info.duration].filter(Boolean).join(' · ');
        mediaThumb.hidden = true;
        thumbnailFallback.hidden = false;
        mediaThumb.removeAttribute('src');
        if (info.thumbnail) {
          try {
            const thumbnailUrl = new URL(info.thumbnail);
            if (['http:', 'https:'].includes(thumbnailUrl.protocol)) {
              mediaThumb.onload = () => {
                mediaThumb.hidden = false;
                thumbnailFallback.hidden = true;
              };
              mediaThumb.onerror = () => {
                mediaThumb.hidden = true;
                thumbnailFallback.hidden = false;
              };
              mediaThumb.src = thumbnailUrl.href;
            }
          } catch {
            // Invalid thumbnail URLs are omitted; media metadata remains available.
          }
        }
        const presets = Array.isArray(info.presets) ? info.presets : [];
        formatPresets.replaceChildren(...presets.map((preset) => buildFormatButton(preset, url)));
        formatCount.textContent = presets.length ? `${presets.length} ${presets.length === 1 ? 'option' : 'options'}` : '';
        if (!presets.length) {
          const empty = document.createElement('p');
          empty.className = 'history-empty';
          empty.textContent = 'No downloadable formats were found for this link.';
          formatPresets.append(empty);
        }
        rememberLink({ url, title: info.title || 'Untitled media', platform: info.platform || 'Media' });
        mediaCard.hidden = false;
        mediaCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch (error) {
        showError(error instanceof Error ? error.message : 'This link could not be checked. Try another public link.');
      } finally {
        setLoading(false);
      }
    });

    urlInput.addEventListener('input', () => {
      if (!formError.hidden) setFormError('');
    });

    pasteButton.addEventListener('click', async () => {
      if (!navigator.clipboard?.readText) {
        setFormError('Clipboard access is unavailable in this browser. Paste the link into the field.');
        urlInput.focus();
        return;
      }
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          urlInput.value = text.trim();
          setFormError('');
          urlInput.focus();
        }
      } catch {
        setFormError('Clipboard access was denied. Paste the link into the field.');
        urlInput.focus();
      }
    });

    document.getElementById('historyBtn')?.addEventListener('click', () => {
      const modal = document.getElementById('historyModal');
      if (!modal) return;
      renderHistory();
      modal.showModal();
      document.getElementById('closeHistoryBtn')?.focus();
    });
    document.getElementById('closeHistoryBtn')?.addEventListener('click', () => {
      document.getElementById('historyModal').close();
    });
    document.querySelector('[data-history-close]')?.addEventListener('click', () => {
      document.getElementById('historyModal').close();
    });
    document.getElementById('clearHistoryBtn')?.addEventListener('click', () => {
      recentLinks = [];
      renderHistory();
    });
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch((error) => {
        console.warn('GI LINK offline support could not be enabled.', error);
      });
    });
  }
})();
