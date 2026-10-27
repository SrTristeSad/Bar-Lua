for _,p in ipairs({'main.lua','src/scene_view.lua','cache/scenes.lua'}) do
  local chunk,err=loadfile(p)
  assert(chunk,err)
  if p=='cache/scenes.lua' then
    local scenes=chunk()
    assert(#scenes==560 and scenes[1].root and scenes[1].node_count>0)
    print('CSB cache scenes = '..#scenes)
  end
end
print('Lua Fase8 sintaxe/cache: OK')