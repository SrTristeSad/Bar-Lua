for _,file in ipairs({'main.lua','src/contact_view.lua','reports/native_contacts.lua','src/entity_move.lua'}) do
  local f,error_message=loadfile(file)
  assert(f,file..': '..tostring(error_message))
end
print('F15 syntax OK')
