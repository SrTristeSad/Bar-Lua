-- Amostra selecionada de símbolos reais do APK BarbarQ 1.0.1811.
-- O conversor tools/auditar_elf.py pode regenerar um índice mais completo.
return {
  {name="GameScene", count=86, methods={{signature="GameScene::processPursueFrame(int)",address="0xeb8738",bytes=532},{signature="GameScene::updateLogicFrame(float)",address="0xeb7bcc",bytes=2024}}},
  {name="BattleNet", count=52, methods={{signature="BattleNet::processFrameUpdate(pto::battle::SFrameUpdate*)",address="0x1439718",bytes=472}}},
  {name="BattleManager", count=81, methods={{signature="BattleManager::createHero(Entity::DataForInit&)",address="0xe3d4d4",bytes=600}}},
  {name="BattleFieldController", count=8, methods={{signature="BattleFieldController::handleFrameUpdate(google::protobuf::MessageLite*, tms::net::PtoWatcher*)",address="0xe79a9c",bytes=2068}}},
  {name="GameLayer", count=51, methods={{signature="GameLayer::onEntityCreate(LogicEventArgs const&)",address="0x1406e58",bytes=1392}}},
  {name="Hero", count=69, methods={{signature="Hero::InitSkillAndAttri(Entity::DataForInit const&)",address="0xe57810",bytes=184}}},
  {name="CSkill", count=23, methods={{signature="CSkill::CreateSkillBySkillConfigId(Entity*, int, std::__1::vector<CSkillEntity, std::__1::allocator<CSkillEntity> > const*, int)",address="0xe650b4",bytes=320}}},
  {name="CSkillEntity", count=1, methods={{signature="CSkillEntity::GetEntity(bool) const",address="0xe4de4c",bytes=60}}},
  {name="CMoveEdge", count=11, methods={{signature="CMoveEdge::init(config::hero::MoveEdgeConfig const*)",address="0xe5cfe8",bytes=244}}},
  {name="ViewMoveEdge", count=8, methods={{signature="ViewMoveEdge::update(float)",address="0x1314f1c",bytes=256}}},
  {name="BattleDataManager", count=33, methods={{signature="BattleDataManager::calcCauseMostDamage()",address="0xe36234",bytes=216}}},
  {name="UILayer", count=163, methods={{signature="UILayer::initSkillBar()",address="0x141c884",bytes=1420}}},
}
