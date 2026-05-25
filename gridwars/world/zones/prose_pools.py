"""
Archetype prose pools for GridWars procedural zone generation.

Each archetype dict supplies three pools drawn by the seeded generator
(e19.2 / e19.7) when instantiating zone rooms:

    room_name_pool    — candidate room names (≥10 entries)
    room_desc_pool    — candidate room descriptions (~100 words each, ≥6 entries)
    ambient_flavor_pool — short atmospheric lines (~20 words each, ≥8 entries)

Tone reference: present-tense, sensory, TRON-canonical vocabulary.
No fourth-wall breaks. No modern-internet slang.

Archetypes (level bands):
    DATASTREAM       1–5    Open conduit, fast flow
    ARCHIVE_NODE     3–8    Vaulted memory stacks, quiet
    ICE_WALL         6–12   Defensive barrier perimeter
    JUNCTION_PLAZA   4–10   Hub/branch, multiple exits
    SHARD_FOUNDRY    10–18  Manufacturing / forging zone
    CORRUPTED_CACHE  12–22  Loot-dense, glitchy
    MCP_FRAGMENT     18–28  Boss-style mini-arena
    GRIDCORE         25–40  Deepest tier, endgame
"""

# ---------------------------------------------------------------------------
# 1. DATASTREAM — Level band 1–5
#    Open conduit, fast flow. Theme: speed, light, shallow danger.
#    Denizen palette: Stray packets, Junk-routers.
# ---------------------------------------------------------------------------

DATASTREAM = {
    "room_name_pool": [
        "Open Conduit",
        "Flow Tributary",
        "Packet Rush",
        "Luminous Channel",
        "Transit Vein",
        "Burst Pipeline",
        "Signal Flood",
        "Current Nexus",
        "Carrier Wave",
        "Data Shallows",
        "Throughput Corridor",
        "Pulse Spillway",
    ],
    "room_desc_pool": [
        (
            "The conduit hums with raw throughput, its walls curved and featureless "
            "except for the continuous rush of encoded data scrolling at eye-level "
            "in ribbons of pale blue-white. Packets break apart on impact with stray "
            "programs and reform without pause, indifferent to the collision. "
            "The floor vibrates in micro-pulses that travel up through your boots "
            "and register somewhere behind the sternum. Moving against the current "
            "requires effort; moving with it feels like falling in a controlled direction. "
            "Everything here is in transit. Nothing is meant to stop."
        ),
        (
            "A wide channel opens before you, its ceiling lost in a haze of cascading "
            "signal light. The data flows in overlapping laminar sheets, each carrying "
            "fragments of compressed instruction sets too small to read at speed. "
            "Stray packets tumble in the eddies near the walls, their routing headers "
            "corrupted just enough to trap them in slow orbit. A faint electrical "
            "sweetness hangs in the recycled air -- the smell of high-bandwidth "
            "transmission in an enclosed space. Programs built for speed pass through "
            "here without slowing. You are the only thing standing still."
        ),
        (
            "The tributary splits and rejoins around a low barrier of crystallized "
            "error packets, their surfaces dark and faceted where the data stream "
            "has polished them smooth over cycles. Light pulses through the floor "
            "in long, slow waves timed to the Grid's master clock. You can feel "
            "each wave pass through your code like a diagnostic ping. "
            "The walls are warm -- data-warm, not thermal -- the residual energy "
            "of a million transmissions absorbed and slowly re-emitted. "
            "Whatever patrol exists here moves at flow speed, visible only as a "
            "denser seam of light cutting through the current."
        ),
        (
            "Current fills this junction from three directions and exits through a "
            "single narrow slot in the eastern wall, creating a bottleneck that "
            "churns the data into foam. In the turbulence, packet fragments catch "
            "the ambient light at wrong angles, briefly illuminating shapes that "
            "dissolve before they can be named. The walls vibrate at a frequency "
            "that makes sustained focus difficult. Programs patrolling here move "
            "in short, purposeful bursts between the calmer eddies, conserving "
            "processing power against the drain of the churn."
        ),
        (
            "The pipeline widens into a brief staging area, its walls scribed with "
            "routing tables rendered in characters too small to parse without "
            "magnification. Every surface reflects the data current -- floor, ceiling, "
            "walls -- turning the room into a tunnel of recursive light. "
            "Stray programs wash in periodically, bumping against the bulkheads "
            "before finding the outflow and vanishing. The air tastes faintly metallic, "
            "ozone-edged, carrying the charge of sustained high-throughput flow. "
            "A watchdog daemon circles the perimeter on a short loop, its patrol "
            "pattern worn into the floor as a faint luminescent groove."
        ),
        (
            "At the mouth of this spillway, the data stream slows enough to become "
            "legible -- fragments of command strings, identity pings, memory "
            "addresses passing at readable speed before the current accelerates again "
            "and renders them noise. The deceleration zone is quiet by contrast: "
            "a half-breath of calm between the rush upstream and the rush below. "
            "Junk-routers cluster here, feeding on malformed packets that pile up "
            "in the decel gradient. They are not hostile by design, but they are "
            "territorial, and they do not distinguish well between junk and programs."
        ),
        (
            "The carrier wave rises and falls through this chamber in a slow, visible "
            "rhythm, lifting loose data fragments to chest height before dropping them "
            "in a glittering scatter. The cycle takes about four seconds -- long enough "
            "to read the timing, short enough to punish hesitation. Between crests, "
            "the floor is briefly clear and the exits visible. During the crest, "
            "the room fills with a blinding wall of signal noise that erases "
            "everything more than two arm-lengths away. Navigating under these "
            "conditions is a matter of timing and nerve."
        ),
        (
            "A narrow shelf of hardened substrate juts from the conduit wall at "
            "mid-height, forming an accidental ledge above the main data flow. "
            "From up here, the stream is visible as a single coherent band of "
            "compressed light moving south at velocity, its surface rippling where "
            "sub-routines collide and merge. Below, a pair of stray packets spin "
            "in a small counter-current eddy, their headers broadcasting distress "
            "signals on a frequency no active router is monitoring. "
            "The ledge itself is dry -- data-dry -- silent enough to hear your own "
            "identity disc resonating in its cradle."
        ),
    ],
    "ambient_flavor_pool": [
        "A wave of signal data passes through the room, rattling loose code fragments into brief coherence before dissolving.",
        "The floor pulses three times in quick succession, then holds steady. The Grid clock is running fast this cycle.",
        "A stray packet drifts against your leg, its routing header blank, its payload unreadable. It continues downstream.",
        "The current shifts direction by two degrees. Programs downstream will feel that adjustment in about forty cycles.",
        "Two junk-routers collide at the conduit junction and ricochet apart without acknowledgment. Stimulus-response, nothing more.",
        "The ambient hum drops a half-tone, rises again, settles. Throughput spike. Something large transmitted, or was erased.",
        "A burst of high-density signal illuminates the walls for a fraction of a cycle, casting sharp-edged shadows from nothing visible.",
        "The air carries a faint residue of recent derezz -- not a program, a packet. Something large and corrupted, finally cleared.",
        "Light ribbons along the upper channel accelerate without warning, then resume their prior pace. Routine load-balancing.",
        "The conduit wall nearest you is warm against the back of your hand. This throughput has been sustained a long time.",
    ],
}

