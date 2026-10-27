-- Visualizador F6 de interfaces Cocos Studio: inspeção, não menus jogáveis.
-- F9: resolve subtexturas .bplist e compõe hierarquia/ancoras/z para desenho.
local layout = require('src.scene_layout')
local geometry = require('src.sprite_geometry')
local sceneLinks = require('src.scene_links')
local M = {nodeIndex=1,showGuides=true,showHidden=false,showText=true}
local baseScene,current,nodes,viewport=nil,nil,{},nil
local trail,skinStates={},{}
local catalog={}
local MAX_TRAIL=16
local function changeScene(scene, nodeIndex)
    current,nodes,viewport=scene,layout.flatten(scene),nil
    M.nodeIndex=math.max(1,math.min(#nodes,nodeIndex or 1))
end
local function ensure(scene)
    if baseScene == scene then return end
    baseScene=scene
    trail,skinStates={},{}
    changeScene(scene,1)
end
function M.reset()
    baseScene,current,nodes,viewport=nil,nil,{},nil
    trail,skinStates={},{}
    M.nodeIndex=1
end
function M.setCatalog(scenes)
    catalog=sceneLinks.build(scenes)
    M.reset()
end
function M.active(scene) ensure(scene); return current end
function M.depth(scene) ensure(scene);return #trail end
function M.next(scene, direction)
    ensure(scene)
    M.nodeIndex=math.max(1,math.min(#nodes,M.nodeIndex+direction))
end
function M.inspect(scene)
    ensure(scene)
    local entry=nodes[M.nodeIndex]
    if entry then
        local x,y=layout.transform(entry.world,0,0)
        entry.x,entry.y=x,y
    end
    return entry,#nodes
end
function M.openReference(scene)
    ensure(scene)
    local entry=nodes[M.nodeIndex]
    local reference=entry and entry.node and entry.node.project_file
    if not reference then return false,'Nó sem subcena referenciada' end
    local target,reason=sceneLinks.find(catalog,reference)
    if not target then return false,reason end
    if #trail>=MAX_TRAIL then return false,'Limite de profundidade para inspeção' end
    for _,item in ipairs(trail) do
        if item.scene==target then return false,'Referência circular' end
    end
    if current==target then return false,'Referência circular' end
    trail[#trail+1]={scene=current,index=M.nodeIndex}
    changeScene(target,1)
    return true
end
function M.back(scene)
    ensure(scene)
    local previous=trail[#trail]
    if not previous then return false end
    trail[#trail]=nil
    changeScene(previous.scene,previous.index)
    return true
end
local cycle={'normal','pressed','disabled'}
function M.cycleButton(scene)
    ensure(scene)
    local entry=nodes[M.nodeIndex]
    if not entry or entry.node.class~='Button' then return false end
    local available=entry.node.button_states or {}
    local present={}
    for _,key in ipairs(cycle) do if available[key] then present[#present+1]=key end end
    if #present<2 then return false end
    local previous=skinStates[entry.node] or 'normal'
    local at=1
    for i,value in ipairs(present) do if value==previous then at=i end end
    skinStates[entry.node]=present[at % #present+1]
    return true,skinStates[entry.node]
end
function M.currentButtonState(scene)
    ensure(scene)
    local entry=nodes[M.nodeIndex]
    return entry and skinStates[entry.node] or 'normal'
end
function M.toggleGuides() M.showGuides=not M.showGuides end
function M.toggleHidden() M.showHidden=not M.showHidden end
function M.toggleText() M.showText=not M.showText end
function M.pick(scene,mouseX,mouseY)
    ensure(scene)
    local v=viewport
    if not v or mouseX<v.x or mouseY<v.y or mouseX>v.x+v.w or mouseY>v.y+v.h then return false end
    local chosen=layout.pick(nodes,(mouseX-v.ox)/v.scale,(v.oy-mouseY)/v.scale,M.showHidden)
    if chosen then M.nodeIndex=chosen;return true end
    return false
end
local function trunc(s,n)
    s=tostring(s or '')
    return #s<=n and s or s:sub(1,n-3)..'...'
end
local function val(p,name,i,fallback)
    local a=p[name]
    if type(a)=='table' and type(a[i])=='number' then return a[i] end
    return fallback
end
local function drawResource(g,r, w,h)
    local image=r and r.image
    if not image then return false end
    local iw,ih=image:getDimensions()
    if iw<=0 or ih<=0 then return false end
    if r.kind=='atlas' then
        local frame=r.frame
        if not r.quad or not frame then return false end
        local sourceW,sourceH=frame.source_w or frame.w,frame.source_h or frame.h
        if sourceW<=0 or sourceH<=0 then return false end
        -- O atlas pode guardar só um recorte. A geometria original é medida
        -- no canvas completo e escalada para o tamanho do widget.
        g.push()
        g.translate(w/2,h/2)
        g.scale(w/sourceW,h/sourceH)
        geometry.draw(image,r.quad,frame)
        g.pop()
    else
        g.draw(image,0,h,0,w/iw,-h/ih)
    end
    return true
end
function M.draw(scene,ctx)
    ensure(scene)
    scene=current
    local g,x,y,w,h=love.graphics,ctx.x,ctx.y,ctx.w,ctx.h
    ctx.background(x,y,w,h,{0.11,0.15,0.19})
    if #nodes==0 then ctx.put('Cena sem nós recuperados.',x+20,y+20);return end
    local root=scene.root.props or {}
    local size=root.size or {960,540}
    local sw,sh=size[1]>0 and size[1] or 960,size[2]>0 and size[2] or 540
    local frameH=math.max(80,h-153)
    local factor=math.max(0.02,math.min((w-55)/sw,(frameH-42)/sh,2.0))
    local ox,oy=x+w/2-sw*factor/2,y+46+(frameH-sh*factor)/2+sh*factor
    viewport={x=x,y=y+40,w=w,h=frameH-40,ox=ox,oy=oy,scale=factor}
    g.setColor(0.23,0.30,0.36)
    g.rectangle('fill',ox,oy-sh*factor,sw*factor,sh*factor)
    g.setScissor(viewport.x,viewport.y,viewport.w,viewport.h)
    local maxImages,maxLabels=900,220
    local totalImages, missing = 0,0
    local cursor=0
    g.push()
    g.translate(ox,oy)
    g.scale(factor,-factor)
    local function drawNode(node,depth)
        cursor=cursor+1
        local currentIndex=cursor
        local entry=nodes[currentIndex]
        if not entry then return end
        local p=node.props or {}
        g.push()
        local tx,ty,sx,sy,rotation,kx,ky=layout.parameters(p)
        g.translate(tx,ty)
        if rotation~=0 then g.rotate(rotation) end
        if kx~=0 or ky~=0 then g.shear(kx,ky) end
        g.scale(sx,sy)
        local rw,rh=entry.w,entry.h
        g.translate(-val(p,'anchor',1,0.5)*rw,-val(p,'anchor',2,0.5)*rh)
        if entry.visible or M.showHidden then
            local resource = node.resource
            if node.class=='Button' and node.button_states then
                local state = skinStates[node] or 'normal'
                resource = node.button_states[state] or node.button_states.normal or resource
            end
            if resource and maxImages>0 then
                local resolved
                if ctx.resolveResource then
                    resolved=ctx.resolveResource(resource)
                elseif ctx.resolveImage then
                    local img=ctx.resolveImage(resource.path,resource.type)
                    if img then resolved={kind='image',image=img} end
                end
                if resolved then
                    local iw,ih=resolved.image:getDimensions()
                    local fw=(resolved.frame and (resolved.frame.source_w or resolved.frame.w)) or iw
                    local fh=(resolved.frame and (resolved.frame.source_h or resolved.frame.h)) or ih
                    local cw,ch=rw>0 and rw or fw,rh>0 and rh or fh
                    if cw>0 and ch>0 then
                        local col=p.color or {255,255,255,255}
                        local opacity=entry.opacity*(entry.visible and 1 or 0.30)
                        g.setColor((col[1] or 255)/255,(col[2] or 255)/255,(col[3] or 255)/255,opacity)
                        if drawResource(g,resolved,cw,ch) then maxImages=maxImages-1;totalImages=totalImages+1 end
                    end
                else
                    missing=missing+1
                end
            end
            if M.showText and node.text and maxLabels>0 then
                maxLabels=maxLabels-1
                g.setColor(0.98,0.96,0.89,math.min(0.9,entry.opacity))
                -- Fontes nativas e estilos Cocos Studio ainda nao sao recuperados.
                -- O texto abaixo é uma anotacao visual, não tipografia fiel.
                g.push()
                g.scale(1,-1)
                g.print(trunc(node.text,42),0,-math.max(rh,12))
                g.pop()
            end
            if M.showGuides and rw>0 and rh>0 then
                if currentIndex==M.nodeIndex then g.setColor(1,0.78,0.24,1)
                elseif entry.visible then g.setColor(0.38,0.78,0.88,0.20)
                else g.setColor(1,0.4,0.4,0.17) end
                g.rectangle('line',0,0,rw,rh)
            end
            if currentIndex==M.nodeIndex then
                g.setColor(1,0.78,0.24,1)
                g.circle('fill',0,0,3/factor)
            end
        end
        for _,child in ipairs(layout.ordered(node.children)) do
            drawNode(child.node,depth+1)
        end
        g.pop()
    end
    drawNode(scene.root,0)
    g.pop()
    g.setScissor()
    local selected=nodes[M.nodeIndex] or nodes[1]
    local n,p=selected.node,selected.node.props or {}
    local wx,wy=layout.transform(selected.world,0,0)
    ctx.put(trunc(scene.name or scene.path,48)..' | '..#nodes..' nós | '..sw..'×'..sh..' | imagens: '..totalImages..' | subcenas: '..#trail,
        x+10,y+10,{0.96,0.98,1},ctx.small)
    ctx.background(x+8,y+h-105,w-16,100,{0.08,0.12,0.16})
    ctx.put(M.nodeIndex..'/'..#nodes..' '..string.rep('· ',math.min(8,selected.depth))..
        trunc(n.class..' '..(p.name or ''),65),x+16,y+h-100,{1,0.82,0.40},ctx.small)
    ctx.put(string.format('Origem (%.1f, %.1f) | tamanho %.1f×%.1f | z=%s | visível=%s',
        wx,wy,selected.w,selected.h,tostring(p.z or 0),tostring(selected.visible)),
        x+16,y+h-77,{0.84,0.9,0.96},ctx.small)
    local res=n.resource
    local activeSkin=skinStates[n] or 'normal'
    if n.class=='Button' and n.button_states then
        res=n.button_states[activeSkin] or n.button_states.normal or res
    end
    if n.project_file then
        ctx.put('ProjectNode → '..trunc(n.project_file,81),x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    elseif n.class=='Button' then
        ctx.put('Botão ['..activeSkin..'] | touch='..tostring(p.touch)..' | imagem='..trunc(res and res.path or '-',57),
            x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    elseif res then ctx.put('Imagem: '..trunc(res.path,82),x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    elseif n.text then ctx.put('Texto: '..trunc(n.text,82),x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    else ctx.put('Tag: '..tostring(p.action_tag or 0)..' | referência: '..tostring(p.callback or ''),x+16,y+h-56,{0.72,0.78,0.86},ctx.small) end
    ctx.put('Clique: selecionar | Tab: nós | Enter: subcena | Backspace: voltar | H: estado botão | G/V/T',
        x+16,y+h-27,{0.86,0.91,0.96},ctx.small)
end
return M
