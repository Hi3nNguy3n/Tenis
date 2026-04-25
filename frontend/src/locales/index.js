import { createI18n } from 'vue-i18n'
import vi from './vi/index.js'
import en from './en/index.js'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('app_locale') || 'vi',
  fallbackLocale: 'vi',
  messages: {
    vi,
    en
  }
})

export default i18n