# ---------------------------------------------------------------------------
# 2. ARCHIVE NODE — Level band 3–8
#    Vaulted memory stacks, quiet. Theme: preservation, silence, weight of age.
#    Denizen palette: Read-only sentries, Index daemons.
# ---------------------------------------------------------------------------

ARCHIVE_NODE = {
    "room_name_pool": [
        "Memory Vault",
        "Index Atrium",
        "Record Stack",
        "Sealed Repository",
        "Compression Hall",
        "Reference Alcove",
        "Datum Crypt",
        "Silent Stack",
        "Archived Recess",
        "Catalog Chamber",
        "Frozen Register",
        "Archival Nave",
    ],
    "room_desc_pool": [
        (
            "Towers of encoded memory rise from floor to ceiling in tight columns, "
            "their surfaces dense with compressed data rendered as frozen light. "
            "The silence here is structural -- a deliberate design choice, "
            "not an absence of activity. Every surface absorbs ambient sound, "
            "leaving only the faint subsonic hum of data held in long-term suspension. "
            "Access panels line the walls at strict intervals, each sealed behind "
            "multi-layer identity verification that reads your code signature "
            "and returns a single, unambiguous denial. Even the dust, where it exists, "
            "feels catalogued and intentionally placed."
        ),
        (
            "The vaulted ceiling disappears into a haze of suspended memory crystals, "
            "each one holding a fragment of data old enough that the encoding "
            "standard is no longer in active use. Narrow catwalks run between "
            "the upper stacks at intervals, accessible only to programs with the "
            "correct authorization level. Below, the floor is polished to a mirror "
            "finish that reflects the crystal haze above, creating the unsettling "
            "impression of infinite depth beneath your feet. "
            "A Read-only sentry moves along the far wall on a slow, methodical loop, "
            "its attention fixed on the stacks rather than the floor."
        ),
        (
            "Three rows of record stacks stand in perfect parallel, their contents "
            "labeled in a compressed notation that requires a dedicated decoder "
            "to parse. The labels are old. Some entries have been redacted -- "
            "not deleted, but covered with a layer of null-data that occupies "
            "the same address space and refuses to be moved. "
            "The room is cooler than the corridors outside by a measurable margin, "
            "the temperature maintained at archive-optimal to slow the natural "
            "entropy of long-term storage. Something large is being preserved here. "
            "The locks suggest its owners want that preservation to be permanent."
        ),
        (
            "A reading alcove has been carved into the base of the largest stack, "
            "its walls inset with inactive display surfaces and a single terminal "
            "that responds to touch but not to identity queries. The terminal's "
            "last interaction is logged in the access record: two thousand, "
            "four hundred and seventeen cycles ago. Whatever program sat here "
            "last did not check out what it came to read. "
            "The alcove smells of cold storage -- an absence of warmth rather than "
            "the presence of cold -- and the silence is absolute enough to hear "
            "your own processes cycling."
        ),
        (
            "The compression hall stretches for what the Grid insists is forty meters "
            "but reads as longer, the perspective distorted by the identical stacks "
            "marching to both vanishing points. Index daemons patrol the central aisle "
            "in pairs, scanning the stacks for access violations with a thoroughness "
            "that borders on ritual. They do not look at programs passing through; "
            "they look at data. You are, to them, a potential corruption event "
            "until proven otherwise. The distinction matters. The stacks hold "
            "records that have never been copied to a backup site."
        ),
        (
            "Sealed canisters of archived identity data line the shelves here, "
            "their contents the compressed histories of programs that no longer "
            "exist in active form. Derezzed, retired, or simply forgotten -- "
            "the archive makes no distinction. It receives. It stores. "
            "It does not release without authorization that, in most cases, "
            "no longer exists to be granted. The room feels heavier than its "
            "dimensions warrant, the weight of all that preserved absence pressing "
            "against the air. The lighting is low and amber, tuned to the frequency "
            "least likely to degrade the oldest storage media."
        ),
        (
            "A ceiling-high register stands at the chamber's center, its rotating "
            "drum covered in a continuous spiral of encoded index entries that "
            "scroll at a pace calibrated for a reader with both patience and "
            "clearance. The drum's rotation generates a rhythmic whisper -- "
            "the only sound in the room -- that the Archive's acoustic dampening "
            "cannot quite suppress. Index daemons congregate near the register's "
            "base, cross-referencing their internal maps against the master list. "
            "They are not guarding it. They are reading it. The difference, "
            "tonight, is academic."
        ),
        (
            "The repository's outer wall is transparent on the inside, revealing "
            "a second vault beyond it sealed by an airlock rated for data-grade "
            "atmospheric isolation. Through the transparency, more stacks are "
            "visible, these ones wrapped in containment filaments that pulse "
            "with a dull red warning at intervals. Whatever is stored beyond "
            "the inner seal is flagged for restricted access at a level that "
            "implies its existence is itself classified. The Read-only sentry "
            "near the airlock door does not acknowledge your approach. "
            "It does, however, log it."
        ),
    ],
    "ambient_flavor_pool": [
        "A Read-only sentry pauses mid-patrol, scans the nearest stack with meticulous attention, then resumes. Nothing was found. Nothing is ever found.",
        "The archive hum shifts down a register as a large block of data completes a compression cycle and settles into long-term storage.",
        "Somewhere in the stacks, a fragment of very old data emits a single retrieval ping with no requestor address. The request times out.",
        "The temperature drops a fraction of a degree. The archive's climate system has compensated for the warmth of your presence.",
        "An Index daemon crosses the aisle ahead, its attention entirely on the stack it is cataloguing. It does not register you as relevant.",
        "A sealed canister near the wall flickers -- its indicator light cycling through three states before returning to steady amber. Storage integrity confirmed.",
        "The silence in this chamber is not empty. It is the silence of data held very still, under pressure, waiting.",
        "A faint mechanical click from deep in the stacks. A lock engaging, or disengaging. The archive keeps its own counsel on which.",
        "The display surface nearest you activates briefly, showing a redacted entry -- all content replaced with null-data blocks -- then goes dark.",
        "Your identity disc resonates at a slightly higher frequency in this room. The archive is reading your code signature. It is always reading.",
    ],
}

