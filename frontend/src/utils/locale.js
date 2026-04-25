import i18n from '../locales/index.js'

export const currentLocale = i18n.global.locale

export const t = (key, params) => i18n.global.t(key, params)

export const toggleLocale = () => {
  const newLocale = currentLocale.value === 'vi' ? 'en' : 'vi'
  currentLocale.value = newLocale
  localStorage.setItem('app_locale', newLocale)
}
