/**
 * Simple FE data contracts for admin modules.
 * Keep these as reference shapes before wiring real APIs.
 */

export const TournamentStatus = Object.freeze({
  DRAFT: 'draft',
  OPEN: 'open',
  ONGOING: 'ongoing',
  FINISHED: 'finished',
})


export const RegistrationStatus = Object.freeze({
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  REJECTED: 'rejected',
  CANCELLED: 'cancelled',
})

export const PaymentStatus = Object.freeze({
  HOLDING: 'holding',
  PAID: 'paid',
  EXPIRED: 'expired',
  REFUNDED: 'refunded',
})


export const CourtStatus = Object.freeze({
  AVAILABLE: 'available',
  MAINTENANCE: 'maintenance',
  UNAVAILABLE: 'unavailable',
})

export const ScheduleStatus = Object.freeze({
  SCHEDULED: 'scheduled',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
})

export const createTournament = ({
  id,
  name,
  status = TournamentStatus.DRAFT,
  drawSize = 32,
  category = 'Open',
  location = 'Saigon',
}) => ({
  id,
  name,
  status,
  drawSize,
  category,
  location,
})

export const createRegistration = ({
  id,
  tournamentId,
  playerName,
  paymentStatus = PaymentStatus.UNPAID,
  approved = false,
}) => ({
  id,
  tournamentId,
  playerName,
  paymentStatus,
  approved,
})

export const createCourt = ({
  id,
  name,
  surface = 'Hard',
  location = 'Saigon Tennis Club',
  status = CourtStatus.AVAILABLE,
}) => ({
  id,
  name,
  surface,
  location,
  status,
})

export const createMatchSlot = ({
  id,
  tournamentId,
  courtId,
  date,
  startTime,
  endTime,
  status = ScheduleStatus.SCHEDULED,
  note = '',
}) => ({
  id,
  tournamentId,
  courtId,
  date,
  startTime,
  endTime,
  status,
  note,
})