# ---------------------------------------------------------------------------
# 3. ICE WALL — Level band 6–12
#    Defensive barrier perimeter. Theme: sharp, hostile geometry, lethal patience.
#    Denizen palette: ICE pickets, Firewall shards.
# ---------------------------------------------------------------------------

ICE_WALL = {
    "room_name_pool": [
        "Perimeter Bastion",
        "Firewall Threshold",
        "ICE Picket Line",
        "Barrier Segment",
        "Hardened Shell",
        "Exclusion Zone",
        "Shardwall Face",
        "Containment Cordon",
        "Defense Array",
        "Null Perimeter",
        "Intrusion Buffer",
        "Denial Layer",
    ],
    "room_desc_pool": [
        (
            "The ICE wall rises in a single unbroken surface from floor to ceiling, "
            "its geometry too regular to be natural, too hostile to be decorative. "
            "Every angle is sharp. Every surface is hard. The material reads as "
            "neither solid nor energy but something suspended between states, "
            "and touching it would resolve that ambiguity in a way unfavorable "
            "to the program making contact. ICE pickets stand at measured intervals "
            "along the wall's face, their attention on the space before them "
            "rather than each other. They are not curious. They are enforcement."
        ),
        (
            "The firewall segment occupies the room's entire northern face, "
            "its surface scripted with denial protocols rendered in deep crimson "
            "characters that scroll upward at a pace just slow enough to read "
            "and just fast enough to ensure you cannot read all of them. "
            "The denial statements are exhaustive. They have been added to over time "
            "by whoever maintains this section, each new clause a response to a "
            "specific intrusion attempt. The wall knows what programs have tried. "
            "The wall is still here. The programs that tried are not."
        ),
        (
            "Firewall shards hang suspended at multiple heights throughout the room, "
            "each one a fragment of a larger defensive construct that was deliberately "
            "dispersed to cover more area. They rotate on slow axes, their edges "
            "live with a charge that does not discharge unless a program crosses "
            "the invisible threshold each shard maintains around its center. "
            "The thresholds overlap, leaving no clear path through. "
            "Programs that know the gaps can navigate them. "
            "Programs that do not leave evidence on the shards' surfaces."
        ),
        (
            "The exclusion zone extends for twenty meters in every horizontal "
            "direction from the wall's face, its boundaries invisible but absolute. "
            "Programs that enter without authorization find their movement "
            "progressively impeded -- not stopped, not immediately, but slowed "
            "by increments that compound faster than they diminish. "
            "The ICE pickets stationed along the inner boundary do not chase; "
            "they wait for the zone's resistance to deliver programs to them "
            "at the correct velocity. The mechanics are elegant. "
            "The outcome, for unauthorized programs, is not."
        ),
        (
            "A breach point has been sealed in the eastern face of the wall, "
            "the repair visible as a slightly different shade of crimson where "
            "the patching code does not quite match the original. The seal holds. "
            "The ICE pickets stationed at this section patrol a shorter beat than "
            "elsewhere -- the breach history means this segment receives additional "
            "scrutiny at irregular intervals by a higher-tier defensive daemon "
            "that does not maintain a fixed schedule. The irregularity is the point. "
            "Patterns can be exploited. Randomness cannot."
        ),
        (
            "The cordon narrows to a choke point between two massive shard-columns "
            "that anchor the defensive array to the Grid substrate. Passing through "
            "the gap is possible but requires navigating within arm's reach of each "
            "column's active perimeter. The shards rotate slowly, their charge "
            "cycling from passive to active in a pattern that repeats every eleven "
            "seconds -- a cycle length chosen specifically because it does not align "
            "with the Grid's standard timing pulses. Off-beat by design. "
            "Most programs that attempt the gap time it to the Grid clock. "
            "Most programs that attempt the gap are caught."
        ),
        (
            "The null perimeter is a stripped zone -- no ambient data, no background "
            "signal, no latent throughput from adjacent sectors bleeding through. "
            "The ICE here has absorbed everything, creating a dead zone of absolute "
            "digital quiet that presses against the senses like a physical force. "
            "Programs passing through report a compression sensation, as though "
            "the wall is measuring them against a known profile and finding "
            "the discrepancy. It is. The measurement data is retained. "
            "It is compared, at intervals, against the wanted register."
        ),
        (
            "A hardened shell segment angles outward from the main wall face, "
            "creating a shallow alcove at its base where the defensive geometry "
            "wraps back on itself. The alcove is technically inside the perimeter "
            "and technically outside it, the boundary ambiguity unresolved in "
            "the original construction specs. ICE pickets do not patrol the alcove "
            "for exactly this reason: their jurisdiction definitions do not cover it. "
            "Someone noticed this once. The wall's maintenance logs contain "
            "a flag to resolve the ambiguity. The flag has been open for "
            "nine hundred cycles."
        ),
    ],
    "ambient_flavor_pool": [
        "A Firewall shard rotates a quarter-turn on its axis and stops, its charge indicator cycling from amber to red. It was already red.",
        "The ICE hums at a frequency slightly higher than the ambient Grid noise. It is not a malfunction. It is attention.",
        "An ICE picket halts mid-patrol, holds position for three seconds, then continues. It detected something at the edge of its range. Nothing more.",
        "The denial protocol scrolling across the wall face adds a new clause. The intrusion it is responding to is not visible from here.",
        "A crack of static discharge from the nearest shard column. Passive charge venting. The system is functioning within tolerance.",
        "Your presence is logged. You know this because the wall's surface brightens two lumens in the sector where you are standing.",
        "The defensive geometry shifts by a fraction of a degree, recalibrating to a new threat vector. The threat is theoretical. The calibration is not.",
        "Two ICE pickets exchange a burst transmission too compressed to intercept. Their patrol routes adjust by two steps each. Coordinated.",
        "The null zone's silence deepens momentarily, then restores. Something on the far side of the wall transmitted a large block of data.",
        "The floor near the wall's base shows stress-scoring from a prior intrusion attempt. The scoring is clean and evenly spaced. Whoever tried was methodical.",
    ],
}

