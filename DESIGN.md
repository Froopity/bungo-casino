# Big Bungo's Casino - One-Dollar Bet Tracker
## Design Document

---

## Project Overview

A lightweight bet tracking system themed as "Big Bungo's Casino" - a cowboy-western themed platform for friends to make $1 wagers on silly things. The system consists of a Discord bot for creating and managing bets, and a Flask website for viewing bets and leaderboards.

**Key Principles:**
- Lightweight and simple
- Keep things quick and easy
- Minimal JavaScript (prefer raw HTML)
- Straight-faced comedy (absurd but not trying to be funny)
- No authentication system (Discord handles identity)

---

## System Architecture

### Components
1. **Discord Bot** (Python)
   - Handles user registration
   - Creates, resolves, and cancels bets
   - Runs in specific Discord channel with role requirements
   - Runs as separate Docker container

2. **Flask Website** (Python)
   - Read-only view of bets and leaderboard
   - Single-page application with in-page navigation
   - Minimal JavaScript
   - Runs on Raspberry Pi in Docker container

3. **SQLite Database**
   - Shared between bot and website via Docker mount
   - Stores users, bets, and all related data

### Infrastructure
- Hosted on Raspberry Pi
- Both services run in Docker containers
- Shared volume mount for SQLite database
- Low traffic expected (small friend group)

---

## Database Schema

### Users Table
```
users
├── id (INTEGER PRIMARY KEY)
├── discord_user_id (TEXT UNIQUE NOT NULL) - Discord user ID (never exposed publicly)
├── display_name (TEXT UNIQUE NOT NULL) - User's chosen display name
├── registered_at (TIMESTAMP NOT NULL) - When user registered
└── INDEX on discord_user_id
```

**Constraints:**
- Display name: 3-32 characters, alphanumeric + spaces only, no symbols
- Display names must be unique
- Discord user IDs must be unique

### Bets Table
```
bets
├── id (INTEGER PRIMARY KEY) - "ticket number"
├── participant1_id (INTEGER NOT NULL) - Creator of the bet (FOREIGN KEY -> users.id)
├── participant2_id (INTEGER NOT NULL) - Opponent (FOREIGN KEY -> users.id)
├── description (TEXT NOT NULL) - Public bet description (max 280 chars)
├── details (TEXT NULL) - Admin-only additional details (unlimited)
├── state (TEXT NOT NULL) - 'active', 'resolved', 'cancelled'
├── created_at (TIMESTAMP NOT NULL)
├── created_by_discord_id (TEXT NOT NULL) - Discord ID of creator
├── resolved_at (TIMESTAMP NULL)
├── resolved_by_discord_id (TEXT NULL) - Discord ID of resolver
├── winner_id (INTEGER NULL) - FOREIGN KEY -> users.id
├── resolution_notes (TEXT NULL) - Optional notes (max 280 chars)
└── INDEXES on state, created_at, participant1_id, participant2_id
```

**Constraints:**
- Description: max 280 characters
- Details: unlimited (admin-only field)
- Resolution notes: max 280 characters
- State: must be 'active', 'resolved', or 'cancelled'
- participant1_id != participant2_id (no self-betting)

---

## Discord Bot Specifications

### Bot Configuration
- **Framework:** discord.py (or similar common Python Discord library)
- **Channel restriction:** Bot only works in specific channel
- **Role requirement:** Users need specific role to use commands
- **Process:** Runs as separate process from Flask web server

### Commands

#### `/howdy [display_name]`
**Purpose:** Register a new user

**Validations:**
- Display name: 3-32 characters, alphanumeric + spaces only
- Display name must not already be taken
- User must not already be registered

**Responses:**
- Success: [implement normal success response]
- Already registered: "woah there [display_name], ur already all signed up"
- Name taken: "sorry pardner, that name is already done took"
- Invalid format: [implement validation error]

---

#### `/wager @opponent [description]`
**Purpose:** Create a new bet

**Validations:**
- User must be registered
- Opponent must be registered
- Opponent must exist in Discord server
- Cannot bet against yourself
- Description required (max 280 chars)

