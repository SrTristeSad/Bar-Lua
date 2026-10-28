-- F16: consulta dos caminhos de criação de b2Body/fixtures do APK 1.0.1811.
-- Não há mundo Box2D, verificação de contato ou gameplay nesta aba.
local M = {}
local explanations = {
  ['Entity::InitB2Body(b2Vec2 const&, bool)'] = {
    'Corpo existente? Se sim, não cria outro.',
    'Corpo novo: divide posição original por 100,',
    'chama BattleManager::getB2World e CreateBody.',
    'Argumento booleano pode forçar SetType.',
    'A conversão 100 é apenas deste ponto do código.',
  },
  ['Entity::InitCollision(config::hero::CollisionConfig const*)'] = {
    'Códigos de forma 1, 2 e 3 observados:',
    '1: fixture circular, com raio configurado',
    '2: polígono de quatro vértices, largura/altura',
    '3: polígonos de uma forma personalizada',
    'Caminhos criam fixture e bloqueiam rotação.',
    'Flags e regras de contato ainda não recuperadas.',
  },
}
function M.describe(item)
  if type(item) ~= 'table' then return nil end
  return explanations[item.name]
end
function M.draw(item,panel)
  local x,y,w,h=panel.x,panel.y,panel.w,panel.h
  panel.background(x,y,w,h,{0.12,0.16,0.20})
  panel.put('F12 · InitB2Body e InitCollision — leitura ELF ARM64',x+14,y+15,{1,0.88,0.55},panel.small)
  if not item then
    panel.put('Relatório ausente. Execute tools/analisar_colisores.py.',x+14,y+53,nil,panel.small)
    return
  end
  panel.put(item.name or '?',x+14,y+57,{0.9,0.96,1},panel.small)
  panel.put(string.format('Endereço: %s · %d instruções · %d padrões validados',
    item.address or '?', item.instructions or 0, item.checks or 0),x+14,y+95,nil,panel.small)
  local detail=M.describe(item) or {}
  for i,entry in ipairs(detail) do
    local py=y+147+(i-1)*29
    if py<y+h-110 then panel.put(entry,x+24,py,{0.7,0.92,0.83},panel.small) end
  end
  panel.put('Fatos confirmados no ELF 1.0.1811; não são simulação física.',
    x+14,y+h-74,{0.98,0.8,0.53},panel.small)
  panel.put('Não há herói controlável nem colisões executáveis nesta aba.',
    x+14,y+h-41,{0.82,0.88,0.92},panel.small)
end
return M