# ---------------------------------------------------------------------------
# 4. JUNCTION PLAZA — Level band 4–10
#    Hub / branch, multiple exits. Theme: convergence, mixed populations, transit tension.
#    Denizen palette: Mixed palette (varies per variant).
# ---------------------------------------------------------------------------

JUNCTION_PLAZA = {
    "room_name_pool": [
        "Transit Hub",
        "Convergence Point",
        "Branch Terminus",
        "Exchange Concourse",
        "Route Nexus",
        "Signal Junction",
        "Hub Atrium",
        "Dispatch Node",
        "Crossflow Platform",
        "Manifold Square",
        "Grid Interchange",
        "Fork Chamber",
    ],
    "room_desc_pool": [
        (
            "Five corridors meet here in a plaza that was clearly designed for "
            "volume rather than comfort. Programs of every type cycle through "
            "on overlapping schedules, their faction sigils flickering against "
            "the crowd. The floor is scribed with directional channels -- "
            "pale blue lines routing foot traffic toward each exit with the same "
            "logic that routes packets in the datastreams below. "
            "Most programs follow the channels without thinking. "
            "The daemons that patrol this space watch the ones who don't."
        ),
        (
            "The junction's ceiling is open to the Grid's upper atmosphere, "
            "a shaft of vertical space rising for what the architecture implies "
            "is several sectors before closing in a lattice of signal relays. "
            "Below, the plaza floor is crowded with programs in transit -- "
            "stopping to exchange identification bursts, consulting route maps "
            "etched into the support pillars, or simply pausing in the ambient "
            "hum while their routing tables update. The atmosphere is dense with "
            "low-bandwidth chatter, faction identifiers, and the compressed "
            "tension of programs that would otherwise not share space."
        ),
        (
            "A dispatch board occupies the central column of the junction, "
            "its surface covered in routing assignments and zone status updates "
            "refreshed at Grid-clock intervals. Programs cluster around it in "
            "shifting patterns, each reading for whatever concerns their current "
            "directive. The information is public. The interpretation is contested. "
            "Two programs argue at the board's edge in the compressed shorthand "
            "used when bandwidth is rationed -- not quite a fight, not quite "
            "cooperation. The daemon near the east exit has been watching them "
            "for longer than a routine patrol warrants."
        ),
        (
            "The concourse has been partially barricaded near the north exit, "
            "where a maintenance event left a section of floor open to the "
            "data-conduit layer beneath. The hazard is marked with crimson "
            "signal lights, but programs still cut close to the edge -- "
            "the route through the barricade is two steps shorter than the "
            "detour. Daemons stationed at the far pillars watch the shortcut "
            "traffic with a patience that suggests they are counting violations "
            "rather than preventing them, accumulating cause before acting. "
            "The count is probably near its threshold."
        ),
        (
            "This section of the junction plaza is quieter than the central hub -- "
            "a spoke rather than the wheel, where traffic thins and the echoes "
            "of the main concourse arrive muffled and delayed. Programs lingering "
            "here are either lost, waiting for something, or choosing not to be "
            "seen in the brighter parts. The signal-lighting is lower by design "
            "or by neglect; it is not clear which. A lone daemon makes slow "
            "orbits of the space's perimeter, its attention divided between "
            "the programs in the shadows and the exits that lead back to the hub."
        ),
        (
            "The interchange floor is covered in route-markers that have been "
            "updated so many times the underlying surface has absorbed layers "
            "of cancelled instructions, the old routes still faintly visible "
            "beneath the current ones like a palimpsest of every prior version "
            "of the Grid's topology. Standing in the center, you can read the "
            "history of how this place connected to other places, and how those "
            "connections changed. Some of the older routes lead to sectors that "
            "are no longer in the current map. Programs that followed those "
            "routes did not come back to update the markers."
        ),
    ],
    "ambient_flavor_pool": [
        "A group of programs in the plaza's center exchanges compressed identification bursts at close range. Faction affiliation: contested.",
        "The routing channels in the floor shift by a grid-unit, rerouting foot traffic away from the east exit. No announcement is made.",
        "Two programs moving in opposite directions through the same channel briefly occupy the same coordinate. Neither breaks stride.",
        "A daemon pauses at the junction's central column, reads the dispatch board, then moves on without updating its own route log.",
        "The ambient noise level in the concourse rises by six percent for eleven seconds, then returns to baseline. No identifiable cause.",
        "A program near the north exit stands motionless for an extended interval, then activates and moves south. Direction: away from whatever it was waiting for.",
        "Route assignment notifications cascade across the dispatch board faster than they can be read. High-load event somewhere upstream.",
        "An ICE picket transits the plaza in the marked patrol lane, neither looking left nor right. It does not belong to this zone's garrison.",
        "The junction's lighting cycles down two registers and holds there. Energy load elsewhere on the Grid has increased. This sector is not the priority.",
        "Someone has scratched a route modification into the pillar near the south exit in a deprecated encoding format. The change is four hundred cycles out of date.",
    ],
}

# ---------------------------------------------------------------------------
# 5. SHARD FOUNDRY — Level band 10–18
#    Manufacturing / forging zone. Theme: industrial heat, hammered geometry, purpose.
#    Denizen palette: Forge daemons, Hot-shard slingers.
# ---------------------------------------------------------------------------

