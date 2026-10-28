-- F15: apenas inspeção estática do pipeline Box2D original.
-- Não calcula contatos, não move entidades e não substitui Box2D.
local M = {}
local labels = {
  ['b2World::Step(float, int, int)']='Passo do mundo: FindNewContacts, Collide, Solve, SolveTOI (condicionais).',
  ['b2ContactManager::Collide()']='Percorre contatos e delega a atualização para b2Contact::Update.',
  ['b2Contact::Update(b2ContactListener*)']='Atualiza o contato; aciona métodos virtuais conforme transições internas.',
  ['wildsContactListener::BeginContact(b2Contact*)']='Confere indicador +0x1c1 por entidade; pode invocar ProcessContact.',
  ['wildsContactListener::EndContact(b2Contact*)']='Somente RET na biblioteca auditada.',
  ['wildsContactListener::PreSolve(b2Contact*, b2Manifold const*)']='Somente RET na biblioteca auditada.',
  ['wildsContactListener::PostSolve(b2Contact*, b2ContactImpulse const*)']='Somente RET na biblioteca auditada.',
  ['Entity::ProcessContact(b2Vec2)']='Calcula ângulo com trigonometria e atualiza campos de entidade.',
}
function M.describe(entry)
  if type(entry) ~= 'table' then return nil end
  return labels[entry.name]
end
function M.draw(entry, panel)
  local x,y,w,h=panel.x,panel.y,panel.w,panel.h
  panel.background(x,y,w,h,{0.12,0.16,0.20})
  panel.put('F11 · Pipeline Box2D / eventos de contato — SOMENTE leitura',x+14,y+15,{1,0.88,0.58},panel.small)
  if type(entry)~='table' then
    panel.put('Relatório indisponível. Execute tools/analisar_contatos.py.',x+14,y+55,nil,panel.small)
    return
  end
  panel.put(entry.name or '?',x+14,y+55,{0.88,0.97,1.0},panel.small)
  panel.put(string.format('Endereço %s  |  %d instruções  |  %d verificações',
     entry.address or '?',entry.instructions or 0,entry.checks or 0),x+14,y+91,nil,panel.small)
  panel.put(string.format('Chamadas diretas: %d  |  indiretas: %d',
     entry.direct or 0,entry.indirect or 0),x+14,y+119,nil,panel.small)
  panel.put(M.describe(entry) or 'Metadados auditados; sem significado de gameplay confirmado.',
    x+14,y+155,{0.62,0.94,0.76},panel.small)
  local pipeline={
    'b2World::Step',
    '      ↓ b2ContactManager::Collide',
    '      ↓ b2Contact::Update',
    '      ↓ chamada virtual de listener (condicional)',
    '      ↓ wildsContactListener::BeginContact',
    '      ↓ Entity::ProcessContact (se indicador habilitado)',
  }
  local max=math.max(0,math.floor((h-265)/28))
  for i=1,math.min(#pipeline,max) do
    panel.put(pipeline[i],x+24,y+198+(i-1)*28,nil,panel.small)
  end
  panel.put('A ordem ilustrada é a relação de chamadas, NÃO uma simulação.',x+14,y+h-70,{0.92,0.79,0.55},panel.small)
  panel.put('Sem colisões, dano, IA, física executável ou rede nesta aba.',x+14,y+h-40,{0.78,0.85,0.89},panel.small)
end
return M
