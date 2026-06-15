# VM Recovery Acceleration Plan

## Goal

Make replacement VMs in the production MIG become useful much faster.

Success means:
- a recreated VM reaches backend health quickly
- recovery does not depend on a full mutable deploy path
- startup is predictable and small
- VM replacement is safe even during an incident

---

## Current Reality

Today a replacement VM effectively depends on the same machinery used for a deploy:

1. startup metadata / startup script must succeed
2. repo and deploy key must appear on disk
3. `deploy.sh` runs
4. Secret Manager sync runs
5. Ops Agent install/apply runs
6. backend venv / pip setup may run
7. encryption setup runs
8. backend restarts
9. health checks finally pass

That is too much work for an autohealing path.

---

## Why This Is Slow

### 1. Recovery path and deploy path are coupled

The same `deploy.sh` flow is doing both:
- intentional rollout work
- emergency VM bring-up work

Those should not have the same amount of boot-time work.

### 2. Too much mutable setup happens at boot

Even when steps are idempotent, they still cost time and introduce failure modes:
- Git sync
- Secret sync
- pip / venv verification
- Ops Agent install/apply
- encryption bootstrap

### 3. Health depends on a lot of prerequisites

A new VM is not useful until:
- repo exists
- key exists
- env exists
- service starts
- port binds
- health check passes

That chain is longer than it should be.

---

## Desired End State

Replacement VMs should follow this shape:

1. boot from a prepared image/template
2. load runtime secrets
3. start backend service
4. pass health check

That is the target.

In other words:

**build first, boot fast**

not

**boot, then build the machine**

---

## Recommended Architecture Direction

### Phase A: shrink startup work without changing platform

This is the fastest reliability win.

Do now:
- keep current MIG
- reduce what happens in startup
- make deploy and recovery paths more distinct

### Phase B: create a baked backend image/template

Pre-bake:
- app code or release artifact
- Python runtime
- venv
- installed Python dependencies
- Ops Agent
- startup scripts / system config

Then startup only:
- sync env/secrets
- start backend
- smoke check

### Phase C: split deploy path from recovery path

Deploy path:
- may pull new code
- may refresh dependencies
- may do heavier work

Recovery path:
- must be minimal
- must not depend on a full deploy

---

## Concrete Plan

## Step 1: Measure current replacement timeline

Before changing architecture, measure where time is spent.

Capture timestamps for:
- VM created
- startup script begins
- repo ready
- deploy.sh begins
- secret sync complete
- ops agent complete
- backend start
- port bind
- `/api/health` success
- MIG marks healthy

Output:
- one incident-style timing report for a single recreated VM

Why:
- we need real bottlenecks, not guesses

---

## Step 2: Separate “deploy setup” from “boot setup”

Current problem:
- `deploy.sh` mixes deployment and machine bootstrap concerns

Refactor into:

### `bootstrap-runtime.sh`
For replacement/new VM boot only:
- verify required directories
- sync secrets
- ensure service files/config exist
- start backend
- run local smoke check

### `deploy-release.sh`
For intentional deploys only:
- git fetch/reset or artifact swap
- optional dependency refresh
- optional frontend handling
- restart services

Goal:
- recovery no longer depends on full deploy logic

---

## Step 3: Remove pip/install work from recovery path

Recovery should not need to decide whether pip must run.

Move these out of startup:
- venv creation
- `pip install -r requirements.txt`
- package/bootstrap decisions

Allowed at boot:
- verify baked venv exists
- fail fast if missing

Goal:
- no dependency installation during autohealing

---

## Step 4: Bake Ops Agent into the image/template

We already improved this by making `deploy.sh` install/apply Ops Agent.

Next step:
- preinstall Ops Agent in the VM image/template
- keep boot-time config apply lightweight

Goal:
- new VM does not install observability tooling from scratch during recovery

---

## Step 5: Bake app/runtime into image or artifact

Best options:

### Option A: custom VM image
Pre-bake:
- repo checkout at release
- backend venv
- dependencies
- agent

### Option B: release artifact
Boot downloads a versioned backend artifact instead of doing git/bootstrap

Between the two:
- custom image is fastest at boot
- artifact-based is easier to iterate at first

Recommended order:
1. artifact-based simplification
2. then move to image baking

---

## VM Image First: Concrete Implementation Plan

This is the chosen direction for the current API MIG.

### What the VM image should contain

Bake these into the image:
- OS packages required by the backend
- Python runtime
- `/home/tarun_yadav/AstrologyApp/backend/venv`
- Python dependencies already installed
- app code or release artifact already present on disk
- `restart_server.sh`
- backend logs directory structure
- Google Cloud Ops Agent installed
- Ops Agent config file already placed
- service/startup helper scripts already present

Prefer also baking:
- a known-good backend release directory
- smoke-test helper script

Do **not** bake:
- `.env`
- private keys from Secret Manager
- environment-specific secrets
- one-off local machine state

### What should remain dynamic at boot

Startup should only:
1. sync runtime secrets from Secret Manager
2. verify required files exist
3. export runtime env
4. start backend
5. run local `/api/health` smoke check

That is all.