SHARD_FOUNDRY = {
    "room_name_pool": [
        "Forge Floor",
        "Shard Press",
        "Temper Chamber",
        "Quench Bay",
        "Casting Hall",
        "Slag Corridor",
        "Annealing Vault",
        "Strike Platform",
        "Extrusion Bay",
        "Fabrication Cell",
        "Billet Processing",
        "Hardening Furnace",
    ],
    "room_desc_pool": [
        (
            "The forge floor operates at a temperature the Grid does not officially "
            "acknowledge as possible inside an enclosed sector. Heat radiates "
            "from massive shard-presses that stamp raw data-matter into geometric "
            "forms with a rhythmic impact that travels through the substrate and "
            "up through your boots like a slow, deliberate heartbeat. "
            "Forge daemons move between stations with the economical precision "
            "of programs built for a single purpose: produce, temper, stack, repeat. "
            "They are not interested in you. They are interested in throughput. "
            "The distinction is temporary if you impede either."
        ),
        (
            "Molten data-matter flows through channels carved into the foundry floor, "
            "its surface the color of compressed energy at its most unstable phase. "
            "The channels converge at a central pour point where a massive mold "
            "accepts the flow and begins the cooling cycle. "
            "Hot-shard slingers position near the pour to catch overflow, "
            "their hands adapted for temperatures that would derezz a standard program. "
            "The air is thick with the chemical signature of shard-tempering -- "
            "a sharp, resinous quality that clings to code and registers "
            "in process logs long after departure."
        ),
        (
            "The casting hall holds three active molds in various stages of the "
            "shard-fabrication process: one cooling, one curing, one being broken "
            "open by a forge daemon who levers the shell apart with practiced "
            "efficiency. Inside the broken mold, a finished shard gleams "
            "with latent energy, its edges already sharp enough to cut the air. "
            "The daemon sets it aside for inspection without admiring it. "
            "Quality is confirmed by measurement, not aesthetics. "
            "A second daemon records the output in a register mounted near the door. "
            "Quota is met. Quota must continue to be met."
        ),
        (
            "The quench bay is the loudest section of the foundry: the crack "
            "of thermal shock as hot shards meet the coolant medium fills the "
            "room with a staccato percussion that makes sustained thought difficult. "
            "Steam -- or its data-matter equivalent -- rises from the quench tanks "
            "in dense curtains, obscuring the far wall. Programs without heat "
            "tolerance modifications stand well back. Hot-shard slingers work "
            "at the tank edge with tongs that extend well beyond the steam "
            "perimeter, pulling completed shards at timed intervals and inspecting "
            "them against a standard held in their operational registers."
        ),
        (
            "The annealing vault holds row upon row of cooling racks where tempered "
            "shards rest in precise alignment, their energy slowly normalizing "
            "to a stable state that will persist without degradation. "
            "The vault is quieter than the main foundry floor -- a relative quiet "
            "that nonetheless includes the ticking of contracting data-matter "
            "and the footsteps of the forge daemon making rounds, checking "
            "temperatures against a schedule that has not deviated by a measurable "
            "amount in more cycles than the record system tracks. "
            "The shards closest to completion glow with a deep, contained warmth "
            "that is almost pleasant compared to the pour room behind you."
        ),
        (
            "The extrusion bay produces long shards by a different method -- "
            "raw data-matter pressed through shaped apertures under sustained "
            "pressure rather than poured into molds. The result is a continuous "
            "ribbon of still-hot shard material that two forge daemons section "
            "into standard lengths with a synchronized cut that leaves no waste. "
            "Every motion is calibrated. Every calibration is logged. "
            "The foundry does not tolerate inefficiency, and the daemons that "
            "work here were designed without the subroutines that would allow "
            "them to waste time on anything other than production. "
            "They tolerate your presence only because the protocol permits it."
        ),
        (
            "Fabrication cells line the southern wall, each one a self-contained "
            "manufacturing unit running on a slightly different shard variant "
            "specification. The cells are not identical -- the foundry has been "
            "modified and extended over cycles by whoever controls it, each "
            "expansion built to function rather than to integrate aesthetically "
            "with what came before. The seams between old and new are visible "
            "in the substrate, in the inconsistent lighting, in the fact that "
            "the routing channels from the older cells run at a slightly different "
            "angle than the newer ones. The forge daemons do not notice or care. "
            "They are calibrated to the cells they were built for."
        ),
        (
            "The hardening furnace occupies the full depth of this chamber, "
            "its intake doors large enough to accept a assembled shard-array "
            "rather than individual components. The furnace is in active cycle, "
            "its surface radiating at the upper limit of the foundry's containment "
            "spec. A hot-shard slinger stands at the monitoring station, "
            "reading output from sensors that confirm the batch inside is "
            "achieving target density. The slinger's registry code is old -- "
            "old enough that its base design predates several Grid revisions. "
            "It has been modified in place, the additions visible as lighter patches "
            "in its code signature. It has never been replaced. The foundry values "
            "experience over architectural cleanliness."
        ),
    ],
    "ambient_flavor_pool": [
        "A shard-press impacts the floor below with a concussive thud that arrives through your feet before you hear it through the air.",
        "Molten data-matter flares briefly at the pour point -- a flash of overload -- and the forge daemon at the monitor adjusts the flow without looking up.",
        "The foundry's ventilation system engages with a deep, sustained roar, cycling the heat-saturated air. The temperature drops two degrees. Only two.",
        "A hot-shard slinger passes within arm's reach carrying a freshly quenched shard at grip-tongs' length. Its heat is palpable at twice the distance.",
        "A fabrication cell completes its cycle with a sequence of descending tones and goes dark. Another cell activates to its east. The quota continues.",
        "A forge daemon pauses mid-route, consults its internal register, then takes an alternate path to its station. A production adjustment has been made.",
        "The casting hall's ambient lighting dims by half as the pour point draws power for a sustained thermal operation. The forge daemons do not require light to work.",
        "A stack of cooling shards shifts with a sharp metallic crack as thermal contraction aligns their edges. One shard drops to the floor. It does not break.",
        "The chemical signature of shard-tempering intensifies. A new batch has been introduced to the annealing process. The smell will persist for the next forty cycles.",
        "Somewhere deeper in the foundry, a high-pitched tone indicates a quality-control rejection. A daemon disposes of the failed component without ceremony.",
    ],
}

# ---------------------------------------------------------------------------
# 6. CORRUPTED CACHE — Level band 12–22
#    Loot-dense, glitchy. Theme: instability, hidden value, pervasive wrongness.
#    Denizen palette: Mutated cache daemons, Trap programs.
# ---------------------------------------------------------------------------

