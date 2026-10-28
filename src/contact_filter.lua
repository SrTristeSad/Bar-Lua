-- BarbarQ 1.0.1811: decisão de contato b2ContactFilter::ShouldCollide auditada no ELF.
-- Não executa Box2D e não resolve colisões.
local M={}
local function u16(v)
  if type(v)~='number' or v~=v or v==math.huge or v==-math.huge or v%1~=0 then
    error('campo de filtro inválido: inteiro requerido',3)
  end
  return v%65536
end
local function s16(v)
  local n=u16(v)
  return n>=32768 and n-65536 or n
end
local function band16(a,b)
  a,b=u16(a),u16(b)
  local r,bit=0,1
  for _=1,16 do
    if a%2==1 and b%2==1 then r=r+bit end
    a,b,bit=math.floor(a/2),math.floor(b/2),bit*2
  end
  return r
end
function M.filterForCollidable(enabled)
  if type(enabled)~='boolean' then error('enabled booleano requerido',2) end
  if enabled then return {categoryBits=1,maskBits=3,groupIndex=0} end
  return {categoryBits=0,maskBits=1,groupIndex=0}
end
function M.shouldCollide(a,b)
  if type(a)~='table' or type(b)~='table' then error('fixtures requeridos',2) end
  for _,f in ipairs({a,b}) do
    for _,key in ipairs({'categoryBits','maskBits','groupIndex'}) do
      if f[key]==nil then error('campo ausente: '..key,2) end
      u16(f[key])
    end
  end
  local ga,gb=s16(a.groupIndex),s16(b.groupIndex)
  if ga~=0 and ga==gb then return ga>0 end
  return band16(a.maskBits,b.categoryBits)~=0
     and band16(b.maskBits,a.categoryBits)~=0
end
return M
