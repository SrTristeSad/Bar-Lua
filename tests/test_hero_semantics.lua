package.path='./?.lua;./?/init.lua;'..package.path
local schema=require('src.hero_schema')
local view=require('src.level_attributes_view')
local native=dofile('reports/hero_schema.lua')
local evidence=dofile('reports/hero_semantics.lua')
local catalog=dofile('cache/hero_levels.lua')
assert(evidence.phase==31 and evidence.verified_instruction_count==648)
assert(schema.validatedSpeedType(native))
assert(schema.validatedSpeedReport(evidence))
assert(schema.slotLabel('0x44')=='HP inicial')
assert(schema.slotLabel('0x48')=='velocidade-base')
assert(schema.slotLabel('0x38')=='atributo nao identificado')
assert(schema.valueType(native,19).offset=='0x328')
local barbarian
for _,item in ipairs(catalog.groups) do if item.base_id==210001 then barbarian=item;break end end
assert(barbarian)
local row=barbarian.levels[1]
assert(schema.configSpeed(row)==150)
assert(schema.speedComponent(row,evidence)==1.5)
assert(schema.speedComponent(row,{})==nil)
assert(schema.configSpeed({values={['0x48']=-2}})==nil)
local buffer={}
local panel={x=0,y=0,w=1000,h=700,small='stub',background=function()end,put=function(text)buffer[#buffer+1]=tostring(text) end}
view.keypressed('r')
view.draw(barbarian,{total_instructions=696},panel,native,evidence)
local content=table.concat(buffer,'\n')
assert(content:find('velocidade-base',1,true))
assert(content:find('1.50',1,true))
assert(content:find('ValueType 5',1,true))
view.keypressed('t')
view.keypressed('right')
buffer={}
view.draw(barbarian,{},panel,native,evidence)
local content=table.concat(buffer,'\n')
assert(content:find('19',1,true))
assert(content:find('velocidade-base',1,true))
view.keypressed('r')
print('F31 HERO SEMANTICS LUA OK')
