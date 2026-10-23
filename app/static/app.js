document.addEventListener('DOMContentLoaded', () => {
  const urlForm = document.getElementById('urlForm');
  const urlInput = document.getElementById('urlInput');
  const fetchBtn = document.getElementById('fetchBtn');
  const fetchIcon = document.getElementById('fetchIcon');
  const fetchText = document.getElementById('fetchText');
  const fetchSpinner = document.getElementById('fetchSpinner');
  const mediaCard = document.getElementById('mediaCard');
  const errorCard = document.getElementById('errorCard');
  const errorMessage = document.getElementById('errorMessage');
  const mediaThumb = document.getElementById('mediaThumb');
  const mediaTitle = document.getElementById('mediaTitle');
  const mediaAuthor = document.getElementById('authorText');
  const mediaDuration = document.getElementById('mediaDuration');
  const mediaPlatform = document.getElementById('mediaPlatform');
  const formatPresets = document.getElementById('formatPresets');
  const downloadStatus = document.getElementById('downloadStatus');
  const statusText = document.getElementById('statusText');
  const statusBar = document.getElementById('statusBar');
  const historyBtn = document.getElementById('historyBtn');
  const historyModal = document.getElementById('historyModal');
  const closeHistoryBtn = document.getElementById('closeHistoryBtn');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const historyList = document.getElementById('historyList');
  const pasteBtn = document.getElementById('pasteBtn');
  const clearBtn = document.getElementById('clearBtn');

  const updateHistory = (item) => {
    const div = document.createElement('div');
    div.className = 'p-3 rounded-lg bg-slate-800/50 border border-slate-700';
    div.innerHTML = `<a href="#" class="text-indigo-300 hover:underline" data-url="${item.url}">${item.title}</a> - ${item.platform}`;
    historyList.prepend(div);
    // click to refill
    div.querySelector('a').addEventListener('click', (e) => {
      e.preventDefault();
      urlInput.value = item.url;
      fetchMedia();
    });
  };

  const fetchMedia = async () => {
    const url = urlInput.value.trim();
    if (!url) return;
    // UI state
    fetchSpinner.classList.remove('hidden');
    fetchIcon.classList.add('hidden');
    fetchBtn.disabled = true;
    errorCard.classList.add('hidden');
    mediaCard.classList.add('hidden');
    try {
      const resp = await fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await resp.json();
      if (!data.success) throw new Error(data.error || 'Unknown error');
      const info = data.data;
      // populate UI
      mediaThumb.src = info.thumbnail || '';
      mediaTitle.textContent = info.title;
      mediaAuthor.textContent = info.uploader;
      mediaDuration.textContent = info.duration;
      mediaPlatform.textContent = info.platform;
      // presets
      formatPresets.innerHTML = '';
      info.presets.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'w-full px-3 py-2 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition';
        btn.textContent = p.name;
        btn.dataset.format = p.id;
        btn.dataset.audio = p.ext === "mp3" ? 'true' : 'false';
        btn.addEventListener('click', () => startDownload(url, p.id, p.ext === "mp3"));
        formatPresets.appendChild(btn);
      });
      mediaCard.classList.remove('hidden');
      // add to history
      updateHistory({ url, title: info.title, platform: info.platform });
    } catch (e) {
      errorMessage.textContent = e.message;
      errorCard.classList.remove('hidden');
    } finally {
      fetchSpinner.classList.add('hidden');
      fetchIcon.classList.remove('hidden');
      fetchBtn.disabled = false;
    }
  };

  const startDownload = (url, formatSpec, isAudio) => {
    downloadStatus.classList.remove('hidden');
    statusText.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin text-indigo-400"></i> Preparing download...`;
    // trigger download by navigating to the endpoint (browser handles file response)
    const dlUrl = `/api/download?url=${encodeURIComponent(url)}&format_spec=${encodeURIComponent(formatSpec)}&is_audio=${isAudio}`;
    // use hidden iframe to start download without leaving page
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = dlUrl;
    document.body.appendChild(iframe);
    setTimeout(() => downloadStatus.classList.add('hidden'), 3000);
  };

  urlForm.addEventListener('submit', (e) => { e.preventDefault(); fetchMedia(); });

  // Clipboard paste handling
  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) urlInput.value = text;
    } catch (_) {}
  });

  urlInput.addEventListener('input', () => {
    clearBtn.style.display = urlInput.value ? 'block' : 'none';
  });
  clearBtn.addEventListener('click', () => { urlInput.value = ''; clearBtn.style.display = 'none'; });

  // History modal
  historyBtn.addEventListener('click', () => historyModal.classList.remove('hidden'));
  closeHistoryBtn.addEventListener('click', () => historyModal.classList.add('hidden'));
  clearHistoryBtn.addEventListener('click', () => { historyList.innerHTML = ''; });
});
