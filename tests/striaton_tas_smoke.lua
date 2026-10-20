-- BizHawk Lua smoke test. The workflow starts the emulator with a local
-- BizHawk savestate and supplies BW_TAS_OUTPUT_DIR in the process environment.

local output_dir = assert(os.getenv("BW_TAS_OUTPUT_DIR"), "BW_TAS_OUTPUT_DIR is required")
local result_path = output_dir .. "/result.txt"
local log = assert(io.open(result_path, "w"), "cannot create result file")

local function capture(name)
  client.screenshot(output_dir .. "/" .. name .. ".png")
end

local function advance(frames)
  for _ = 1, frames do
    emu.frameadvance()
  end
end

local function tap_a()
  joypad.set({ A = true })
  advance(8)
  joypad.set({})
  advance(24)
end

local ok, err = pcall(function()
  capture("battle-start")
  for attempt = 1, 8 do
    tap_a()
    if attempt == 1 or attempt == 4 or attempt == 8 then
      capture(string.format("battle-step-%02d", attempt))
    end
  end
  log:write("PASS: BizHawk loaded the local checkpoint, advanced 256 frames, and captured four screenshots.\n")
end)

if not ok then
  log:write("FAIL: " .. tostring(err) .. "\n")
end

log:close()
client.exit()
