for _,p in ipairs({'main.lua','src/collider_view.lua','reports/native_colliders.lua'}) do
  local f,e=loadfile(p)
  assert(f,p..': '..tostring(e))
end
print('F16 syntax OK')
