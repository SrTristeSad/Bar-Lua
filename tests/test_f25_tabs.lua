-- Static syntax contract: all UI modes remain integrated after adding the F25 tab.
for _, p in ipairs({'main.lua','src/hero_hurt.lua','src/hero_hurt_view.lua','reports/entity_damage_flow.lua'}) do
  local chunk,err = loadfile(p)
  assert(chunk, tostring(p)..': '..tostring(err))
end
print('F25 TABS SYNTAX OK')
