export default function HowToUse() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">How To Use CricketArb</h1>
        <p className="text-gray-400">Complete step-by-step guide to make guaranteed profit from cricket betting</p>
      </div>

      {/* Quick Overview */}
      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-emerald-400 mb-3">What Does CricketArb Do?</h2>
        <p className="text-gray-300 leading-relaxed">
          CricketArb monitors live cricket odds from multiple betting sites. When you place a bet before/during a match,
          it watches the odds and alerts you when you can place a <strong className="text-white">second bet on the opposite team</strong> to
          <strong className="text-emerald-400"> guarantee profit regardless of who wins</strong>. This is called <em>hedging</em>.
        </p>
        <div className="mt-4 bg-gray-800/50 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Example:</p>
          <p className="text-gray-300">
            Bet Rs.1000 on India @ 2.50 → India bats well → Australia odds rise to 4.00 →
            <span className="text-emerald-400 font-semibold"> HEDGE ALERT!</span> → Bet Rs.625 on Australia @ 4.00 →
            <span className="text-emerald-400 font-semibold"> Profit Rs.875 no matter who wins!</span>
          </p>
        </div>
      </div>

      {/* Step A: Setup */}
      <Section
        step="A"
        title="First-Time Setup"
        subtitle="One time only — takes 5 minutes"
        color="blue"
      >
        <Step n={1} text="Double-click setup.bat — installs everything automatically" />
        <Step n={2} text="Double-click install-extension.bat — opens Chrome extensions page" />
        <Step n={3} text='In Chrome: Enable "Developer Mode" (top-right toggle) → Click "Load Unpacked" → Select the extension/ folder' />
        <Step n={4} text="Extension icon appears in Chrome toolbar — you're done!" />
        <InfoBox text="You only need to do this once. The extension stays installed in Chrome permanently." />
      </Section>

      {/* Step B: Starting */}
      <Section
        step="B"
        title="Starting CricketArb"
        subtitle="Every time you want to use it"
        color="purple"
      >
        <Step n={1} text="Double-click start.bat — launches all services + opens browser" />
        <Step n={2} text="Login at the dashboard (or register if first time)" />
        <Step n={3} text="Allow browser notifications when prompted (needed for alerts)" />
        <InfoBox text="Use stop.bat to shut everything down when you're done." />
      </Section>

      {/* Step C: Before Match */}
      <Section
        step="C"
        title="Before the Match"
        subtitle="Place your first bet and set up monitoring"
        color="yellow"
      >
        <Step n={1} text="Open your betting app (bet365, dream11, betway, etc.)" />
        <Step n={2} text="Place your first bet on the match (e.g., India to win @ 2.50 for Rs.1000)" />
        <Step n={3} text='Come to CricketArb → Go to "Hedge Monitor" page' />
        <Step n={4} text='Click "+ Record New Bet" → Enter your bet details:' />
        <DetailBox items={[
          'Team A: India, Team B: Australia',
          'Bet on: India',
          'Odds: 2.50',
          'Stake: Rs.1000',
        ]} />
        <Step n={5} text='Click "Start Monitoring"' />
        <Step n={6} text="System shows your breakeven odds (e.g., Australia must exceed 1.67)" />
      </Section>

      {/* Step D: During Match */}
      <Section
        step="D"
        title="During the Live Match"
        subtitle="Extension captures odds automatically"
        color="cyan"
      >
        <Step n={1} text="Open the betting website in Chrome (where live odds are showing)" />
        <Step n={2} text='Click CricketArb extension icon → "Open Capture Panel"' />
        <Step n={3} text="Enter Team A and Team B names" />
        <Step n={4} text='Click "Auto" button → Green dot appears → Extension starts scanning' />
        <Step n={5} text="Extension reads odds from the page every 7 seconds automatically" />
        <Step n={6} text="You can minimize the panel and keep watching the match!" />
        <InfoBox text="The extension ONLY reads odds from the page. It never places bets or interacts with your betting account." />
      </Section>

      {/* Step E: The Alert */}
      <Section
        step="E"
        title="When the Hedge Alert Comes"
        subtitle="This is the moment you've been waiting for!"
        color="emerald"
      >
        <Step n={1} text="India bats well → Australia's odds rise from 1.40 to 1.80" />
        <Step n={2} text="1.80 > 1.67 (your breakeven) → HEDGE ALERT fires!" />
        <Step n={3} text="You hear a double beep sound" />
        <Step n={4} text='Browser notification: "HEDGE NOW! Profit Rs.111"' />
        <Step n={5} text='Hedge Monitor page shows exactly: "Bet Rs.1389 on Australia @ 1.80"' />
      </Section>

      {/* Step F: Lock Profit */}
      <Section
        step="F"
        title="Lock In Your Profit"
        subtitle="Place the hedge bet and you're guaranteed profit"
        color="emerald"
      >
        <Step n={1} text="Open your betting app → Place Rs.1389 on Australia @ 1.80" />
        <Step n={2} text='Click "I Placed the Hedge" in CricketArb' />
        <Step n={3} text="Done! You make Rs.111 profit no matter who wins!" />
        <div className="mt-4 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-sm font-medium text-gray-400 mb-2">Profit Breakdown:</p>
          <div className="space-y-1 text-sm font-mono">
            <p className="text-gray-300">If India wins:     Rs.2500 - Rs.1000 - Rs.1389 = <span className="text-emerald-400 font-bold">+Rs.111</span></p>
            <p className="text-gray-300">If Australia wins:  Rs.2500 - Rs.1000 - Rs.1389 = <span className="text-emerald-400 font-bold">+Rs.111</span></p>
          </div>
        </div>
      </Section>

      {/* Extension Tips */}
      <Section
        step="?"
        title="Chrome Extension Tips"
        subtitle="Getting the best results from auto-capture"
        color="orange"
      >
        <div className="space-y-3 text-sm text-gray-300">
          <TipItem
            title="Works with any betting site"
            text="bet365, betway, dream11, betfair, 1xbet, parimatch, and any other site that shows odds on the page"
          />
          <TipItem
            title="Developer Mode is required"
            text="The extension is not on Chrome Web Store, so it runs in Developer Mode. This is safe — it only reads odds."
          />
          <TipItem
            title="Multiple tabs work"
            text="Open 2-3 different betting sites in separate tabs. The extension scans whichever tab you're viewing."
          />
          <TipItem
            title="Manual fallback"
            text='If auto-capture doesn\'t detect odds on a specific site, use "Select" mode to manually click odds, or type them in.'
          />
          <TipItem
            title="Scan interval"
            text="Default is 7 seconds. Change to 5s for faster updates or 15s if you want less battery usage."
          />
        </div>
      </Section>

      {/* Important Notes */}
      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-yellow-400 mb-3">Important Notes</h2>
        <ul className="space-y-2 text-sm text-gray-300">
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>CricketArb <strong className="text-white">only sends notifications</strong> — it never places bets automatically</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>You always place bets <strong className="text-white">manually</strong> on your betting apps</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>You need the betting website <strong className="text-white">open in Chrome</strong> for the extension to read odds</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>If profit shown is very small (&lt; Rs.50), fees may eat it — wait for a better opportunity</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>Odds change fast during live matches — place hedge bet quickly when alert comes</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 mt-0.5">!</span>
            <span>For best results, have <strong className="text-white">2-3 betting apps</strong> open — different sites offer different odds</span>
          </li>
        </ul>
      </div>

      {/* Pages Guide */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Dashboard Pages Explained</h2>
        <div className="grid gap-3">
          <PageInfo
            name="Dashboard"
            desc="Shows all active arbitrage opportunities in real-time with sound alerts"
          />
          <PageInfo
            name="Hedge Monitor"
            desc="Record your bets here. The system monitors odds and alerts you when to hedge. This is the MAIN feature."
          />
          <PageInfo
            name="Live Matches"
            desc="Shows all live/upcoming cricket matches with odds comparison across bookmakers"
          />
          <PageInfo
            name="Arb History"
            desc="Historical log of all detected arbitrage opportunities"
          />
          <PageInfo
            name="Positions"
            desc="Track your actual bets and hedge positions. Records P&L across all hedged positions."
          />
          <PageInfo
            name="Settings"
            desc="Configure minimum profit %, bookmakers to monitor, notification preferences, Telegram setup"
          />
        </div>
      </div>

      <div className="text-center text-gray-500 text-sm pb-8">
        For detailed technical documentation, see GUIDE.md in the project folder.
      </div>
    </div>
  );
}