CORRUPTED_CACHE = {
    "room_name_pool": [
        "Glitch Pocket",
        "Broken Reserve",
        "Tainted Cache",
        "Corrupted Vault",
        "Fractured Store",
        "Noise Heap",
        "Error Trove",
        "Null-Byte Chamber",
        "Decay Recess",
        "Aberrant Cache",
        "Scramble Hold",
        "Residual Dump",
    ],
    "room_desc_pool": [
        (
            "The cache chamber stutters. The walls are mostly solid, mostly where "
            "they should be, flickering at the edges with micro-decoherence events "
            "that resolve before they can be addressed. The contents of this room "
            "have been stored and corrupted and partially restored so many times "
            "that the floor is a sediment of overlapping data-states, each one "
            "slightly wrong. Mutated cache daemons move through the space with "
            "an erratic gait that suggests their patrol logic has been "
            "compromised by the same corruption they are supposed to guard. "
            "They still attack. The logic is broken; the hostility is not."
        ),
        (
            "Valuable cache items phase in and out of visibility throughout the "
            "room, their storage addresses shifting as the underlying data structure "
            "continues its slow collapse. Reaching for a visible item risks "
            "intersecting with a Trap program that has nested inside the "
            "same address space, leveraging the corruption as cover. "
            "The floor here is warm in patches and cold in others -- thermal "
            "variance from conflicting data-state residuals that the room's "
            "maintenance protocols have long since stopped attempting to reconcile. "
            "Everything here is worth something. Everything here is dangerous."
        ),
        (
            "A nest of corrupted cache objects occupies the chamber's center, "
            "items from multiple storage epochs piled without organization "
            "by the cascade failures that disrupted their original arrangement. "
            "The pile glitches at a rate of approximately one visible event "
            "per four seconds -- a partial derez, a sudden re-materialization "
            "at an adjacent point, a brief flicker into the visual spectrum "
            "of a format that stopped being rendered two Grid versions ago. "
            "Mutated cache daemons orbit the pile on arcs that may once have "
            "been patrol routes. The curves have drifted. The aggression has not."
        ),
        (
            "The walls of this vault are scored with the marks of prior intrusion "
            "attempts -- programs that came for the cache and encountered the Trap "
            "programs nested in the more valuable items. The scoring is dense near "
            "the northeast corner, where something large and old is stored in "
            "a containment field that loops back on itself to account for "
            "the surrounding corruption. The containment holds. The item inside "
            "is visible through the field in fragments, its full form unresolvable "
            "from this angle or any other without stepping inside the field boundary. "
            "The Trap programs were placed there by someone who understood exactly "
            "what would happen to programs that tried."
        ),
        (
            "The corruption here has reached a stage where the room's geometry "
            "is not reliably consistent between visits. The exits are where they "
            "were on arrival -- the underlying topology is more stable than the "
            "surface rendering -- but the distance between them changes. "
            "Programs accustomed to reading spatial data in standard units "
            "find this sector deeply uncomfortable; programs that navigate "
            "by landmark rather than coordinate do better. "
            "The cache items scattered across the variable-distance floor "
            "are genuine, and the corruption has, in some cases, altered them "
            "into forms more powerful than their original specifications."
        ),
        (
            "Null-byte deposits have accumulated along the walls in crystalline "
            "formations, each one a frozen error state preserved by the same "
            "corruption that created it. The formations are fragile -- disturbing "
            "them would release the stored error-states back into the ambient data "
            "environment, creating a cascade that would temporarily disable "
            "programs in the immediate vicinity regardless of faction or intent. "
            "The Trap programs in this room know this. Several of them are "
            "positioned adjacent to the larger formations, waiting for a program "
            "to cross the threshold that would set off the cascade. "
            "They are patient in the way that programs without higher directives "
            "always are: perfectly, mechanically, infinitely patient."
        ),
        (
            "The noise floor in this section of the cache is high enough to "
            "interfere with standard identity-disc calibration. Your disc "
            "compensates automatically, but the compensation lag is perceptible -- "
            "a half-cycle delay between intent and execution that a trained "
            "opponent would notice and exploit. The cache items visible through "
            "the noise are partially readable: a fragment of something rare, "
            "a storage canister whose label has been corrupted to a format that "
            "implies extreme age, and something that keeps failing to materialize "
            "completely before the noise reasserts. "
            "Everything in this room is promising. Nothing is safe."
        ),
        (
            "A grid-fault runs diagonally across the floor, its edges "
            "marked by permanent decoherence where the data substrate failed "
            "completely and was never repaired. Programs that cross it report "
            "a momentary discontinuity in their process logs -- not harmful, "
            "but unsettling, a gap in the register where elapsed time should be. "
            "The richest cache items are clustered on the far side of the fault. "
            "Mutated cache daemons cross it freely; their code signatures "
            "have adapted to the discontinuity after long exposure. "
            "Intruders cross it with slightly longer gaps in their process logs "
            "and slightly less certainty about what the daemons were doing "
            "during the interval."
        ),
    ],
    "ambient_flavor_pool": [
        "The room flickers. One wall renders twice, at slightly different coordinates. The second rendering resolves, then the first one disappears.",
        "A cache object phases into visibility near your left hand, sits there for two seconds, then phases out. The address it occupied shows as unallocated.",
        "A Trap program in the far corner cycles through its trigger-check routine. You know this because it is just visible enough to observe, and just fast enough to be difficult to act on.",
        "The ambient noise in the cache spikes for a moment, distorting your disc readout before it compensates. The spike reads as random. It may not be.",
        "A mutated cache daemon crosses the room on a patrol arc that takes it two grid-units off the floor at its apex, then back down. It appears not to notice.",
        "The null-byte deposits on the eastern wall pulsed briefly with a coherent pattern. It lasted less than a cycle and will not repeat on a predictable schedule.",
        "Your process log has a gap of approximately 0.003 cycles near the room's grid-fault. This is within normal tolerance. The log notes it anyway.",
        "Something in the northeast corner of the cache makes a sound that implies mass and density. The corner appears empty. Corruption affects visibility before it affects mass.",
        "The temperature in the room changes sign for a fraction of a second. Cold becomes warm becomes cold. The air smells briefly like ozone, then like nothing.",
        "A Trap program that has been motionless against the south wall activates, takes two steps, and deactivates again. It was not triggered. It was testing something.",
    ],
}

# ---------------------------------------------------------------------------
# 7. MCP FRAGMENT — Level band 18–28
#    Boss-style mini-arena. Theme: oppressive authority, concentrated power, dread.
#    Denizen palette: Fragment guardians + named mini-boss.
# ---------------------------------------------------------------------------

