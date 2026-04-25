import layout from './modules/layout'
import dashboard from './modules/dashboard'
import players from './modules/players'
import tournaments from './modules/tournaments'
import registrations from './modules/registrations'
import draws from './modules/draws'
import news from './modules/news'
import rankings from './modules/rankings'
import matches from './modules/matches'
import payments from './modules/payments'
import logs from './modules/logs'
import mailCampaign from './modules/mailCampaign'
import courts from './modules/courts'

export default {
  ...layout,
  ...dashboard,
  ...players,
  ...tournaments,
  ...registrations,
  ...draws,
  ...news,
  ...rankings,
  ...matches,
  ...payments,
  ...logs,
  ...mailCampaign,
  ...courts
}
