package.path='./?.lua;./?/init.lua;'..package.path
local nav=require('src.scene_links')
local view=require('src.scene_view')
local function props(name,size)
 return {name=name,position={0,0},scale={1,1},anchor={0,0},size=size or {100,100},visible=true}
end
local root={path='gui/MAIN.csb',name='Main',root={class='Node',props=props('Root'),children={
  {class='ProjectNode',project_file='Gui/CELL.csb',props=props('Nested',{0,0}),children={}},
  {class='Button',props=props('Start',{50,30}),button_states={
     normal={path='normal.png',type=0},pressed={path='pressed.png',type=0},disabled={path='disable.png',type=0}},resource={path='normal.png',type=0},children={}},
}}}
local cell={path='gui/cell.csb',name='Cell',root={class='Node',props=props('Cell'),children={
   {class='ProjectNode',project_file='Gui/MAIN.csb',props=props('Cycle',{0,0}),children={}},
}}}
local index=nav.build({root,cell})
assert(nav.find(index,'GUI/CeLl.csb')==cell)
assert(nav.find(index,'../gui/cell.csb')==nil)
assert(nav.find(index,'Gui/..\\CELL.csb')==nil)
assert(nav.find(index,'Gui/unavailable.csb')==nil)
assert(nav.find(nav.build({cell,cell}),'gui/cell.csb')==nil)
view.setCatalog({root,cell})
assert(view.active(root)==root)
view.next(root,1)
local node,count=view.inspect(root)
assert(count==3 and node.node.project_file=='Gui/CELL.csb')
assert(view.openReference(root)==true)
assert(view.active(root)==cell and view.depth(root)==1)
view.next(root,1)
assert(view.openReference(root)==false) -- protege contra ciclos
assert(view.back(root)==true)
assert(view.active(root)==root and view.inspect(root).node.project_file=='Gui/CELL.csb')
assert(view.back(root)==false)
view.next(root,1)
assert(view.inspect(root).node.class=='Button')
assert(view.currentButtonState(root)=='normal')
local ok,state=view.cycleButton(root)
assert(ok and state=='pressed')
ok,state=view.cycleButton(root)
assert(ok and state=='disabled')
ok,state=view.cycleButton(root)
assert(ok and state=='normal')
view.reset()
assert(view.depth(root)==0 and view.inspect(root).node.class=='Node')
print('FASE10 OK')