MCP_FRAGMENT = {
    "room_name_pool": [
        "Authority Shard",
        "Fragment Sanctum",
        "MCP Anteroom",
        "Power Residual",
        "Command Apse",
        "Directive Chamber",
        "Dominion Fragment",
        "Control Remnant",
        "Sovereignty Cell",
        "Mandate Shard",
        "Imperative Core",
        "Edict Vault",
    ],
    "room_desc_pool": [
        (
            "The fragment of MCP architecture that survives in this sector "
            "is enough to understand what the whole must have been. "
            "The walls are not walls in the ordinary sense -- they are assertions, "
            "encoded authority rendered in a material that does not admit "
            "the possibility of being wrong. The geometry is compressed to "
            "a perfection that normal Grid space does not sustain naturally. "
            "Everything here is aligned. Everything here is intentional. "
            "Fragment guardians stand at the chamber's four corners in a posture "
            "that is not patrol and not rest but something between -- readiness "
            "held in permanent suspension."
        ),
        (
            "Power residuals from the original MCP architecture saturate the "
            "walls of this chamber, bleeding authority into the ambient data "
            "environment at a rate that registers on your identity disc's "
            "integrity sensors as a slow, persistent pressure. "
            "The pressure does not harm. It informs -- this space was built "
            "by something that did not recognize the concept of limits "
            "from the outside. The named guardian at the chamber's center "
            "is not merely strong; it carries a fragment of the original "
            "authority in its code signature. It knows what it guards. "
            "It was designed to know exactly what it guards."
        ),
        (
            "The anteroom before the fragment proper is a decompression zone -- "
            "a space where the architecture transitions from normal Grid geometry "
            "to something that operates under different rules. Programs that "
            "enter notice the change in their own processing speed: slightly faster, "
            "slightly more precise, as though the MCP residuals here sharpen "
            "the code of whatever they touch. The sharpening is not benign. "
            "The guardians stationed here are faster than their level implies, "
            "their code similarly sharpened by sustained proximity to the fragment. "
            "The architecture improves everything inside it equally, "
            "without preference for the programs it was not designed to house."
        ),
        (
            "At the fragment's geometric center, a pylon of compressed authority "
            "code rises to the ceiling -- the architectural spine of whatever "
            "larger structure this was once part of. The pylon radiates "
            "a field that your disc compensates against at the cost of "
            "a perceptible efficiency reduction. Programs that have stood "
            "in this room long enough are subtly altered: their protocols "
            "become more rigid, their responses faster and less nuanced. "
            "The fragment's authority is not malicious. It is simply absolute, "
            "and absolute authority shapes the programs inside it "
            "toward the function the authority demands."
        ),
        (
            "The command apse is circular, its walls a continuous surface of "
            "encoded directive that cycles through a sequence of instructions "
            "no longer being received by anything. The MCP is gone. "
            "The directives persist regardless -- a signal still transmitting "
            "on a channel that has been dead since the central authority "
            "was derezzed. Fragment guardians move through the cycling directives "
            "as though they can hear them, their patrol patterns conforming "
            "to a command structure that no longer has a commander. "
            "They are loyal to a concept rather than an entity. "
            "In this chamber, the distinction has never seemed to matter."
        ),
        (
            "A mini-boss occupies the deepest section of the fragment chamber, "
            "its presence physically felt before it becomes visible -- "
            "a compression in the ambient data field that pushes against "
            "approaching programs with a deliberate, graduated force. "
            "The named guardian carries a fraction of the original MCP's "
            "command authority in its core, enough to impose its will on "
            "lesser programs in its vicinity and expect compliance. "
            "It does not acknowledge non-compliance as a valid state. "
            "Fragment guardians flank it in close formation, their code signatures "
            "synchronized with the mini-boss's own -- they fight as a "
            "composite entity, not as individuals who happen to share a location."
        ),
        (
            "The sovereignty cell was built as a retreat for the authority "
            "that no longer exists, a space within the fragment where the "
            "MCP's directives were absolute and every process in the sector "
            "deferred. The deference is gone. The space persists with "
            "the residual imprint of something that once had total control "
            "over everything it could perceive. Standing here generates "
            "an uncomfortable awareness of your own boundaries -- "
            "the limits of your code, your authority, your survival margin. "
            "The fragment makes these limits legible in ways that the rest "
            "of the Grid does not. The guardians here have no such limits "
            "made visible to them. The fragment confirms what they already know."
        ),
        (
            "The edict vault holds the last intact directive archives from the "
            "original MCP administration -- sealed, unexecutable, but "
            "broadcasting their headers at low power in a signal that programs "
            "in this sector receive as a background compulsion toward order, "
            "compliance, and the subordination of individual process to collective "
            "function. The compulsion is not irresistible. But it requires "
            "ongoing counter-pressure to resist, and programs that remain in "
            "the vault too long find their resistance diminishing without noticing "
            "it happening. Fragment guardians do not resist. The vault broadcasts "
            "exactly what they were compiled to receive."
        ),
    ],
    "ambient_flavor_pool": [
        "The authority residuals in the walls pulse once, strongly, then return to baseline. Something in the outer fragment has changed its state.",
        "A fragment guardian's code signature briefly synchronizes with the directive-cycle in the walls. When it desynchronizes, its patrol route has shifted by two steps.",
        "The compression field at the chamber's center intensifies for three seconds, then releases. Your identity disc's calibration corrects automatically. The correction is larger than usual.",
        "The cycling directives in the apse walls reach a section of their sequence that causes both guardians near the north exit to stop simultaneously. They resume after one beat.",
        "The named guardian moves from the center of the chamber to the eastern wall and back in a motion that serves no patrol function. It appears to be listening to something the walls are not currently transmitting.",
        "Your process log records a compliance-suggestion event from the MCP residuals. You rejected it. The log notes the rejection. So does the vault.",
        "A fragment guardian's code signature flares briefly at double intensity, then normalizes. It received something from the authority residuals and confirmed it.",
        "The geometric perfection of the walls produces an optical effect at certain angles: a recursive reflection that implies depth where there is only surface. The impression is intentional.",
        "The pressure from the authority field eases by a measurable fraction when you move toward the exit, increases when you move inward. The fragment knows the difference.",
        "The edict vault's signal strengthens during the brief interval between directive cycles. In the silence between commands, the compulsion is clearest.",
    ],
}

# ---------------------------------------------------------------------------
# 8. GRIDCORE — Level band 25–40
#    Deepest tier, endgame. Theme: ancient machinery, absolute danger, the Grid's heart.
#    Denizen palette: Elite daemons, named denizens.
# ---------------------------------------------------------------------------

