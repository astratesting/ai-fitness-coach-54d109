'use client';

import { useMemo, useState } from 'react';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import {
  Activity,
  ArrowRight,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ChefHat,
  Clock3,
  Dumbbell,
  Flame,
  HeartPulse,
  LineChart,
  Lock,
  MessageCircle,
  Play,
  Salad,
  ShieldCheck,
  Sparkles,
  Target,
  TimerReset,
  Trophy,
  Zap,
} from 'lucide-react';

const weekPlan = [
  { day: 'Mon', focus: 'Strength', time: '28m', intensity: 'High', color: 'from-orange-400 to-red-500' },
  { day: 'Tue', focus: 'Mobility', time: '16m', intensity: 'Low', color: 'from-emerald-300 to-teal-500' },
  { day: 'Wed', focus: 'Intervals', time: '22m', intensity: 'High', color: 'from-yellow-300 to-orange-500' },
  { day: 'Thu', focus: 'Recovery', time: '14m', intensity: 'Easy', color: 'from-sky-300 to-cyan-500' },
  { day: 'Fri', focus: 'Power', time: '31m', intensity: 'Max', color: 'from-rose-400 to-fuchsia-600' },
];

const meals = [
  { name: 'Protein breakfast bowl', macro: '42g protein', kcal: '510 kcal' },
  { name: 'Desk-friendly salmon wrap', macro: '34g protein', kcal: '620 kcal' },
  { name: 'Late-meeting recovery shake', macro: '28g protein', kcal: '330 kcal' },
];

const progress = [
  { label: 'Weekly adherence', value: '92%', icon: CheckCircle2 },
  { label: 'Avg session', value: '24m', icon: Clock3 },
  { label: 'Energy trend', value: '+18%', icon: LineChart },
];

const coachMessages = [
  'Calendar packed. Switching leg day to 18-minute hotel-room circuit.',
  'Lunch sodium high today. Dinner plan adjusted with potassium-rich sides.',
  'Sleep debt detected. Tomorrow starts with zone-2, not HIIT.',
];

