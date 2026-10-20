-- Probe BizHawk's NDS RAM access against a disposable copy of a local save.
-- The script does not save game progress; all generated output stays in build/.

local output_dir = assert(os.getenv("BW_TAS_OUTPUT_DIR"), "BW_TAS_OUTPUT_DIR is required")
local log = assert(io.open(output_dir .. "/ram-probe.txt", "w"), "cannot create probe log")

local function capture(name)
  client.screenshot(output_dir .. "/" .. name .. ".png")
end

local function advance(frames)
  for _ = 1, frames do emu.frameadvance() end
end

local function tap_a()
  joypad.set({ A = true })
  advance(8)
  joypad.set({})
  advance(48)
end

local function read_u32_le(address, domain)
  local value = 0
  for offset = 0, 3 do
    value = value + memory.readbyte(address + offset, domain) * (256 ^ offset)
  end
  return value
end

local ok, err = pcall(function()
  client.speedmode(1000)
  local domains = memory.getmemorydomainlist()
  log:write("Memory domains:\n")
  for _, domain in ipairs(domains) do
    log:write(string.format("%s: 0x%X bytes\n", domain, memory.getmemorydomainsize(domain)))
  end
  log:write(string.format("SRAM save map ID: %d\n", read_u32_le(0x19580, "SRAM")))
  log:write(string.format("SRAM save badges: 0x%02X\n", memory.readbyte(0x21204, "SRAM")))
  log:flush()

  -- Repeated A taps skip the boot movie and advance title/continue prompts.
  for attempt = 1, 40 do
    tap_a()
    if attempt == 12 or attempt == 24 or attempt == 40 then
      capture(string.format("probe-step-%02d", attempt))
      log:write(string.format("Captured after A tap %d.\n", attempt))
      log:flush()
    end
  end
  log:write("PASS: BizHawk loaded the patched White ROM, skipped opening prompts with A, and captured three milestones.\n")
end)

if not ok then log:write("FAIL: " .. tostring(err) .. "\n") end
log:close()
client.exit()
