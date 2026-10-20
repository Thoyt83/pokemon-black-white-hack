-- Load the local Striaton Gym checkpoint and leave BizHawk open for the user.
-- This startup helper never edits or saves the source game save.

local function advance(frames)
  for _ = 1, frames do emu.frameadvance() end
end

local function tap_a()
  joypad.set({ A = true })
  advance(8)
  joypad.set({})
  advance(10)
end

client.speedmode(1000)

-- Skip the intro/title screens and load the already-verified checkpoint.
for _ = 1, 46 do
  tap_a()
end

-- Decline wireless startup, accept wireless-disabled mode, and allow the map
-- transition to finish. Do not call client.exit(): the emulator stays open.
joypad.set({ B = true })
advance(8)
joypad.set({})
advance(24)
joypad.set({ A = true })
advance(8)
joypad.set({})
advance(900)

client.speedmode(100)
print("Ready: player loaded inside Striaton Gym on the local checkpoint.")
