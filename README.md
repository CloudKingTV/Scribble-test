# stickanim

Procedural stick-figure action animation in the style of the classic "stick figure fights the
mouse cursor on a computer desktop" shorts. You write the choreography as a Python script.
The engine handles the rest: rig, physics, effects, sound, and an MP4 output.

**Needs:** Python 3.9+, Pillow, NumPy, and `ffmpeg` on the PATH.

```bash
python3 kimchi.py                      # render the_kimchi_story.mp4 (~75 s): THE KIMCHI STORY
python3 trenches.py                    # render the_trenches.mp4 (~55 s): THE TRENCHES, a memecoin war story
python3 movie.py                       # render stick_vs_cursor.mp4 (~40 s, 1080p30, with sound)
python3 movie.py --still 19.4          # one frame at t=19.4 s -> still.png
python3 movie.py --sheet 5,10.8,19.4   # contact sheet of several moments -> sheet.png
```

The full render takes about 40 seconds on 4 cores, because frames render in parallel.

## THE KIMCHI STORY

`kimchi.py` retells, in the desktop style, the October 2026 saga of the pseudonymous Solana trader
Kimchi. It covers the unverified ~$40M TRUMP claim, Pump.fun signing him as a creative partner,
$KIMCHI hitting ~$40M, the QR-code "Project Kimchi" post that a Pump.fun co-founder reposted, the
~98% crash after the post and repost vanished, the unconfirmed hack claim, Lookonchain's $385K+
early-wallet finding, and the bio scrub and boycott calls. Claims and allegations appear as
unverified or unconfirmed, as the sources report them. Sources are listed on the end card and in
the script.

## THE TRENCHES

"The trenches" is Solana slang for trading brand-new memecoins in their first minutes and hours,
mostly on launchpads like pump.fun. The phrase is a war metaphor, so `trenches.py` stages it as
one. Every beat comes from the research:

| On screen | What it stands for |
|---|---|
| Coins bursting out of the mud with tiny market caps | New token launches: ~313,000 in a single week on Solana launchpads ([Crypto Briefing](https://cryptobriefing.com/solana-trenches-313k-tokens-weekly-high/)) |
| Laser sights, tracers, the coin rocketing out of reach and then crashing | Sniper bots buying in the first block, then dumping on latecomers |
| A loudspeaker on the parapet: "100x. SEND IT!!!" | A KOL (key opinion leader / influencer) shilling a coin |
| FRONT-RUN and BACK-RUN slices of bread crushing the buy | A sandwich (MEV) attack. Bots took an est. $370M–$500M over 16 months, and high-slippage memecoin traders are prime targets ([Solana Compass](https://solanacompass.com/learn/accelerate-25/scale-or-die-at-accelerate-2025-the-state-of-solana-mev), [Helius](https://helius.dev/blog/solana-mev-report)) |
| A hooded dev yanking the LIQUIDITY rug; "DEV SOLD" | A rug pull. A 2026 preprint finds most new memecoins show rug-pull behavior within an hour of launch ([arXiv 2608.20271](https://arxiv.org/abs/2608.20271v1)) |
| Red candles falling like artillery; grey "jeets" fleeing | Dumps, and panic sellers |
| A bonding-curve bar filling; green candles rising into a staircase out of the trench | A pump.fun token "graduating": once its bonding curve sells out it migrates to a DEX pool (PumpSwap). Fewer than 1 in 100 do ([Solana Compass](https://solanacompass.com/news/pumpfun-launched-42000-tokens-in-one-day-fewer-than-2-will-ever-reach-a-dex), [The Block](https://www.theblock.co/post/347360/pump-fun-launches-dex-called-pumpswap-to-instantly-migrate-graduated-tokens)) |
| He makes it over the top... and jumps straight back in for the next launch | The trenches |

All tickers are made up. It's a parody, not financial advice.

## What's in the box

| Module | What it does |
|---|---|
| `rig.py` | 11-joint skeleton, forward kinematics, two-bone IK, and pose ↔ joint-position conversion |
| `actors.py` | `Figure` and `Cursor` timelines: keyframes with easing (incl. overshoot/snap), walk/run cycles with planted feet, ballistic leaps and flips, ragdoll segments, IK reaches, pencil "draw-on", spring follow-through, idle breathing |
| `physics.py` | Verlet ragdoll with joint limits, wall/floor collisions, and pins (so the cursor can grab the head and fling the figure) |
| `scene.py` | Effects (impact bursts, dust, smear frames, speed lines, screen shake, flash, punch-in zoom, hit-stop freeze frames), baking, and parallel rendering into ffmpeg |
| `battlefield.py` | Side-scrolling trench stage: parallax sky with a candlestick-chart skyline, sandbags, revetments, barbed wire, duckboards, artillery flashes, drifting ash |
| `props.py` | Keyframed props: app windows (live chart, social post with QR code, profile bio), supercar, magnifier, rubber stamps, coins, rugs, bread slices, candles, megaphones, speech bubbles, laser sights, floating labels, signs; HUD wallet, banners, typewriter captions, progress bar |
| `desktop.py` | The stage: wallpaper, icons, taskbar, a drawing-app window that opens/closes, tool palette, and cursor icons (arrow, open hand, grab, pencil, eraser) |
| `audio.py` | Synthesised SFX (whooshes, punches, thuds, clicks, pencil scratch, footsteps…) mixed in stereo with room reverb |
| `poses.py` | A pose library: READY, PUNCH, FLY_KICK, UPPERCUT, HERO_LAND, TUCK, … |

## Writing a scene

Authoring is sequential. Each action returns the time it ends, so you can chain them. Physics runs
while you write the script, so you can ask where a body part will be and aim the next beat there.

```python
from stickanim import Desktop, Scene, poses as P

D = Desktop()
sc = Scene(duration=8, backdrop=D)
D.open_window(0.0)
floor = D.CANVAS[3]

hero = sc.figure(700, floor)
cur = sc.cursor(1300, 400)

t = hero.walk(1000, t0=0.5, run=True)                 # planted-foot run
t = hero.leap(0.6, 1150, floor, height=150, t0=t, spin=360,
              poses_=[(0.3, P.TUCK), (0.7, P.TUCK)])  # front flip
hero.key(t + 0.3, pose=P.READY)

t_hit = t + 0.8
hero.key(t_hit, pose=P.PUNCH, ease="snap")
fist = hero.point(t_hit, "r_hand")                    # where will the fist be?
cur.move(t_hit, *fist, t0=t)                          # ...put the cursor there
sc.hit(t_hit, *fist, power=0.8)                       # sound + burst + shake + freeze frame
cur.move(t_hit + 0.4, 1500, 200, rot=400, ease="out") # knocked spinning

sc.render("short.mp4")
```

Angles are in degrees in the figure's own frame: 0 = hanging down, +90 = pointing forward,
180 = up. Each joint is relative to its parent. `spin` rotates the whole body (+ = front flip).
See `rig.py` for the details.