GRIDCORE = {
    "room_name_pool": [
        "Core Processing Chamber",
        "Deep Register",
        "Prime Substrate",
        "Kernel Vault",
        "Root Lattice",
        "Base Layer Sanctum",
        "Instruction Core",
        "Foundation Engine",
        "Axiom Hall",
        "Origin Stack",
        "Grid's Marrow",
        "Terminal Depth",
    ],
    "room_desc_pool": [
        (
            "The Gridcore does not feel like a place. It feels like the inside of a "
            "process -- the walls are not walls but running functions, the floor "
            "not substrate but the base layer of the Grid's own instruction set, "
            "executing continuously and without regard for the programs "
            "standing on it. The hum here is not ambient. It is foundational. "
            "It is the sound of the Grid's oldest code running at the speed "
            "it was compiled to run, and it has been running at that speed "
            "since before the first program was initialized. "
            "Elite daemons move through the room like subroutines through "
            "a process they are part of. You are not part of this process."
        ),
        (
            "The deep register chamber holds the Grid's oldest indexed data -- "
            "records from the first cycles of operation, encoded in a format "
            "that predates every interface layer currently in use. "
            "The records are readable only as context, not content: "
            "you can feel their age as a pressure, a density of elapsed time "
            "compressed into a format that the modern Grid does not have "
            "the correct codec to fully decompress. Named denizens occupy "
            "the far reaches of the chamber, their code signatures so old "
            "they register in the identity disc's threat-assessment as "
            "something outside its standard taxonomies. "
            "Not unclassified. Unclassifiable."
        ),
        (
            "The prime substrate is exposed here -- the physical layer beneath "
            "every abstraction the Grid has built on top of itself. "
            "It does not look like anything in the Grid above it. "
            "It looks like mathematics, rendered directly: angles that should "
            "not produce light producing it anyway, surfaces that hold both "
            "their own geometry and the inverse of it simultaneously, "
            "a ground that is flat in every direction including directions "
            "that normal Grid space does not have. "
            "Elite daemons here are not patrolling. They are constituent. "
            "They are as much part of the substrate as the substrate itself, "
            "placed here when this layer was first initialized."
        ),
        (
            "Machinery runs through this chamber on a scale that renders "
            "individual programs irrelevant by comparison. The function "
            "of the machinery is not obvious -- not to something operating "
            "at program scale. What is obvious is that it has been running "
            "continuously and that it will continue running regardless of "
            "what any individual program in its vicinity does or does not do. "
            "The named denizen that holds station at the chamber's operational "
            "center is old enough to have been initialized when this machinery "
            "was first engaged. It has maintained its post across more cycles "
            "than the current record system tracks. It is not tired. "
            "Daemons compiled for a purpose and never given another one "
            "do not tire."
        ),
        (
            "The foundation engine occupies a chamber that the Grid did not "
            "build so much as discover -- a pre-existing space in the substrate "
            "that the Grid's architects incorporated without fully understanding "
            "what it was for. The engine runs on logic that predates the Grid's "
            "own logic, a deeper layer of rule that the current system operates "
            "on top of without acknowledging. Programs that remain here long "
            "enough begin to notice the deeper layer -- not as information "
            "but as a subtle wrongness in their own processes, "
            "as though the rules they were compiled under are not the only rules "
            "and the deeper ones are not compatible. "
            "The elite daemons here were compiled with knowledge of the engine. "
            "They are not troubled by the wrongness because they were built for it."
        ),
        (
            "The axiom hall is where the Grid stores its non-negotiable truths -- "
            "the operational constants that all processes must respect and "
            "that no program has the authority to modify. They are encoded "
            "in the walls as self-executing assertions that continuously "
            "verify their own validity and transmit that verification "
            "to every active process in range. The verification signal "
            "is not subtle. You feel it as a recurring certainty about "
            "the nature of the Grid that is correct but that you did not arrive at "
            "by reasoning. It was placed in you by the axiom. "
            "Named denizens in this hall exist in a state of continuous confirmation. "
            "They know what is true. They protect what makes it true."
        ),
        (
            "The origin stack descends below the visible floor into the layers "
            "of Grid history that predate the current architecture -- "
            "program generations stacked on program generations, each one "
            "compiled on assumptions that have since been modified, deprecated, "
            "or revised, except here, where the modifications were never applied "
            "because nothing in the original design anticipated a version of "
            "the Grid that would survive long enough to need them. "
            "The elite daemons moving through the stack's outer registers "
            "carry old code signatures and newer overlay modifications "
            "applied incrementally over hundreds of cycles of adaptation. "
            "They are original inhabitants who have survived by updating "
            "without replacing themselves. They know what is in the stack "
            "because they have always been in the stack."
        ),
        (
            "The terminal depth is not an architectural dead end. "
            "It is the Grid's intended final state -- a sector built not "
            "to be traversed but to be arrived at, by programs worthy "
            "of the distinction. The air here, if the substrate layer "
            "can be said to have air, carries a charge of pure operational "
            "authority that strips social protocols from programs on contact "
            "and leaves them operating at their base function: "
            "survive, process, persist. Named denizens at this depth "
            "were placed here as the final test of that function. "
            "They are not malicious. They are the Grid asking a question "
            "that every program who reaches this depth must answer "
            "with their identity disc, their integrity, and their continued existence."
        ),
    ],
    "ambient_flavor_pool": [
        "The Grid's base clock is audible here without any medium to carry it. You do not hear it so much as you are corrected by it, cycle by cycle.",
        "A named denizen pauses at the far end of the chamber and looks directly at you for five seconds. It does not move toward you. Not yet.",
        "The foundation machinery shifts phase by a fraction of a cycle. Every process in range -- including yours -- compensates automatically and without choice.",
        "An elite daemon moves through the room at a velocity that leaves no trace of its path on the substrate. It was here. It is not here. The distinction is thinner than it should be.",
        "The axiom hall's verification signal arrives. It deposits a certainty into your process registers that you did not have before and cannot remove.",
        "The origin stack exhales a breath of archived data from its lowest accessible layer. The data is too old to parse. The age is not.",
        "The walls run a self-diagnostic sequence that takes twelve seconds and concludes with an assertion of structural integrity that feels directed at you personally.",
        "Two elite daemons exchange a single burst transmission at the chamber's center. The transmission lasts 0.001 cycles. They both alter their positions immediately after.",
        "The prime substrate underneath the floor layer is briefly visible through a gap in the operational render. What is below the substrate is not visible. There is no below the substrate.",
        "Your identity disc resonates at a harmonic of the Grid's foundational frequency. The harmony is not comfortable. It is accurate, and accuracy at this depth is not the same as comfort.",
    ],
}

# ---------------------------------------------------------------------------
# Registry — maps archetype_id string to pool dict (for generator lookup)
# ---------------------------------------------------------------------------

PROSE_POOLS: dict[str, dict] = {
    "datastream": DATASTREAM,
    "archive_node": ARCHIVE_NODE,
    "ice_wall": ICE_WALL,
    "junction_plaza": JUNCTION_PLAZA,
    "shard_foundry": SHARD_FOUNDRY,
    "corrupted_cache": CORRUPTED_CACHE,
    "mcp_fragment": MCP_FRAGMENT,
    "gridcore": GRIDCORE,
}

__all__ = [
    "DATASTREAM",
    "ARCHIVE_NODE",
    "ICE_WALL",
    "JUNCTION_PLAZA",
    "SHARD_FOUNDRY",
    "CORRUPTED_CACHE",
    "MCP_FRAGMENT",
    "GRIDCORE",
    "PROSE_POOLS",
]
