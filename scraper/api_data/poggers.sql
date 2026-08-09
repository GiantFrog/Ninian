--HARD ALT NAMES
select * from skills inner join skill_families on skills.skill_family = skill_families.id where skills.name like 'Odd Temp%' order by skills.name desc limit 1;

--CHARACTER SELECTION FROM A SKILL
select distinct feh_units.* from feh_units cross join skeys(passive_c) as alt_name_c where alt_name_c='Odd Tempest 2';
--pull in skills.name and skill_families.slot to build the above query
