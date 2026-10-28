local lfs = io.popen('find . -name "*.lua" -not -path "*/lib/*" -not -path "*/assets_original/*"')
local n=0
for f in lfs:lines() do
 local fn,err=loadfile(f)
 if not fn then error('syntax in '..f..': '..tostring(err)) end
 n=n+1
end
lfs:close()
print('SYNTAX F36 OK: '..n..' arquivos')
