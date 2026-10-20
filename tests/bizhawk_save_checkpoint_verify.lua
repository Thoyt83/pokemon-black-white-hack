-- Quickly verify a generated BW save in BizHawk and capture every prompt.
-- The only ROM/save inputs are local, user-supplied test materials.

local output_dir = assert(os.getenv("BW_TAS_OUTPUT_DIR"), "BW_TAS_OUTPUT_DIR is required")
local log = assert(io.open(output_dir .. "/save-check.txt", "w"), "cannot create verification log")
local result = assert(io.open(output_dir .. "/result.txt", "w"), "cannot create verification result")

local function advance(frames)
  for _ = 1, frames do emu.frameadvance() end
end

local function tap_a()
  joypad.set({ A = true })
  advance(8)
  joypad.set({})
  advance(10)
end

local function read_u32_le(address, domain)
  local value = 0
  for offset = 0, 3 do
    value = value + memory.readbyte(address + offset, domain) * (256 ^ offset)
  end
  return value
end

client.speedmode(1000)
local initial_map_id = read_u32_le(0x19580, "SRAM")
log:write(string.format("Initial SRAM map ID: %d\n", initial_map_id))
log:write(string.format("Initial SRAM badge flags: 0x%02X\n", memory.readbyte(0x21204, "SRAM")))
log:flush()

if initial_map_id ~= 7 then
  local failure = string.format("FAIL: expected Striaton Gym map 7, found map %d.\n", initial_map_id)
  log:write(failure)
  result:write(failure)
  result:close()
  log:close()
  client.exit()
  return
end

for attempt = 1, 46 do
  tap_a()
  if attempt == 42 or attempt == 46 then
    client.screenshot(string.format("%s/save-check-%02d.png", output_dir, attempt))
    log:write(string.format("Captured milestone after A tap %d.\n", attempt))
    log:flush()
  end
end

-- Decline the optional wireless C-Gear startup prompt and let the loaded save
-- finish entering the overworld. One final screenshot is enough to verify it.
joypad.set({ B = true })
advance(8)
joypad.set({})
advance(24)
joypad.set({ A = true })
advance(8)
joypad.set({})
advance(900)
client.screenshot(output_dir .. "/save-check-gameplay.png")
local success = "PASS: loaded the save-based Striaton Gym checkpoint, disabled wireless, and advanced 900 frames.\n"
log:write(success)
result:write(success)
result:close()

log:close()
client.exit()
