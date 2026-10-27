import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function currentLanguage() {
  return window.location.hash === '#zh' ? 'zh' : 'en';
}

function App() {
  const [language, setLanguage] = useState(currentLanguage);
  const [clicks, setClicks] = useState(0);

  useEffect(() => {
    const onHashChange = () => setLanguage(currentLanguage());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const zh = language === 'zh';

  return (
    <main className="card">
      <nav aria-label="Language / 语言">
        <a href="#en" aria-current={!zh ? 'page' : undefined}>English</a>
        <a href="#zh" aria-current={zh ? 'page' : undefined}>中文</a>
      </nav>
      <p className="eyebrow">React + Vite · Toy</p>
      <h1>{zh ? '让想法动起来。' : 'Build your idea.'}</h1>
      <p>{zh ? '此示例用 hash 切换页面状态，不要求服务器处理子路径。' : 'This example uses hash navigation so the server does not need to handle nested routes.'}</p>
      <p className="secondary">{zh ? 'Toy 位于 /toy/作品地址/ 子目录；资源路径由 Vite 的相对 base 处理。' : 'Toy lives under its own subdirectory; Vite emits relative asset paths.'}</p>
      <div className="counter" aria-live="polite">
        <span>{zh ? '点击次数' : 'Clicks'}</span><strong>{clicks}</strong>
      </div>
      <button type="button" onClick={() => setClicks((value) => value + 1)}>{zh ? '点我试试' : 'Try it'}</button>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
