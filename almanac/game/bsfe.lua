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
setmetatable(Character, Character)

Character.section = almanac.get("database/fe3/redirect.json")
Character.helper_job_growth = false
Character.helper_portrait = "database/fe3/images"

function Character:setup()
    self.job = self.Job:new(self.options.class)
    
end

function Character:default_options()
    return {
        class = self.data.job,
        book = "bsfe"
    }
end

function Character:show_cap()
    return nil
end

function Character:get_cap()
    return {hp = 52, atk = 20, skl = 20, spd = 20, lck = 20, def = 20, res = 20, wlv = 20}
end


function Character:final_base()
    
    local base = self:calc_base()

    -- For reclass games
    if not self.average_classic then
        if self.helper_job_base and not self:is_personal() then         
            base = util.math.add_stats(base, self.job:get_base())
            base.hp = base.hp - self.job.data.base.hp
            base.hp = base.hp + math.max(self.job.data.base.hp, self.data.base.hp)

            base.wlv = base.wlv - self.job.data.base.wlv 
            base.wlv = base.wlv + math.max(self.job.data.base.wlv, self.data.base.wlv )
        
          --[[
            print(self.job.data.name)
            if self.promo_remove_hp then
                base.hp = base.hp - self.job:get_base().hp
            end
            print('reclass')
            print(base.hp)
            ]]
        end
    
    -- Non reclass games
    else
        -- Apply base class stats
        local job = self.data.job
        if self:is_changed("class") then 
            job = self.job 
        else 
            job = self.Job:new(self.data.job) 
        end

        print(job.data.name)
        
        base = base + job:get_base()
        
        if self:has_averages() then
            base = self:calc_averages_classic(base)
        end
        
        if self.personal then
            base = base - job:get_base()
        end
    end
    
    base = self:common_base(base)
    
    return base
end

function Character:calc_averages(base, args)
    args = args or {}

    local calculator = self.avg:set_character(self)

    for k, v in pairs(args) do
        calculator[k] = v
    end

    base = calculator:calculate(base, self:get_lvl(), self.lvl, self.job_averages)
    return base
end

function Character:calc_base()
    local base = self:get_base()
    local job = self.Job:new(self.data.job)

    base.hp = 0
    base.wlv = 0

    if not self.average_classic and self:has_averages() then
        base = self:calc_averages(base)
    end
   

    return base
end

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