### What must move out of boot-time

These current `deploy.sh` responsibilities should no longer be part of recovery:
- `git fetch`
- `git reset --hard`
- changed-files diff logic
- pip decision logic
- venv creation
- `pip install`
- frontend build logic
- release selection logic mixed with restart logic

### Recommended boot-time script shape

Create a dedicated script:

`scripts/bootstrap-runtime.sh`

Responsibilities:
- load instance/release metadata
- sync `backend/.env`
- sync WhatsApp private key
- verify baked backend tree exists
- verify baked venv exists
- optionally re-apply Ops Agent config
- start backend
- run local health check
- exit non-zero on failure

This script should be small and deterministic.

### Recommended deploy-time script shape

Keep a heavier deploy/release script separate, for intentional rollout only:

`scripts/deploy-release.sh`

Responsibilities:
- prepare next backend release
- update image input or release artifact
- optional dependency rebuild
- optional frontend work
- controlled rollout

### Release layout recommendation

Instead of a single mutable app tree, move toward:

- `/home/tarun_yadav/releases/backend/<release-id>/...`
- `/home/tarun_yadav/current-backend -> /home/tarun_yadav/releases/backend/<release-id>`

Then the image can boot with a known release already present.

Benefits:
- easier rollback
- less mutation in-place
- clearer release identity in logs

### How image creation should work

Recommended flow:

1. build release on a controlled builder VM or CI runner
2. populate backend app tree
3. install dependencies into venv
4. install/apply Ops Agent
5. place bootstrap scripts
6. create VM image from that prepared machine
7. create/update instance template using that image
8. verify template metadata explicitly
9. roll MIG to new template

### What the instance template should provide

Template should define from scratch:
- machine type
- disk/image
- service account
- tags
- metadata
- startup-script

Avoid:
- inheriting old startup-script metadata through copied template lineage

### Minimal startup-script target

The startup-script embedded in template metadata should ideally do something like:

1. log startup begin
2. invoke `scripts/bootstrap-runtime.sh`
3. exit with success/failure

That script should not contain large inline provisioning logic.

### Rollout path after image adoption

Normal deploy:
- build new release/image
- create new instance template
- point MIG to new template
- rolling replace

Recovery/autohealing:
- MIG creates replacement VM from baked image
- small startup script runs
- backend becomes healthy quickly

### How this changes current `deploy.sh`

Today `deploy.sh` is doing:
- code sync
- dependency management
- secret sync
- agent install/apply
- backend restart
- frontend build/serve decisions

After VM-image adoption, the recovery path should not call this full script.

At most, parts of it should be split into:
- build-time image prep
- release-time rollout
- runtime bootstrap

### Recommended milestone sequence

#### Milestone 1
Extract:
- `scripts/bootstrap-runtime.sh`
- `scripts/deploy-release.sh`

#### Milestone 2
Make current MIG startup call only `bootstrap-runtime.sh`

#### Milestone 3
Create first manually baked backend image

#### Milestone 4
Create fresh instance template using that image

#### Milestone 5
Test controlled single-VM replacement timing

#### Milestone 6
Adopt for production rolling replacement path

### Acceptance criteria for VM-image phase

We should call the VM-image migration successful when:
- replacement VM does not run pip at boot
- replacement VM does not do git sync at boot
- replacement VM does not install Ops Agent at boot
- startup script is short and understandable
- backend health comes up materially faster than current path
- template metadata is explicitly verified before rollout

---

## Step 6: Make startup script tiny and explicit

Startup script should do only:

1. ensure secrets are present
2. ensure expected release/app path exists
3. start backend service
4. run local health probe

Avoid in startup:
- apt installs
- pip installs
- git operations
- multi-purpose deploy branching
- one-off repair logic

---

## Step 7: Improve readiness contract

A VM should only count healthy when:
- backend process is started
- port `8001` is listening
- `/api/health` succeeds

Optional but useful:
- startup checkpoint log includes release/version
- local smoke check verifies critical env vars are loaded

---

## Step 8: Keep one spare if recovery speed is critical

Even with a faster template, replacement still takes time.

If incidents are expensive:
- consider keeping one extra healthy instance during busy periods

This is not a substitute for boot optimization.
It is a safety margin.

---

## Recommended Delivery Order

### Near-term
- measure current boot timeline
- split bootstrap from deploy
- stop pip/install work during recovery

### Mid-term
- switch from git/bootstrap-on-boot to release artifact on boot

### Best long-term
- baked backend image/template with minimal startup script

---

## What To Change In This Repo

### Likely files involved
- `deploy.sh`
- `restart_server.sh`
- startup-script source-of-truth in GCP metadata/template
- new `scripts/bootstrap-runtime.sh`
- new release/artifact prep script

### Documentation to keep updated
- `docs/PRODUCTION_STATUS_2026-06-10.md`
- `docs/OBSERVABILITY_HARDENING_PLAN.md`
- this file

---

## Risks To Avoid

### 1. Mutating all-instances metadata inline
We have already seen this become brittle.

### 2. Copying old templates that silently carry stale startup metadata
Template authoring must be explicit and verifiable.

