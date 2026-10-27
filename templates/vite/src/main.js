import './style.css';

document.querySelector('#app').innerHTML = `
  <main class="card">
    <p class="eyebrow">Bilibili Toy starter · 哔哩哔哩 Toy 起点</p>
    <h1>Build your idea.<br><span>让想法动起来。</span></h1>
    <p>This Vite project builds relative asset URLs for Toy's subdirectory.</p>
    <p>这个 Vite 项目会为 Toy 子目录生成相对资源路径。</p>
    <div class="counter" aria-live="polite">
      <span>Clicks · 点击次数</span><strong id="count">0</strong>
    </div>
    <button id="add" type="button">Try it · 点我试试</button>
  </main>
`;

let clicks = 0;
document.querySelector('#add').addEventListener('click', () => {
  document.querySelector('#count').textContent = String(++clicks);
});
