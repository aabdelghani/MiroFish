<template>
  <div class="app-wrap">
    <router-view />
    <div class="locale-switcher">
      <button
        class="locale-btn"
        :class="{ active: locale === 'en' }"
        @click="setLocale('en')"
      >EN</button>
      <span class="locale-sep">|</span>
      <button
        class="locale-btn"
        :class="{ active: locale === 'zh' }"
        @click="setLocale('zh')"
      >中文</button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { setLocale } from './i18n'

const { locale } = useI18n()
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getStoredLocale } from './i18n'

// Sync html lang attribute on mount
onMounted(() => {
  const locale = getStoredLocale()
  document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en'
})
</script>

<style>
.app-wrap {
  position: relative;
  min-height: 100vh;
}

.locale-switcher {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0,0,0,0.06);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 13px;
}

.locale-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  color: #666;
  font-weight: 500;
}

.locale-btn:hover {
  color: #000;
  background: rgba(0,0,0,0.06);
}

.locale-btn.active {
  color: #000;
  background: rgba(255,255,255,0.9);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
}

.locale-sep {
  color: #999;
  user-select: none;
}

/* Global resets */
// Vue Router manages page navigation.
</script>

<style>
// Vue Router manages page navigation.
</script>

<style>
/* Global reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

/* Scrollbar styles */
/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Global button styles */
/* Global button styling */
button {
  font-family: inherit;
}
</style>
