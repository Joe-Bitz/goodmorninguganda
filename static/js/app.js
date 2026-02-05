(function () {
  const canvas = document.getElementById("chartCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let series = JSON.parse(canvas.dataset.series || "[]");

  function yScale(v, min, max, h, pad) {
    return pad + ((max - v) / (max - min || 1)) * (h - pad * 2);
  }

  function draw() {
    const width = canvas.width;
    const height = canvas.height;
    const pad = 26;
    ctx.clearRect(0, 0, width, height);

    const min = Math.min(...series);
    const max = Math.max(...series);
    const step = (width - pad * 2) / Math.max(series.length - 1, 1);

    ctx.strokeStyle = "rgba(245,244,235,0.14)";
    ctx.lineWidth = 1;
    for (let i = 0; i < 6; i++) {
      const y = pad + ((height - pad * 2) / 5) * i;
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(width - pad, y);
      ctx.stroke();
    }

    ctx.strokeStyle = "#6ee0cf";
    ctx.lineWidth = 2;
    ctx.beginPath();
    series.forEach((point, i) => {
      const x = pad + i * step;
      const y = yScale(point, min, max, height, pad);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function toast(msg) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => el.classList.remove("show"), 2800);
  }

  async function recalc() {
    const res = await fetch("/api/recalc");
    const data = await res.json();

    document.getElementById("netWorth").textContent = data.metrics.net_worth;
    document.getElementById("shortInterest").textContent = data.metrics.short_interest;
    document.getElementById("pnl").textContent = data.metrics.pnl;

    series = data.series;
    draw();
    toast("Recomputed fake returns.");
  }

  async function news() {
    const res = await fetch("/api/news");
    const data = await res.json();

    const list = document.getElementById("headlineList");
    const article = document.createElement("article");
    article.className = "headline";
    article.innerHTML = `<header><span>${data.stamp}</span><span class="mono">${data.tag}</span></header><p>${data.text}</p>`;
    list.prepend(article);

    while (list.children.length > 5) {
      list.removeChild(list.lastElementChild);
    }

    toast("Breaking: " + data.tag);
  }

  document.getElementById("recalcBtn").addEventListener("click", recalc);
  document.getElementById("newsBtn").addEventListener("click", news);

  draw();
})();