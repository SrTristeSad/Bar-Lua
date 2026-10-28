-- Fase 15: metadados de contatos do APK original; NAO e fisica funcional.
return {
  {name="wildsContactListener::PreSolve(b2Contact*, b2Manifold const*)", address="0xe43928", instructions=1, direct=0, indirect=0, checks=0},
  {name="b2World::Step(float, int, int)", address="0x1b70eac", instructions=127, direct=13, indirect=0, checks=5},
  {name="wildsContactListener::BeginContact(b2Contact*)", address="0xe438c0", instructions=25, direct=1, indirect=0, checks=5},
  {name="wildsContactListener::EndContact(b2Contact*)", address="0xe43924", instructions=1, direct=0, indirect=0, checks=0},
  {name="Entity::ProcessContact(b2Vec2)", address="0xe4b574", instructions=52, direct=4, indirect=0, checks=5},
  {name="b2Contact::Update(b2ContactListener*)", address="0x1b726d8", instructions=148, direct=2, indirect=4, checks=2},
  {name="wildsContactListener::PostSolve(b2Contact*, b2ContactImpulse const*)", address="0xe4392c", instructions=1, direct=0, indirect=0, checks=0},
  {name="b2ContactManager::Collide()", address="0x1b6dcc8", instructions=102, direct=3, indirect=1, checks=1},
}