### 3. Treating “deploy succeeded” as “replacement path is healthy”
Those are different success criteria.

---

## Acceptance Criteria

We should consider this solved when:

- a recreated backend VM reaches healthy state much faster than today
- replacement no longer depends on pip/install work
- startup script is short and deterministic
- app logs clearly show startup checkpoints
- template/image contents are verified before MIG rollout

---

## Next Practical Session

1. Measure one real replacement VM timeline end to end
2. Extract a minimal `bootstrap-runtime.sh` from current `deploy.sh`
3. Identify everything in `deploy.sh` that should never happen during recovery
4. Decide whether first simplification uses:
   - baked VM image, or
   - versioned backend artifact

My recommendation:

**start with boot-path separation first, then move to image baking**

That gives the quickest improvement without a giant platform jump.

---

## Current Progress

- `scripts/bootstrap-runtime.sh` now exists as the first extracted runtime-only bootstrap path.
- It currently handles:
  - Secret Manager sync
  - optional Ops Agent apply
  - baked app/venv presence checks
  - backend restart/start
  - local `/api/health` verification
- It intentionally does **not** handle:
  - git fetch/reset
  - pip install
  - frontend build/deploy
- `scripts/deploy-release.sh` now contains the heavier existing release/deploy flow.
- `deploy.sh` is now a thin wrapper that delegates to `scripts/deploy-release.sh`.
- `scripts/gce-startup-bootstrap.sh` now exists as a candidate minimal GCE startup script that delegates directly to `scripts/bootstrap-runtime.sh`.
- Current production MIG inspection confirmed the active template still uses a heavyweight startup script that:
  - installs packages at boot
  - installs `gcloud` / `node` at boot
  - pulls a GitHub deploy key from Secret Manager
  - clones/pulls the repo
  - invokes `bash deploy.sh` during boot
  - in at least the active `astroroshni-v3-template-nat`, does so with `FORCE_FULL_DEPLOY=true`
- A non-prod validation image was created from `astroroshni-mig-zmc9` via:
  - snapshot: `astroroshni-bootstrap-test-snap-20260615-180806`
  - image: `astroroshni-bootstrap-test-20260615-180947`
- A standalone validation VM was created:
  - instance: `astroroshni-bootstrap-vmtest-1`
- First boot with the minimal startup script failed for the expected reason:
  - the baked app tree in that image did not yet contain `scripts/bootstrap-runtime.sh`
  - this confirms the wrapper startup path is wired correctly and that the image contents, not the startup model, were the blocker
- After copying `scripts/bootstrap-runtime.sh` onto the standalone validation VM, the runtime-only bootstrap completed successfully:
  - Secret Manager sync succeeded
  - backend restarted cleanly
  - local `/api/health` passed
- After copying and running `scripts/gce-startup-bootstrap.sh` on the same validation VM, the full wrapper -> bootstrap chain also completed successfully.
- `scripts/bootstrap-runtime.sh` can start both:
  - backend on `8001`
  - frontend static server on `3001`
  but the recovery/image path should run with `SERVE_FRONTEND_LOCALLY=false` because frontend is now intended to be served from the bucket/CDN path
- A fresh release image was baked from the current repo state:
  - builder VM: `astroroshni-image-builder-20260615-203157`
  - image: `astroroshni-release-20260615-203157`
- A second standalone validation VM was created directly from that fresh release image:
  - instance: `astroroshni-bootstrap-vmtest-2`
- That second validation VM succeeded without any manual file copy:
  - minimal startup wrapper ran
  - `scripts/bootstrap-runtime.sh` was already present in the baked app tree
  - backend health passed
  - frontend health passed
  - total runtime bootstrap reached healthy state in roughly 26 seconds after script start
- A clean regional instance template was created from the validated release image:
  - template: `astroroshni-vmimage-template-20260615`
  - startup script: `scripts/gce-startup-bootstrap.sh`
  - status: created, not attached to the prod MIG yet

Validation takeaway:
- the new startup model is valid
- before production rollout, the baked image content must include the new repo state containing:
  - `scripts/bootstrap-runtime.sh`
  - `scripts/deploy-release.sh`
  - updated `deploy.sh`
- that requirement is now satisfied by `astroroshni-release-20260615-203157`
- the first non-prod template artifact is now ready as `astroroshni-vmimage-template-20260615`
- follow-up correction: the VM-image recovery path should be backend-only and run with `SERVE_FRONTEND_LOCALLY=false`, matching the documented bucket/CDN frontend architecture
- A backend-only release image was then baked:
  - image: `astroroshni-release-backend-20260615-212840`
- A backend-only standalone validation VM was created from that image:
  - instance: `astroroshni-bootstrap-vmtest-backend-1`
- That backend-only validation succeeded:
  - minimal startup wrapper ran
  - backend health passed
  - no frontend startup was attempted
  - only port `8001` was listening after bootstrap
  - runtime bootstrap reached healthy backend state in roughly 24 seconds after script start

Next code step:
- create a fresh backend-only instance template from `astroroshni-release-backend-20260615-212840`, then do a one-instance canary rollout while preserving the current prod template as rollback
