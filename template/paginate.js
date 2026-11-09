(async function () {
  // 원본 블록은 hidden 상태라 글꼴 요청이 늦게 시작된다. 측정 전에 쓰는 굵기를 모두 먼저 불러온다.
  const FAM = document.body.classList.contains('lang-ja') ? 'PretendardJPM' : 'PretendardM';
  const SAMPLE = FAM === 'PretendardJPM' ? 'あ漢1A' : '가1A';
  await Promise.all([400, 500, 700, 800].map(w => document.fonts.load(`${w} 16px ${FAM}`, SAMPLE)));
  await document.fonts.ready;
  if (![400, 500, 700, 800].every(w => document.fonts.check(`${w} 16px ${FAM}`, SAMPLE))) throw new Error('Pretendard 로드 실패');
  await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
  const src = document.getElementById('src');
  const book = document.getElementById('book');
  let pno = 0;
  const pageMap = {};

  // [표 제목 열 너비, 고정프롬프트 표 절] 첫 열 글이 단어 중간에서 잘리거나 3줄 이상이거나 마지막 줄에 낱말 하나(3글자 이하)만 떨어지면
  // 첫 열을 4px씩 좁히거나(96px까지) 넓혀(표 너비의 30%까지) 본다. 표 높이가 늘거나 어느 칸이든 3줄이 되는 너비는 쓰지 않는다 (2026-11-04).
  {
    const probe = document.createElement('div');
    probe.className = 'page body';
    probe.style.cssText = 'position:absolute;left:-10000px;top:0';
    const pa = document.createElement('div'); pa.className = 'area'; pa.style.top = '0'; probe.appendChild(pa);
    document.body.appendChild(probe);
    const firstCells = t => [...t.rows].map(r => r.cells[0]).filter(Boolean);
    const lineCount = c => {
      const r = document.createRange(); r.selectNodeContents(c);
      const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.bottom)));
      return tops.size;
    };
    // 단어(공백으로 나눈 덩어리)가 칸 안쪽 너비보다 길면 잘린 것으로 본다
    const broken = c => {
      const cs = getComputedStyle(c);
      const inner = c.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const tw = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
      const texts = []; while (tw.nextNode()) texts.push(tw.currentNode);
      let n = 0;
      for (const node of texts) {
        for (const w of node.textContent.split(/\s+/)) {
          if (!w) continue;
          const sp = document.createElement('span'); sp.style.whiteSpace = 'nowrap'; sp.textContent = w;
          node.parentElement.appendChild(sp);
          if (sp.getBoundingClientRect().width > inner + 0.5) n++;
          sp.remove();
        }
      }
      return n;
    };
    // 너비를 정하고, 모든 단어가 들어가면 자동 하이픈을 끈다(들어가는 단어를 억지로 쪼개지 않게)
    // 머리글 칸에는 build.py가 적은 % 너비가 있어, 첫 열만 px로 바꾸면 나머지 % 합이 100%라 무시된다. 첫 열을 바꿀 때 나머지 머리글 칸은 남은 너비를 원래 비율로 나눠 갖는다 (2026-11-04)
    let hdrs = [], hdrPct = [];
    const setW = (cells, w) => {
      cells.forEach(c => { c.style.width = w === null ? '' : w + 'px'; c.style.hyphens = c.style.webkitHyphens = ''; });
      const sum = hdrPct.slice(1).reduce((a, b) => a + b, 0);
      if (sum > 0) hdrs.forEach((h, i) => { if (i) h.style.width = w === null ? (hdrPct[i] ? hdrPct[i] + '%' : '') : `calc((100% - ${w}px) * ${(hdrPct[i] / sum).toFixed(4)})`; });
      if (w === null) return 0;
      const b = cells.reduce((s, c) => s + broken(c), 0);
      if (!b) cells.forEach(c => { c.style.hyphens = c.style.webkitHyphens = 'manual'; });
      return b;
    };
    for (const wrap of src.querySelectorAll('.tblwrap')) {
      const t = wrap.querySelector('table');
      if (!t || !t.rows.length || t.rows[0].cells.length < 2) continue;
      const mark = document.createComment(''); wrap.replaceWith(mark); pa.appendChild(wrap);
      const cells = firstCells(t);
      const all = [...t.querySelectorAll('td,th')];
      hdrs = [...t.rows[0].cells]; hdrPct = hdrs.map(h => parseFloat(h.style.width) || 0);
      const base = Math.round(cells[0].getBoundingClientRect().width);
      const cap = Math.round(t.getBoundingClientRect().width * 0.3);
      const floor = Math.min(base, 96);
      // 낱말 하나 떨어짐: 첫 열 칸이 두 줄 이상인데 마지막 줄에 3글자 이하(「Priorität / 1」)만 남은 것 (hy0909 결정, 2026-11-04 데이터내보내기 1.1 독일어)
      const orphans = () => cells.reduce((n, c) => { const s = lastLineChars(c); return n + (s.lines >= 2 && s.last <= 3 ? 1 : 0); }, 0);
      const state = b => ({ h: t.getBoundingClientRect().height, b, l: Math.max(...cells.map(lineCount)), la: Math.max(...all.map(lineCount)), o: orphans() });
      const s0 = state(cells.reduce((s, c) => s + broken(c), 0));
      if (s0.b > 0 || s0.l > 2 || s0.o > 0) {
        // 후보 너비: 좁히기(96px까지)와 넓히기(표 너비의 30%까지) 모두 4px씩. 조건: 표 높이가 처음보다 늘지 않고, 어느 칸도 3줄이 되지 않는다(원래 3줄이던 칸은 그 줄 수까지).
        // 고르는 순서: 잘린 낱말 적음 → 떨어진 낱말 적음 → 첫 열 3줄 없음 → 표 높이 낮음 → 원래 너비에 가까움
        const key = (s, w) => [s.b, s.o, s.l > 2 ? 1 : 0, Math.round(s.h), Math.abs(w - base)];
        const better = (a, b) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] < b[i]; return false; };
        let best = { w: base, k: key(s0, base) }; const cands = [];
        for (let w = floor; w <= cap; w += 4) {
          if (w === base) continue;
          const s = state(setW(cells, w));
          cands.push([w, Math.round(s.h), s.b, s.o, s.l, s.la]);
          if (s.h > s0.h + 0.5 || s.la > Math.max(2, s0.la)) continue;
          const k = key(s, w);
          if (better(k, best.k)) best = { w, k };
        }
        if (best.w !== base) { setW(cells, best.w); t.dataset.c0w = best.w; } else setW(cells, null);
        (window.__c0 = window.__c0 || []).push({ base, cap, s0, best, cands });   // 검사용 기록
      }
      mark.replaceWith(wrap);
    }
    probe.remove();
  }

  function newPage(cls) {
    const p = document.createElement('div');
    p.className = 'page ' + (cls || '');
    book.appendChild(p);
    pno += 1;
    p.dataset.pno = pno;
    return p;
  }
  const overflow = a => a.scrollHeight > a.clientHeight + 0.5;

  // [제목 끝 줄 1~3글자 보정, 고정프롬프트 2절] 여러 줄 제목의 마지막 줄에 1~3글자만 남으면
  // 줄 길이를 고르게 나눠(text-wrap:balance) 단어·구절 단위로 다시 줄을 바꾼다. 일본어는 문절 단위(auto-phrase), 한국어는 어절 단위(keep-all).
  const LANG = document.documentElement.lang;
  function lastLineChars(el) {
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const chars = [];
    const r = document.createRange();
    while (tw.nextNode()) {
      const n = tw.currentNode;
      for (let i = 0; i < n.length; i++) {
        if (/\s/.test(n.data[i])) continue;
        r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getBoundingClientRect();
        if (b.width || b.height) chars.push(Math.round(b.top + b.height / 2));
      }
    }
    if (!chars.length) return { lines: 0, last: 0 };
    const lh = parseFloat(getComputedStyle(el).lineHeight) || 20;
    const tops = []; for (const t of chars) if (!tops.some(x => Math.abs(x - t) < lh / 2)) tops.push(t);
    const lastTop = Math.max(...tops);
    return { lines: tops.length, last: chars.filter(t => Math.abs(t - lastTop) < lh / 2).length };
  }
  function fixShortLastLine(el) {
    if (!el) return;
    const s0 = lastLineChars(el);
    if (s0.lines < 2 || s0.last > 3) return;
    el.style.textWrap = 'balance';
    if (LANG === 'ja') el.style.wordBreak = 'auto-phrase';
    else if (LANG === 'ko') el.style.wordBreak = 'keep-all';
    let s1 = lastLineChars(el);
    // balance로 안 풀리면(가타카나 합성어처럼 문절이 긴 경우) 낱말 경계(Intl.Segmenter)에만 줄바꿈 지점(<wbr>)을 넣고 다시 고르게 나눈다
    if ((s1.lines > s0.lines || s1.last <= 3) && (LANG === 'ja' || LANG === 'ko') && window.Intl && Intl.Segmenter) {
      const seg = new Intl.Segmenter(LANG, { granularity: 'word' });
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const nodes = []; while (tw.nextNode()) nodes.push(tw.currentNode);
      for (const n of nodes) {
        const f = document.createDocumentFragment();
        [...seg.segment(n.data)].forEach((p, i) => { if (i) f.appendChild(document.createElement('wbr')); f.appendChild(document.createTextNode(p.segment)); });
        n.replaceWith(f);
      }
      el.style.wordBreak = 'keep-all';
      s1 = lastLineChars(el);
    }
    // 그래도 안 되면 폭을 조금씩 좁혀 앞줄 끝 낱말을 다음 줄로 넘긴다
    if (s1.lines > s0.lines || s1.last <= 3) {
      el.style.textWrap = '';
      const w0 = el.getBoundingClientRect().width;
      for (let k = 0.98; k >= 0.6; k -= 0.02) {
        el.style.maxWidth = (w0 * k) + 'px';
        s1 = lastLineChars(el);
        if (s1.lines > s0.lines) break;
        if (s1.last > 3) break;
      }
    }
    // 줄 수가 늘었거나 그래도 짧으면 되돌린다(글자를 줄이거나 자르지 않는다)
    if (s1.lines > s0.lines || s1.last <= 3) { el.style.textWrap = el.style.wordBreak = el.style.maxWidth = ''; }
    else el.dataset.balanced = s0.last + '→' + s1.last;
  }

  // 블록을 area에 차례로 넣고 넘치면 새 쪽을 만든다. kwn(다음 블록과 붙임)은 함께 넘긴다.
  function flow(blocks, makePage) {
    let area = makePage(true);
    for (const b of blocks) {
      area.appendChild(b);
      if (!overflow(area)) continue;
      if (b.classList.contains('tblwrap')) {
        // 표는 행 단위로 나누고 다음 쪽에 머리행을 다시 붙인다
        let cur = b;
        while (overflow(area)) {
          const body = cur.querySelector('tbody');
          const rest = [];
          while (overflow(area) && body.rows.length > 2) rest.unshift(body.removeChild(body.lastElementChild));
          if (overflow(area)) { // 두 행도 안 들어가면 표 전체를 다음 쪽으로
            area.removeChild(cur);
            area = makePage(false); area.appendChild(cur);
            rest.forEach(r => body.appendChild(r));
            continue;
          }
          if (!rest.length) break;
          const nxt = cur.cloneNode(true);
          const nb = nxt.querySelector('tbody'); nb.innerHTML = '';
          rest.forEach(r => nb.appendChild(r));
          area = makePage(false); area.appendChild(nxt); cur = nxt;
        }
        continue;
      }
      const moving = [b];
      let prev = b.previousElementSibling;
      while (prev && prev.classList.contains('kwn')) { moving.unshift(prev); prev = prev.previousElementSibling; }
      // [빈 공간 채우기 규칙, 고정프롬프트 11절]
      // 1) 묶음 전체(탭·안내·이미지·첫 설명)가 조금 모자라면 캡처를 최대 85%까지 줄여 이 쪽에 둔다.
      const fig = moving.find(m => m.classList.contains('fig'));
      const shots = fig ? [...fig.querySelectorAll('.shot')] : [];
      const base = shots.map(s => parseFloat(s.style.width));
      const scaleFig = k => shots.forEach((s, i) => { s.style.width = (base[i] * k) + 'px'; });
      if (fig && moving.length < area.children.length) {
        let fitted = false;
        for (const k of [0.95, 0.9, 0.85]) { scaleFig(k); if (!overflow(area)) { fitted = true; fig.dataset.scale = k; break; } }
        if (fitted) continue;
        scaleFig(1);
        // 2) 그래도 안 되면 이미지 뒤 설명은 다음 쪽으로 넘기고, 탭·안내·이미지는 이 쪽에 둔다(캡처 최대 75%).
        //    설명이 다음 쪽으로 넘어가도 이 쪽을 비워 두지 않는다.
        const tail = moving.slice(moving.indexOf(fig) + 1);
        if (tail.length) {
          tail.forEach(t => area.removeChild(t));
          for (const k of [1, 0.95, 0.9, 0.85, 0.8, 0.75]) { scaleFig(k); if (!overflow(area)) { fitted = true; if (k < 1) fig.dataset.scale = k; break; } }
          if (fitted) { area = makePage(false); tail.forEach(t => area.appendChild(t)); continue; }
          scaleFig(1); tail.forEach(t => area.appendChild(t));
        }
      }
      // 3) 유의사항 카드는 통째로 넘기지 않고 항목 단위로 나눠 이어 쓴다(같은 카드 제목을 다음 쪽 카드에 다시 붙임).
      if (b.classList.contains('card')) {
        const ul = b.querySelector('ul'); const rest = [];
        while (overflow(area) && ul.children.length > 1) rest.unshift(ul.removeChild(ul.lastElementChild));
        if (!overflow(area) && rest.length) {
          const nxt = b.cloneNode(true); const nu = nxt.querySelector('ul'); nu.innerHTML = '';
          rest.forEach(r => nu.appendChild(r));
          area = makePage(false); area.appendChild(nxt); continue;
        }
        rest.forEach(r => ul.appendChild(r));
      }
      if (moving.length === area.children.length) {
        if (moving.length === 1) continue; // 한 쪽보다 큰 블록: 그대로 둔다
        moving.splice(0, moving.length - 1); // 쪽 전체가 묶음이면 마지막 블록만 넘긴다
      }
      area = makePage(false);
      moving.forEach(m => area.appendChild(m));
    }
  }

  // 표지
  const cover = newPage('cover');
  cover.append(...src.querySelector('section.cover').children);
  cover.querySelectorAll('.cv-title, .cv-sub').forEach(fixShortLastLine);
  pageMap.cover = 1;

  // 목차
  const tocBlocks = [...src.querySelectorAll('section.toc .tch')];
  let firstToc = true;
  flow(tocBlocks, () => {
    const p = newPage('toc');
    p.innerHTML = `<div class="toc-h"><h1>${src.querySelector('section.toc').dataset.title}</h1><img class="brand" src="img/smart-edc-logo-gray.png" alt="SMART EDC"></div><div class="area"></div>`;
    if (firstToc) { p.id = 'toc'; pageMap.toc = +p.dataset.pno; firstToc = false; }
    return p.querySelector('.area');
  });

  // 간지 + 절
  for (const sec of src.querySelectorAll('section.divider, section.sec')) {
    if (sec.classList.contains('divider')) {
      const p = newPage('divider');
      p.append(...sec.children);
      p.querySelectorAll('.dtitle, .dlist .dt').forEach(fixShortLastLine);
      const bar = document.createElement('div'); bar.className = 'dbar'; p.appendChild(bar);
      const pn = document.createElement('div'); pn.className = 'pno'; pn.textContent = p.dataset.pno; p.appendChild(pn);
      pageMap['ch' + sec.dataset.ch] = +p.dataset.pno;
      continue;
    }
    const hdr = sec.querySelector('template.hdr-tpl').innerHTML;
    const blocks = [...sec.querySelector('.flow').children];
    let first = true;
    flow(blocks, () => {
      const p = newPage('body');
      if (first) { p.id = sec.id; pageMap[sec.dataset.num] = +p.dataset.pno; }
      p.innerHTML = `<header class="hdr">${hdr}</header><div class="area"></div><footer class="ftr"><span class="chn">${sec.dataset.chtitle}</span><img class="brand" src="img/smart-edc-logo-footer.png" alt="SMART EDC"><span class="pg">${p.dataset.pno}</span></footer>`;
      first = false;
      // 가변 높이 법칙: 본문 시작 = 실제 헤더 아래끝 + 22px (한 줄 헤더 98px → 120px)
      fixShortLastLine(p.querySelector('.hdr .hx'));
      const area = p.querySelector('.area');
      area.style.top = (p.querySelector('.hdr').getBoundingClientRect().height + 22) + 'px';
      return area;
    });
  }
  src.remove();
  document.querySelectorAll('.page.toc .tct, .page.toc .tt').forEach(fixShortLastLine);

  // 간지 장식 막대: 큰 번호 글자 윗선 ~ 제목 아랫선
  for (const p of document.querySelectorAll('.page.divider')) {
    const n = p.querySelector('.dnum'), t = p.querySelector('.dtitle'), bar = p.querySelector('.dbar');
    const pr = p.getBoundingClientRect(), nr = n.getBoundingClientRect(), tr = t.getBoundingClientRect();
    const fs = parseFloat(getComputedStyle(n).fontSize);
    const top = nr.top - pr.top + (nr.height - fs * 0.72) / 2;   // 숫자 대략 cap-height 위치
    bar.style.top = top + 'px';
    bar.style.height = (tr.bottom - pr.top - top) + 'px';
  }

  // 목차 쪽번호
  for (const tp of document.querySelectorAll('.tp')) {
    const id = tp.dataset.for;
    const pg = document.getElementById(id);
    tp.textContent = pg ? pg.dataset.pno : '?';
  }

  // 설정 → 결과 점선 연결: 설정 원 아래 중앙 → 결과 원 왼쪽 중앙
  const NS = 'http://www.w3.org/2000/svg';
  for (const item of document.querySelectorAll('.item')) {
    const ress = item.querySelectorAll('.res > .cir');
    if (!ress.length) continue;
    const page = item.closest('.page');
    const ir = page.getBoundingClientRect();
    const pc = item.querySelector(':scope > .cir').getBoundingClientRect();
    const x0 = pc.left + pc.width / 2 - ir.left, y0 = pc.bottom - ir.top;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'conn'); svg.setAttribute('width', ir.width); svg.setAttribute('height', ir.height);
    svg.setAttribute('aria-hidden', 'true');
    let d = '';
    ress.forEach(rc => {
      const r = rc.getBoundingClientRect();
      const y = r.top + r.height / 2 - ir.top, x1 = r.left - ir.left;
      d += `M${x0} ${y0}V${y}H${x1}`;
    });
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', d); path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#94A3B8');
    path.setAttribute('stroke-width', '1'); path.setAttribute('stroke-dasharray', '2 2');
    svg.appendChild(path);
    page.appendChild(svg);
  }
  // 표지 제목: 한 낱말(예: DE „Untersuchungspanel“)이 폭을 넘으면 넘지 않을 때까지 글자 크기를 줄인다(가변 높이 법칙과 같은 취지)
  document.querySelectorAll('.cv-title').forEach(t => {
    let fs = parseFloat(getComputedStyle(t).fontSize);
    while (t.scrollWidth > t.clientWidth + 1 && fs > 48) { fs -= 2; t.style.fontSize = fs + 'px'; t.style.lineHeight = (Math.round(fs * 1.21 / 2) * 2) + 'px'; }   // 글자 크기·줄 높이는 짝수 px (2026-11-09)
  });
  window.__pageMap = pageMap;
  window.__pageCount = pno;
  window.__done = true;
})();
