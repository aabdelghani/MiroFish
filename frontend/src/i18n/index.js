import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

const STORAGE_KEY = 'mirofish_locale'

function getDefaultLocale() {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'zh'
  } catch {
    return 'zh'
  }
}

function setStoredLocale(locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch (_) {}
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: { zh, en },
  globalInjection: true,
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  setStoredLocale(locale)
}

export function getLocale() {
  return i18n.global.locale.value
}

import en from './en.json'
import zh from './zh.json'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: localStorage.getItem('locale') || 'en',
  fallbackLocale: 'en',
  messages: { en, zh }
import ko from './locales/ko'

const LOCALE_KEY = 'mirofish-locale'
const SUPPORTED_LOCALES = ['zh', 'en', 'ko']

export function getStoredLocale() {
  try {
    const stored = localStorage.getItem(LOCALE_KEY)
    if (SUPPORTED_LOCALES.includes(stored)) return stored
  } catch (_) {}
  return 'zh'
}

export function setStoredLocale(locale) {
  try {
    localStorage.setItem(LOCALE_KEY, locale)
  } catch (_) {}
}

/** Get locale for API requests (en or zh) */
export function getApiLocale() {
  return getStoredLocale()
}

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: getStoredLocale(),
  fallbackLocale: 'zh',
  messages: {
    zh,
    en,
    ko,
  },
})

export default i18n