const featureCards = [
  {
    icon: Dumbbell,
    title: 'Adaptive workouts',
    text: 'Plans reshape around meetings, equipment, soreness, and real available time.',
  },
  {
    icon: Salad,
    title: 'Nutrition tracking',
    text: 'Macro targets, meal suggestions, and missed-meal recovery without spreadsheet work.',
  },
  {
    icon: MessageCircle,
    title: 'AI coach',
    text: 'Daily coaching that explains tradeoffs, nudges behavior, and keeps momentum sane.',
  },
  {
    icon: BarChart3,
    title: 'Progress cockpit',
    text: 'Strength, consistency, body metrics, and recovery signals in one executive dashboard.',
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
};

export default function HomePage() {
  const [selectedDay, setSelectedDay] = useState(0);
  const activeDay = weekPlan[selectedDay];

  const currentCoachMessage = useMemo(
    () => coachMessages[selectedDay % coachMessages.length],
    [selectedDay],
  );

  return (
    <main className="min-h-screen overflow-hidden bg-[#0b0f0a] text-stone-50 selection:bg-lime-300 selection:text-black">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
          --coach-ink: #0b0f0a;
          --coach-lime: #d8ff3e;
          --coach-mint: #9affc8;
          --coach-clay: #ff7a3d;
          --coach-paper: #f7f1df;
        }

        body {
          background: #0b0f0a;
        }

        .font-display {
          font-family: 'Archivo Black', sans-serif;
        }

        .font-editorial {
          font-family: 'Fraunces', serif;
        }

        .font-body {
          font-family: 'Manrope', sans-serif;
        }

        .coach-grid {
          background-image:
            linear-gradient(rgba(216, 255, 62, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(216, 255, 62, 0.08) 1px, transparent 1px);
          background-size: 44px 44px;
        }

        .grain::before {
          content: '';
          pointer-events: none;
          position: fixed;
          inset: 0;
          z-index: 50;
          opacity: 0.13;
          mix-blend-mode: screen;
          background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,.35) 1px, transparent 0);
          background-size: 6px 6px;
        }

        .pulse-ring {
          animation: pulse-ring 2.8s cubic-bezier(.2,.9,.2,1) infinite;
        }

        @keyframes pulse-ring {
          0% { transform: scale(.84); opacity: .75; }
          70% { transform: scale(1.14); opacity: 0; }
          100% { transform: scale(1.14); opacity: 0; }
        }

        .ticker {
          animation: ticker 24s linear infinite;
        }

        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>

      <div className="grain relative font-body">
        <div className="pointer-events-none absolute left-1/2 top-[-18rem] h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-lime-300/25 blur-3xl" />
        <div className="pointer-events-none absolute right-[-16rem] top-40 h-[34rem] w-[34rem] rounded-full bg-orange-500/20 blur-3xl" />
        <div className="pointer-events-none absolute bottom-20 left-[-14rem] h-[28rem] w-[28rem] rounded-full bg-emerald-400/16 blur-3xl" />

        <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
          <a href="#top" className="group flex items-center gap-3" aria-label="AI Fitness Coach home">
            <span className="relative grid h-11 w-11 place-items-center rounded-2xl border border-lime-200/30 bg-lime-300 text-black shadow-[0_0_30px_rgba(216,255,62,.35)]">
              <span className="absolute inset-0 rounded-2xl border border-lime-200/30 pulse-ring" />
              <HeartPulse className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="leading-none">
              <span className="block font-display text-sm uppercase tracking-[0.28em] text-lime-200">PulseForge</span>
              <span className="block text-xs font-semibold uppercase tracking-[0.2em] text-stone-400">AI Fitness Coach</span>
            </span>
          </a>

          <nav className="hidden items-center gap-8 text-sm font-bold text-stone-300 md:flex" aria-label="Primary navigation">
            <a href="#plans" className="transition hover:text-lime-200">Plans</a>
            <a href="#nutrition" className="transition hover:text-lime-200">Nutrition</a>
            <a href="#coach" className="transition hover:text-lime-200">AI Coach</a>
            <a href="#progress" className="transition hover:text-lime-200">Progress</a>
          </nav>

          <div className="flex items-center gap-3">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="rounded-full border border-stone-700 bg-stone-950/80 px-4 py-2 text-sm font-extrabold text-stone-100 shadow-2xl transition hover:border-lime-300 hover:text-lime-200">
                  Sign in
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <div className="rounded-full border border-stone-700 bg-stone-950/80 p-1">
                <UserButton afterSignOutUrl="/" />
              </div>
            </SignedIn>
          </div>
        </header>

        <section id="top" className="relative z-10 mx-auto grid max-w-7xl gap-10 px-5 pb-16 pt-8 sm:px-8 lg:grid-cols-[1.02fr_.98fr] lg:pb-24 lg:pt-16">
          <motion.div
            initial="hidden"
            animate="show"
            transition={{ staggerChildren: 0.11 }}
            className="flex flex-col justify-center"
          >
            <motion.div variants={fadeUp} className="mb-7 inline-flex w-fit items-center gap-2 rounded-full border border-lime-200/25 bg-lime-200/10 px-3 py-2 text-xs font-extrabold uppercase tracking-[0.22em] text-lime-100">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Built for 25-minute lives
            </motion.div>

            <motion.h1 variants={fadeUp} className="font-display text-[clamp(3.6rem,9vw,8.6rem)] uppercase leading-[0.78] tracking-[-0.08em] text-stone-50">
              Fitness that bends around work.
            </motion.h1>

            <motion.p variants={fadeUp} className="mt-8 max-w-2xl text-lg font-medium leading-8 text-stone-300 sm:text-xl">
              Personalized workouts, nutrition, AI coaching, and progress tracking for professionals whose calendars fight back.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-9 flex flex-col gap-4 sm:flex-row">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="group inline-flex items-center justify-center gap-3 rounded-full bg-lime-300 px-7 py-4 text-base font-black text-black shadow-[0_18px_60px_rgba(216,255,62,.33)] transition hover:-translate-y-1 hover:bg-lime-200">
                    Start adaptive plan
                    <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" aria-hidden="true" />
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <a href="#dashboard" className="group inline-flex items-center justify-center gap-3 rounded-full bg-lime-300 px-7 py-4 text-base font-black text-black shadow-[0_18px_60px_rgba(216,255,62,.33)] transition hover:-translate-y-1 hover:bg-lime-200">
                  Open dashboard
                  <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" aria-hidden="true" />
                </a>
              </SignedIn>
              <a href="#coach" className="inline-flex items-center justify-center gap-3 rounded-full border border-stone-700 bg-stone-950/70 px-7 py-4 text-base font-black text-stone-100 backdrop-blur transition hover:border-orange-300 hover:text-orange-200">
                <Play className="h-5 w-5" aria-hidden="true" />
                See coaching loop
              </a>
            </motion.div>

            <motion.div variants={fadeUp} className="mt-10 grid max-w-xl grid-cols-3 gap-3">
              {progress.map(({ label, value, icon: Icon }) => (
                <div key={label} className="rounded-3xl border border-stone-800 bg-stone-950/55 p-4 backdrop-blur">
                  <Icon className="mb-3 h-5 w-5 text-lime-200" aria-hidden="true" />
                  <p className="font-display text-2xl leading-none text-white">{value}</p>
                  <p className="mt-2 text-xs font-bold uppercase tracking-[0.14em] text-stone-500">{label}</p>
                </div>
              ))}
            </motion.div>
          </motion.div>

          <motion.div
            id="dashboard"
            initial={{ opacity: 0, scale: 0.96, rotate: 1.5 }}
            animate={{ opacity: 1, scale: 1, rotate: -1.2 }}
            transition={{ duration: 0.75, ease: [0.2, 0.8, 0.2, 1] }}
            className="relative"
          >
            <div className="absolute -inset-5 rotate-3 rounded-[3rem] bg-lime-300/10 blur-2xl" />
            <div className="coach-grid relative overflow-hidden rounded-[2.4rem] border border-lime-200/20 bg-[#11170f]/90 p-4 shadow-[0_28px_100px_rgba(0,0,0,.55)] backdrop-blur xl:p-5">
              <div className="rounded-[2rem] border border-stone-700/70 bg-black/45 p-5 sm:p-7">
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.25em] text-lime-200">Today</p>
                    <h2 className="mt-2 font-editorial text-4xl font-black tracking-[-0.04em] text-white sm:text-5xl">
                      {activeDay.focus} in {activeDay.time}
                    </h2>
                  </div>
                  <div className="rounded-2xl bg-orange-500 px-3 py-2 text-xs font-black uppercase tracking-[0.18em] text-black">
                    {activeDay.intensity}
                  </div>
                </div>

                <div className="mt-7 grid gap-3 sm:grid-cols-5">
                  {weekPlan.map((item, index) => (
                    <button
                      key={item.day}
                      onClick={() => setSelectedDay(index)}
                      className={`group rounded-3xl border p-3 text-left transition ${
                        selectedDay === index
                          ? 'border-lime-200 bg-lime-200 text-black shadow-[0_16px_45px_rgba(216,255,62,.22)]'
                          : 'border-stone-800 bg-stone-950/75 text-stone-300 hover:border-lime-200/60'
                      }`}
                      aria-pressed={selectedDay === index}
                    >
                      <p className="text-xs font-black uppercase tracking-[0.18em]">{item.day}</p>
                      <div className={`mt-8 h-16 rounded-2xl bg-gradient-to-br ${item.color}`} />
                      <p className="mt-3 text-sm font-black">{item.time}</p>
                    </button>
                  ))}
                </div>

                <div className="mt-6 grid gap-4 lg:grid-cols-[.9fr_1.1fr]">
                  <div className="rounded-[1.8rem] border border-stone-800 bg-stone-950/80 p-5">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-black uppercase tracking-[0.2em] text-stone-400">Coach adjustment</p>
                      <Zap className="h-5 w-5 text-orange-300" aria-hidden="true" />
                    </div>
                    <p className="mt-5 text-lg font-extrabold leading-7 text-stone-100">{currentCoachMessage}</p>
                  </div>

                  <div className="rounded-[1.8rem] border border-stone-800 bg-[#f7f1df] p-5 text-black">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-black uppercase tracking-[0.2em] text-black/55">Readiness</p>
                      <Activity className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <div className="mt-5 flex items-end gap-2">
                      {[38, 56, 44, 72, 86, 64, 91].map((height, index) => (
                        <div key={index} className="flex-1 rounded-full bg-black/10 p-1">
                          <div className="rounded-full bg-black" style={{ height: `${height}px` }} />
                        </div>
                      ))}
                    </div>
                    <p className="mt-5 font-display text-4xl tracking-[-0.05em]">91</p>
                    <p className="text-sm font-extrabold text-black/60">Ready for focused effort after 6:30 PM.</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        <section className="relative z-10 border-y border-lime-200/15 bg-lime-300 py-3 text-black">
          <div className="ticker flex w-[200%] gap-8 whitespace-nowrap font-display text-2xl uppercase tracking-[-0.04em] sm:text-4xl">
            {Array.from({ length: 2 }).map((_, group) => (
              <div key={group} className="flex min-w-1/2 items-center gap-8">
                <span>Workout plans</span><Flame className="h-7 w-7" />
                <span>Macro tracking</span><ChefHat className="h-7 w-7" />
                <span>AI coaching</span><Sparkles className="h-7 w-7" />
                <span>Progress dashboard</span><Trophy className="h-7 w-7" />
              </div>
            ))}
          </div>
        </section>

        <section id="plans" className="relative z-10 mx-auto max-w-7xl px-5 py-20 sm:px-8">
          <div className="grid gap-5 md:grid-cols-4">
            {featureCards.map(({ icon: Icon, title, text }, index) => (
              <motion.article
                key={title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-80px' }}
                transition={{ delay: index * 0.08 }}
                className="group min-h-[260px] rounded-[2rem] border border-stone-800 bg-stone-950/70 p-6 backdrop-blur transition hover:-translate-y-2 hover:border-lime-200/60 hover:bg-stone-900"
              >
                <div className="grid h-13 w-13 place-items-center rounded-2xl bg-stone-900 text-lime-200 ring-1 ring-stone-700 transition group-hover:bg-lime-300 group-hover:text-black">
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>
                <h3 className="mt-12 font-editorial text-3xl font-black tracking-[-0.04em] text-white">{title}</h3>
                <p className="mt-4 text-sm font-semibold leading-6 text-stone-400">{text}</p>
              </motion.article>
            ))}
          </div>
        </section>

        <section id="nutrition" className="relative z-10 mx-auto grid max-w-7xl gap-8 px-5 pb-20 sm:px-8 lg:grid-cols-[.9fr_1.1fr]">
          <div className="rounded-[2.5rem] bg-[#f7f1df] p-7 text-black sm:p-10">
            <p className="text-sm font-black uppercase tracking-[0.22em] text-black/50">Nutrition engine</p>
            <h2 className="mt-4 font-display text-5xl uppercase leading-[0.86] tracking-[-0.07em] sm:text-7xl">
              Eat for meetings, muscle, and sanity.
            </h2>
            <p className="mt-7 max-w-xl text-lg font-bold leading-8 text-black/65">
              Log meals fast, hit protein, recover from travel days, and keep calories aligned with goals without turning food into second job.
            </p>
          </div>

          <div className="grid gap-4">
            {meals.map((meal, index) => (
              <motion.div
                key={meal.name}
                initial={{ opacity: 0, x: 28 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="rounded-[2rem] border border-stone-800 bg-stone-950/70 p-6 backdrop-blur"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="grid h-14 w-14 place-items-center rounded-2xl bg-orange-500 text-black">
                      <ChefHat className="h-6 w-6" aria-hidden="true" />
                    </div>
                    <div>
                      <h3 className="text-xl font-black text-white">{meal.name}</h3>
                      <p className="mt-1 text-sm font-bold text-stone-500">{meal.macro}</p>
                    </div>
                  </div>
                  <p className="rounded-full bg-lime-300 px-4 py-2 text-sm font-black text-black">{meal.kcal}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        <section id="coach" className="relative z-10 mx-auto max-w-7xl px-5 pb-20 sm:px-8">
          <div className="overflow-hidden rounded-[2.5rem] border border-lime-200/20 bg-stone-950/75 shadow-2xl backdrop-blur">
            <div className="grid lg:grid-cols-[.85fr_1.15fr]">
              <div className="border-b border-stone-800 p-7 sm:p-10 lg:border-b-0 lg:border-r">
                <p className="text-sm font-black uppercase tracking-[0.22em] text-lime-200">AI-powered coaching</p>
                <h2 className="mt-5 font-editorial text-5xl font-black leading-none tracking-[-0.06em] text-white sm:text-6xl">
                  Coach with context, not generic motivation.
                </h2>
                <p className="mt-6 text-lg font-semibold leading-8 text-stone-400">
                  Reads plan adherence, nutrition, recovery, and schedule pressure. Then gives next best action before day falls apart.
                </p>
              </div>
              <div className="space-y-4 p-5 sm:p-8">
                {coachMessages.map((message, index) => (
                  <div key={message} className={`max-w-[92%] rounded-[1.8rem] p-5 ${index === 1 ? 'ml-auto bg-lime-300 text-black' : 'bg-stone-900 text-stone-100'}`}>
                    <div className="mb-3 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] opacity-60">
                      {index === 1 ? <Target className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                      {index === 1 ? 'Action' : 'Coach'}
                    </div>
                    <p className="text-lg font-extrabold leading-7">{message}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="progress" className="relative z-10 mx-auto max-w-7xl px-5 pb-24 sm:px-8">
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="rounded-[2.2rem] border border-stone-800 bg-stone-950/70 p-7 lg:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-black uppercase tracking-[0.22em] text-stone-500">Progress tracking</p>
                  <h2 className="mt-3 font-display text-5xl uppercase leading-none tracking-[-0.06em] text-white">Executive health score</h2>
                </div>
                <div className="rounded-full bg-lime-300 px-5 py-3 text-sm font-black text-black">+12 points this month</div>
              </div>
              <div className="mt-8 grid gap-4 sm:grid-cols-3">
                {[
                  { label: 'Strength', value: 78, icon: Dumbbell },
                  { label: 'Consistency', value: 92, icon: CalendarDays },
                  { label: 'Recovery', value: 84, icon: TimerReset },
                ].map(({ label, value, icon: Icon }) => (
                  <div key={label} className="rounded-[1.6rem] bg-stone-900 p-5">
                    <div className="flex items-center justify-between">
                      <Icon className="h-5 w-5 text-lime-200" aria-hidden="true" />
                      <span className="font-display text-3xl tracking-[-0.05em] text-white">{value}</span>
                    </div>
                    <div className="mt-6 h-2 overflow-hidden rounded-full bg-stone-800">
                      <div className="h-full rounded-full bg-lime-300" style={{ width: `${value}%` }} />
                    </div>
                    <p className="mt-4 text-sm font-black uppercase tracking-[0.18em] text-stone-500">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[2.2rem] border border-orange-300/30 bg-orange-500 p-7 text-black">
              <ShieldCheck className="h-9 w-9" aria-hidden="true" />
              <h3 className="mt-8 font-editorial text-4xl font-black tracking-[-0.05em]">Secure by default.</h3>
              <p className="mt-4 text-base font-extrabold leading-7 text-black/70">
                Clerk authentication gates personal dashboard data. Backend API can enforce user identity for plans, meals, coaching, and metrics.
              </p>
              <div className="mt-8 flex items-center gap-2 rounded-full bg-black px-4 py-3 text-sm font-black text-orange-100">
                <Lock className="h-4 w-4" aria-hidden="true" />
                Auth-ready MVP shell
              </div>
            </div>
          </div>
        </section>

        <footer className="relative z-10 border-t border-stone-800 px-5 py-8 sm:px-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-4 text-sm font-bold text-stone-500 sm:flex-row sm:items-center sm:justify-between">
            <p>PulseForge AI Fitness Coach MVP</p>
            <p>Personalized workouts · Nutrition · AI coaching · Progress</p>
          </div>
        </footer>
      </div>
    </main>
  );
}
