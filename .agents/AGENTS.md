# Dashboard Editing Rules for Home Assistant

- **Dashboard File Structure** (`dashboard_nha-c-a-hi-u.yaml`):
  - **View 1: `Chế độ Phone`** (Lines 1 to ~1373):
    - All mobile solar widgets are packed into a single `vertical-stack` card.
    - Synchronized with `card_phone_full.yaml`.
  - **View 2: `Chế độ PC`** (Lines 1374 to end):
    - Desktop solar widgets and layout sections.
    - Synchronized with `card_pc_full.yaml`.

- **Agent Behavior Guidelines**:
  1. If the user specifies **"Phone"** or selects `card_phone_full.yaml`: Only edit View 1 and update `card_phone_full.yaml`. Output the copyable block for Phone.
  2. If the user specifies **"PC"** or selects `card_pc_full.yaml`: Only edit View 2 (`Chế độ PC`) and update `card_pc_full.yaml`. Output the copyable block for PC.
  3. If the user does not specify which view to modify, ask or check context before editing.