function Section({ step, title, subtitle, color, children }: {
  step: string; title: string; subtitle: string; color: string; children: React.ReactNode;
}) {
  const colorMap: Record<string, string> = {
    blue: 'border-blue-500/30 bg-blue-500/5',
    purple: 'border-purple-500/30 bg-purple-500/5',
    yellow: 'border-yellow-500/30 bg-yellow-500/5',
    cyan: 'border-cyan-500/30 bg-cyan-500/5',
    emerald: 'border-emerald-500/30 bg-emerald-500/5',
    orange: 'border-orange-500/30 bg-orange-500/5',
  };
  const stepColorMap: Record<string, string> = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500',
    cyan: 'bg-cyan-500',
    emerald: 'bg-emerald-500',
    orange: 'bg-orange-500',
  };

  return (
    <div className={`border rounded-xl p-6 ${colorMap[color] || colorMap.blue}`}>
      <div className="flex items-center gap-3 mb-1">
        <span className={`${stepColorMap[color] || stepColorMap.blue} text-white text-sm font-bold w-8 h-8 rounded-full flex items-center justify-center`}>
          {step}
        </span>
        <h2 className="text-xl font-semibold text-white">{title}</h2>
      </div>
      <p className="text-gray-400 text-sm mb-4 ml-11">{subtitle}</p>
      <div className="ml-11 space-y-2">
        {children}
      </div>
    </div>
  );
}

function Step({ n, text }: { n: number; text: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="text-gray-500 text-sm font-mono w-5 text-right flex-shrink-0">{n}.</span>
      <p className="text-gray-300 text-sm">{text}</p>
    </div>
  );
}

function DetailBox({ items }: { items: string[] }) {
  return (
    <div className="ml-8 bg-gray-800/50 rounded-lg p-3 border border-gray-700">
      {items.map((item, i) => (
        <p key={i} className="text-gray-400 text-sm font-mono">{item}</p>
      ))}
    </div>
  );
}

function InfoBox({ text }: { text: string }) {
  return (
    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mt-2">
      <p className="text-blue-300 text-sm">{text}</p>
    </div>
  );
}

function TipItem({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <p className="font-medium text-white">{title}</p>
      <p className="text-gray-400">{text}</p>
    </div>
  );
}

function PageInfo({ name, desc }: { name: string; desc: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="text-emerald-400 font-medium text-sm w-32 flex-shrink-0">{name}</span>
      <span className="text-gray-400 text-sm">{desc}</span>
    </div>
  );
}
