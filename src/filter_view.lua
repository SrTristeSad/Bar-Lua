-- F13: visualizador de regras de filtragem, não física executável.
local codec=require('src.contact_filter')
local M={a=true,b=true,group=0}
function M.reset() M.a,M.b,M.group=true,true,0 end
function M.state()
  local a,b=codec.filterForCollidable(M.a),codec.filterForCollidable(M.b)
  if M.group~=0 then a.groupIndex=M.group;b.groupIndex=M.group end
  return a,b,codec.shouldCollide(a,b)
end
function M.keypressed(key)
  if key=='a' then M.a=not M.a;return true end
  if key=='b' then M.b=not M.b;return true end
  if key=='g' then M.group=(M.group==0 and 1 or (M.group==1 and -1 or 0));return true end
  if key=='r' then M.reset();return true end
  return false
end
function M.draw(_,panel)
  local x,y,h=panel.x,panel.y,panel.h
  panel.background(x,y,panel.w,h,{0.12,0.16,0.20})
  local function put(s,dy,c)
    if dy<h-15 then panel.put(s,x+16,y+dy,c,panel.small) end
  end
  put('F13 · Filtros de contato ARM64 1.0.1811',19,{1,0.86,0.5})
  put('A/B alternam fixture · G grupo 0/+1/-1 · R reinicia',56)
  local a,b,yes=M.state()
  local function fmt(label,f)
    return string.format('%s category=0x%04X mask=0x%04X group=%d',label,f.categoryBits,f.maskBits,f.groupIndex)
  end
  put(fmt('Fixture A',a),111,{0.79,0.93,1})
  put(fmt('Fixture B',b),149,{0.79,0.93,1})
  put('ShouldCollide = '..(yes and 'TRUE' or 'FALSE'),206,yes and {0.6,1,0.7} or {1,0.72,0.66})
  put('setCollidable(true): categoria 1, máscara 3, grupo 0.',259)
  put('setCollidable(false): categoria 0, máscara 1, grupo 0.',290)
  put('As duas máscaras devem permitir as categorias correspondentes.',339)
  put('Grupos iguais não-zero: positivo libera, negativo bloqueia.',371)
  put('Matriz com group=0:',419,{1,0.9,0.64})
  for i,c in ipairs({{true,true},{true,false},{false,true},{false,false}}) do
    local result=codec.shouldCollide(codec.filterForCollidable(c[1]),codec.filterForCollidable(c[2]))
    put(string.format('A=%-5s B=%-5s => %s',tostring(c[1]),tostring(c[2]),result and 'TRUE' or 'FALSE'),438+i*25)
  end
  put('Sem geometria, contatos físicos ou gameplay nesta aba.',h-44,{1,0.79,0.55})
end
return M