**Responses:**
- Success: "alrighty your ticket is [bet_id] good luck champ"
- Unregistered creator: "woaah slow down ther cowboy, you gotta say /howdy first"
- Unregistered opponent (with @): "hold on hold on, [username] has to say /howdy to ol' bungo first"
- Unregistered opponent (no @, is Discord member): "hold on hold on, [username] has to say /howdy to ol' bungo first"
- Unregistered opponent (no @, not Discord member): "i ain't never heard o' no [username]"
- Self-betting: "you cant place a wager on urself!"

**Behavior:**
- Bet is immediately active (no acceptance required)
- No notification sent to opponent
- Returns bet ID (ticket number)

---

#### `/resolve [bet_id] [@winner]`
**Purpose:** Resolve a bet by declaring the winner

**Validations:**
- User must be a participant in the bet
- Bet must exist
- Bet must be in 'active' state
- Winner must be one of the two participants
- Winner can be specified by Discord handle or display name

**Responses:**
- Shows confirmation prompt: "r ya sure [winner] wins?" with buttons:
  - "yes"
  - "nevrmind"
- On confirmation: "congrertulatiorns [winner], betrr luck next time [loser]"
- Invalid bet ID: "i ain't know nothin bout that ticket numbr"
- Not a participant: "slow down pardner, you ain't a part of that there wager"
- Already resolved/cancelled: "cmon champ, that wager's long gone by now"
- Invalid winner: "they aint a pard of this, its between [participant1] and [participant2]"

**Behavior:**
- Must be resolved by one of the two participants
- Either participant can declare either person as winner
- Confirmation required before resolution
- First resolution wins (atomic operation to handle concurrency)
- Records who resolved it and when
- Can optionally include resolution notes (max 280 chars)

---

#### `/cancel [bet_id]`
**Purpose:** Cancel an active bet

**Validations:**
- User must be a participant in the bet
- Bet must exist
- Bet must be in 'active' state

**Responses:**
- Shows confirmation prompt: "r ya sure?" with buttons:
  - "yes"
  - "nevrmind"
- On confirmation: "ah well"
- Invalid bet ID: "i ain't know nothin bout that ticket numbr"
- Not a participant: "slow down pardner, you ain't a part of that there wager"
- Already resolved/cancelled: "cmon champ, that wager's long gone by now"

**Behavior:**
- Either participant can cancel
- No reason required
- Confirmation required
- Cancelled bets remain in database but hidden from website
- First cancellation wins (atomic operation to handle concurrency)

---

#### `/leadrbord`
**Purpose:** Link to website leaderboard

**Response:**
- Returns link to website leaderboard page

---

## Website Specifications

### Page Structure
**Single page with two sections:**
1. Bets section (active + resolved)
2. Leaderboard section

**Navigation:** In-page toggle/tabs to switch between Bets and Leaderboard views

**Branding:**
- Title: "Big Bungo's Casino"
- Tagline: "head on in pardner, win urself a prize"
- Inherits existing header and styling from other site pages

---

### Bets Section

#### Active Bets
**Display for each bet:**
- Ticket number (bet ID)
- Participants (both names)
- Description
- Date created (format: "23/12/2025 3:45pm" in Australia/Perth timezone)
- Details icon (coin icon, tooltip on hover - only shown if details exist)

**Ordering:** Creation date descending (newest first)

**Empty state:**
- Show empty table
- Message: "looks like there ain't nothin exciting goin on. care to raise one urself?"

---

#### Resolved Bets
**Display for each bet:**
- All fields from active bets, plus:
- Winner name
- Resolution notes (if present)
- Date resolved

**Ordering:** Resolution date descending (newest first)

**Empty state:**
- Show empty table
- Message: "ain't no bets! you could have the first one tho"

---

#### Filtering & Search

**Filter by Participant:**
- Search bar with autocomplete
- Shows matching participant names as you type (e.g., "da" shows "Dave", "Darren")
- Filters to bets where selected person is either participant
- Applies to both active and resolved bets

