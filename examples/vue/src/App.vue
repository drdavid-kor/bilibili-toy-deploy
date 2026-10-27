<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';

const language = ref(window.location.hash === '#zh' ? 'zh' : 'en');
const clicks = ref(0);
const zh = computed(() => language.value === 'zh');

function onHashChange() {
  language.value = window.location.hash === '#zh' ? 'zh' : 'en';
}

onMounted(() => window.addEventListener('hashchange', onHashChange));
onUnmounted(() => window.removeEventListener('hashchange', onHashChange));
</script>

<template>
  <main class="card">
    <nav aria-label="Language / 语言">
      <a href="#en" :aria-current="!zh ? 'page' : undefined">English</a>
      <a href="#zh" :aria-current="zh ? 'page' : undefined">中文</a>
    </nav>
    <p class="eyebrow">Vue + Vite · Toy</p>
    <h1>{{ zh ? '让想法动起来。' : 'Build your idea.' }}</h1>
    <p>{{ zh ? '此示例用 hash 切换页面状态，不要求服务器处理子路径。' : 'This example uses hash navigation so the server does not need to handle nested routes.' }}</p>
    <p class="secondary">{{ zh ? 'Toy 位于 /toy/作品地址/ 子目录；资源路径由 Vite 的相对 base 处理。' : 'Toy lives under its own subdirectory; Vite emits relative asset paths.' }}</p>
    <div class="counter" aria-live="polite"><span>{{ zh ? '点击次数' : 'Clicks' }}</span><strong>{{ clicks }}</strong></div>
    <button type="button" @click="clicks += 1">{{ zh ? '点我试试' : 'Try it' }}</button>
  </main>
</template>
