package.path='./?.lua;./?/init.lua;'..package.path
local scenes=assert(loadfile('cache/scenes.lua'))()
assert(#scenes==560)
local view=require('src.scene_view')
view.setCatalog(scenes)
local original
for _,s in ipairs(scenes) do if s.path=='gui/00_node_itemcell.csb' then original=s;break end end
assert(original,'Cena exemplo nao encontrada')
local valid=false
local selected,total=view.inspect(original)
for i=1,total do
 local entry=view.inspect(original)
 if entry.node.project_file then
  if view.openReference(original) then
   assert(view.depth(original)==1)
   local active=view.active(original)
   assert(active~=original and active.path:lower()==entry.node.project_file:lower())
   assert(view.back(original) and view.active(original)==original)
   valid=true
   break
  end
 end
 view.next(original,1)
end
assert(valid,'Nenhuma referencia valida no exemplo real')
print('FASE10 REAL CSB OK')