**Search by Description:**
- Text input field
- Case-insensitive contains matching
- Searches both active and resolved bets

**Combined Filters:**
- Implementation-dependent based on raw HTML constraints
- See how it plays out during development

---

### Leaderboard Section

**Columns:**
1. Rank
2. Display Name
3. Balance (in dollars)
4. Wins
5. Losses
6. Total Bets

**Calculation:**
- Starting balance: $0
- Win a bet: +$1
- Lose a bet: -$1
- Only shows users who have participated in at least one bet

**Ranking Logic:**
1. Balance (descending)
2. Wins (descending)
3. Total Bets (descending)
4. Registered datetime (ascending - earlier registration ranks higher)

**Empty state:**
- Show empty table
- No message needed

---

## Business Rules

### Bet Lifecycle
1. **Creation:** User creates bet via `/wager` → immediately active
2. **Active:** Bet can be resolved or cancelled by either participant
3. **Resolution:** Either participant declares winner → bet moves to resolved state
4. **Cancellation:** Either participant cancels → bet moves to cancelled state

### Bet States
- **active:** Bet is ongoing, can be resolved or cancelled
- **resolved:** Bet has a winner, cannot be modified (except admin DB edits)
- **cancelled:** Bet was cancelled, hidden from website, cannot be modified

### Participant Roles
- **Participant 1:** Creator of the bet (important for descriptions like "I can jump over that pole")
- **Participant 2:** The opponent
- **Both participants can:**
  - Resolve the bet (declare either person as winner)
  - Cancel the bet

### Financial Tracking
- All bets worth exactly $1
- Win = +$1 to balance
- Lose = -$1 to balance
- Cancelled bets don't affect balance
- Everyone starts at $0

### Administrative Access
- Admin manually edits SQLite database for disputes
- Admin can edit the "details" field for any bet
- No admin commands in Discord bot (too complex)
- Once resolved, bets cannot be unresolved (except via direct DB edit)

---

## Technical Requirements

### Date/Time Handling
- **Storage:** All timestamps in UTC
- **Display:** Convert to Australia/Perth timezone
- **Format:** Australian localization - "23/12/2025 3:45pm"

### Concurrency
- Bet resolution and cancellation must be atomic operations
- First person to confirm wins in concurrent scenarios
- Second person gets appropriate error message

### Data Privacy
- Discord user IDs stored for correlation but never exposed publicly
- Only display names shown on website and in bot responses

### Performance
- Lightweight queries (SQLite on Raspberry Pi)
- Minimal traffic expected (small friend group)
- No heavy JavaScript - keep it raw HTML as much as possible

---

## Deployment

### Docker Setup
**Two containers:**
1. Flask web server (existing, to be modified)
2. Discord bot (new)

**Shared Resources:**
- SQLite database via shared volume mount
- Database location: [TBD - somewhere both containers can access]

**Process Management:**
- Auto-restart handled by Docker lifecycle
- Both services should restart automatically on failure

### Development Phases
1. Database schema creation
2. Discord bot implementation
3. Website modifications
4. Integration testing
5. Deployment to Raspberry Pi

---

## Notes for Implementation

### Details Field
- The "details" field is admin-only and unlimited in length
- Displayed via hover tooltip (coin icon) on website if present
- Only editable via direct database access
- Use case: Adding context or funny commentary that doesn't fit in description

### Display Name Rules
- 3-32 characters
- Alphanumeric and spaces only
- No special characters or symbols
- Cannot be changed after registration
- Must be unique

### Bot Error Messages
All bot messages maintain the cowboy-western theme with intentional misspellings. Be consistent with the voice.

### Website Styling
Website inherits existing branding and styling from other pages on the site. Focus on functionality and data display. Keep JavaScript minimal - prefer server-side rendering and simple HTML/CSS solutions.

---

## Future Considerations
(Not in scope for initial implementation)

- Allow display name changes
- Admin commands in Discord bot
- Editing resolved bets via Discord
- Bet expiration dates
- Bet categories or tags
- Statistics page (most wins, longest winning streak, etc.)
- Integration with payment systems (currently honor system)
