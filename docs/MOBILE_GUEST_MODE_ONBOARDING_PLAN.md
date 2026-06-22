# Mobile Guest Mode Onboarding Plan

## Why we are considering this

The current mobile acquisition funnel shows the biggest drop before users fully enter the auth flow. Many users install and open the app, but do not commit to phone-based login or registration immediately.

The likely product issue is early friction:

- fresh installs first see a welcome/marketing screen
- valuable app experiences are mostly behind auth
- users are asked for phone verification before they have felt enough product value

This suggests we should let new users experience some real utility before requiring account creation.

## Current conclusion

We should revisit onboarding later with a **guest mode** approach instead of forcing login first.

The key idea:

- let guests enter the app and explore useful chart-based features
- keep expensive / account-linked / synchronized features behind login
- store guest-created birth charts only on the device until the user signs in

This is not being implemented right now, but this is the direction we agreed is worth pursuing.

## Product direction we agreed on

### Guest users should be able to

- enter the app without login/register
- reach Home and browse the app
- open menu and understand what the app offers
- create a birth chart locally on the device
- view charts and dashas
- explore chart-oriented utility without server-side account persistence

### Guest users should not be able to

- use AI chat
- run heavy personalized analyses like partnership, career, health, wealth, etc.
- buy or use credits
- sync charts across devices
- permanently save charts to backend
- access account-only notification or history features

### Guest chart behavior

- birth chart data stays in local mobile storage only
- it is not linked to a backend user
- if the app is deleted, guest charts are lost
- after login/register, we should offer to import the local chart(s) into the new account

## Why this looks promising

This approach matches the funnel behavior better:

- users can get value first
- auth is requested only when they want something deeper
- phone verification becomes a higher-intent action
- this should reduce top-of-funnel abandonment from paid and organic acquisition

## Recommended technical approach

### 1. Keep guest charts local first

Preferred approach:

- do **not** create backend guest users
- do **not** persist guest charts in server DB initially
- store guest birth charts in mobile local storage only

This is the safest first version because it avoids:

- fake user/account complexity
- guest-to-user DB migration complexity at creation time
- backend cleanup concerns for abandoned guest records

### 2. Use auth walls at feature boundaries

When a guest attempts to use gated features like:

- chat
- partnership analysis
- career analysis
- health analysis
- wealth analysis
- credits / purchases

show a clear login/register prompt:

- explain what unlocks after sign-in
- explain that their local chart can be saved to the account after sign-in

### 3. Import guest chart(s) after login

After successful login/register:

- detect local guest chart(s)
- offer “Save this chart to your account”
- create the real backend birth chart rows at that point

This keeps server persistence aligned with real user identity.

## Chart computation note

This needs a dedicated design review before implementation.

Two broad options:

### Option A: guest chart uses stateless backend calculation

- mobile sends birth details to calculation endpoints
- backend returns computed chart data without requiring a saved backend chart row
- chart is cached locally on device

Pros:

- keeps chart accuracy consistent with the current backend
- avoids rebuilding core astrology calculation logic in mobile

Cons:

- guest users can still consume backend compute
- needs rate limits / abuse protection

### Option B: local-only computation

- app computes charts locally on device

Pros:

- no backend cost for guest users

Cons:

- likely too large/risky for current architecture
- would duplicate trusted backend logic

### Current preference

If we do guest mode, current preference is:

- **local chart identity + local storage**
- but chart calculation can still rely on **stateless backend calculation**

That gives a better balance of speed, safety, and parity.

## Important guardrails

If guest mode is implemented, we should protect backend cost and abuse:

- no guest AI chat
- no guest heavy analysis reports
- no unlimited expensive chart recalculations
- add sensible throttling/rate limits for guest stateless chart calculation if needed

## Suggested rollout phases

### Phase 1

- reduce forced splash delay
- keep current onboarding otherwise

Status:

- splash minimum already reduced from `3000 ms` to `1200 ms`

### Phase 2

- let guest users enter the app and reach Home without auth
- keep existing welcome context if still useful, but do not block core exploration

### Phase 3

- add local guest birth chart creation and selection
- support charts + dashas in guest mode

### Phase 4

- add auth walls for chat / analyses / credits / account-only features

### Phase 5

- add guest-chart import into account after login/register

## Open questions for later

These need to be answered before implementation:

1. Should guest users be able to create one local chart or multiple?
2. Which chart views are allowed for guests?
3. Should transit views also be allowed for guests?
4. Should guests be able to see only charts/dashas, or also some light explanatory text?
5. Which exact moment should trigger the auth wall?
6. Should guest chart calculations be rate-limited per installation ID?
7. Should welcome screen remain, but become much lighter, once guest mode exists?

## Summary

The agreed future direction is:

- allow value before auth
- let guests create and explore local-only birth charts
- keep expensive and account-bound features behind login
- save/import charts to backend only after the user authenticates

This is likely a stronger answer to top-of-funnel drop-off than simply adjusting copy on the current auth gate.
