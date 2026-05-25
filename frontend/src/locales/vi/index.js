import nav from './customer/nav.js'
import common from './common.js'
import home from './customer/home.js'
import auth from './auth/auth.js'
import chat from './customer/chat.js'
import footer from './customer/footer.js'
import news from './customer/news.js'
import rankings from './customer/rankings.js'
import matches from './customer/matches.js'
import tournaments from './customer/tournaments.js'
import challenges from './customer/challenges.js'
import players from './customer/players.js'
import profile from './customer/profile.js'
import admin from './admin/admin.js'

export default {
  nav,
  common,
  home: {
    ...home,
    goldPartner: 'Đối tác Vàng',
    featuredTournaments: 'GIẢI ĐẤU TIÊU BIỂU',
    viewAllTournaments: 'Xem tất cả giải đấu',
  },
  auth,
  chat,
  footer,
  news,
  rankings,
  matches,
  tournaments: {
    ...tournaments,
    tournamentFee: 'Lệ phí giải',
    freeFee: 'Miễn phí',
    registrationTime: 'Thời gian đăng ký',
    participants: 'Danh sách VĐV',
    noParticipants: 'Chưa có VĐV nào đăng ký.'
  },
  challenges,
  players,
  profile,
  admin
}
