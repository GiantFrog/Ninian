local almanac = require("almanac")

local util = almanac.util

local fe3 = require("almanac.game.fe3")


local Character = {}
local Redirect = {}
local Job = {}
local Item = {}



---------------------------------------------------
-- Character --
---------------------------------------------------
Character.__index = Character
setmetatable(Character,  fe3.Character)

Character.section = almanac.get("database/fe3/redirect.json")
Character.helper_job_growth = false
Character.helper_portrait = "database/fe3/images"

Character.compare_cap = false

Character.inventory = inventory

Character.Job = Job
Character.Item = Item

Character.item_warning = true

function Character:show_cap()
    return nil
end

function Character:get_cap()
    return {hp = 52, atk = 40, skl = 40, spd = 40, lck = 40, def = 40, res = 40}
end

---------------------------------------------------
-- Redirect --
---------------------------------------------------
Redirect.__index = Redirect
setmetatable(Redirect, almanac.Workspace)

Redirect.section = almanac.get("database/fe3/redirect.json")

Redirect.redirect = true

function Redirect:default_options()
    return {book = false}
end

function Redirect:setup()
    self.book = self.options.book
end

local redirect_table = {
    b1 = Book 1,
    b2 = Book 2
    
}

function Redirect:show()
    local character = self:get()
    
    return character:show()
end

function Redirect:get()
    if not self.book then
        self.book = self.data.book[1]
    
    elseif book and not util.misc.value_in_table(self.data.book, self.book) then
        self.book = self.data.book[1]
    end
    
    local character = redirect_table[self.book]:new(self.id)
    character:set_options(self.passed_options)
    
    return character
end

function Redirect:default_options()
    return {book = false}
end

function Redirect:setup()
    self.book = self.options.book
end



---------------------------------------------------
-- Item --
---------------------------------------------------
Item.__index = Item
setmetatable(Item, fe3.Item)

Item.section = almanac.get("database/fe3/item.json")



--------------------------------------------------
-- Job --
---------------------------------------------------
Job.__index = Job
setmetatable(Job, fe3.Job)

Job.section = almanac.get("database/fe3/job.json")

-- Only return the res for display stuff and dread fither
function Job:get_base(display)
    local base = util.copy(self.data.base)
    
    if not display and self.id ~= "dreadfighter" then
        base.res = 0
    end
    
    return base
end

return {
    Character = Character,
    Job = Job,
    Item = Item,
    Redirect = Redirect
}
