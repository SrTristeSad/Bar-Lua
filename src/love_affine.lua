-- Convert the recovered 2D affine pose into LÖVE 11.x's 4x4 row-major matrix.
-- Source affine transform: x'=a*x+c*y+tx; y'=b*x+d*y+ty.
local M={}
function M.set(transform,m)
    assert(type(m)=='table' and type(m.a)=='number' and type(m.b)=='number'
        and type(m.c)=='number' and type(m.d)=='number'
        and type(m.tx)=='number' and type(m.ty)=='number',
        'expected 2D affine matrix with a,b,c,d,tx,ty')
    transform:setMatrix(
        m.a,m.c,0,m.tx,
        m.b,m.d,0,m.ty,
        0,0,1,0,
        0,0,0,1
    )
    return transform
end
function M.apply(m)
    local transform=M.set(love.math.newTransform(),m)
    love.graphics.applyTransform(transform)
end
return M
