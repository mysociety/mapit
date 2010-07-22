-- 1   2004-12-02
-- 2   2004-12-07  Scottish Parl constituencies (for 2005 election)
-- 3   2005-10-03  some E councils
-- 7   2007-07-17  Some E councils, Welsh Assembly
-- 9   2007-10-18  Scottish Councils
-- 10  2009-01-29  Some E council changes
-- 11  2009-03-31  April 2009 council changes
-- 12  2009-12-07  Added parishes; a county boundary changes; as do some unitaries.
-- 13  2009-12-22  New WMC

-- Insert old generation 10 areas manually
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2216, 'E', 'CTY', 1, 10, 'Bedfordshire County Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2216, 'O', 'Bedfordshire County');
INSERT INTO areas_code (area_id, type, code) VALUES (2216, 'ons', '09');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2219, 'E', 'CTY', 1, 10, 'Cheshire County Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2219, 'O', 'Cheshire County');
INSERT INTO areas_code (area_id, type, code) VALUES (2219, 'ons', '13');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2252, 'E', 'DIS', 1, 10, 'South Bedfordshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2252, 'O', 'South Bedfordshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2252, 'ons', '09UE');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2254, 'E', 'DIS', 1, 10, 'Mid Bedfordshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2254, 'O', 'Mid Bedfordshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2254, 'ons', '09UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2264, 'E', 'DIS', 1, 10, 'Macclesfield Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2264, 'O', 'Macclesfield District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2264, 'ons', '13UG');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2265, 'E', 'DIS', 1, 10, 'Crewe and Nantwich Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2265, 'O', 'Crewe and Nantwich District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2265, 'ons', '13UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2266, 'E', 'DIS', 1, 10, 'Chester City Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2266, 'O', 'Chester District');
INSERT INTO areas_code (area_id, type, code) VALUES (2266, 'ons', '13UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2267, 'E', 'DIS', 1, 10, 'Ellesmere Port and Neston Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2267, 'O', 'Ellesmere Port and Neston District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2267, 'ons', '13UE');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2268, 'E', 'DIS', 1, 10, 'Congleton Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2268, 'O', 'Congleton District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2268, 'ons', '13UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2269, 'E', 'DIS', 1, 10, 'Vale Royal Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2269, 'O', 'Vale Royal District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2269, 'ons', '13UH');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2270, 'E', 'DIS', 1, 10, 'Restormel Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2270, 'O', 'Restormel District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2270, 'ons', '15UG');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2297, 'E', 'DIS', 1, 10, 'Easington District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2297, 'O', 'Easington District');
INSERT INTO areas_code (area_id, type, code) VALUES (2297, 'ons', '20UF');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2298, 'E', 'DIS', 1, 10, 'Teesdale District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2298, 'O', 'Teesdale District');
INSERT INTO areas_code (area_id, type, code) VALUES (2298, 'ons', '20UH');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2299, 'E', 'DIS', 1, 10, 'Sedgefield Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2299, 'O', 'Sedgefield District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2299, 'ons', '20UG');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2300, 'E', 'DIS', 1, 10, 'Derwentside District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2300, 'O', 'Derwentside District');
INSERT INTO areas_code (area_id, type, code) VALUES (2300, 'ons', '20UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2301, 'E', 'DIS', 1, 10, 'Wear Valley District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2301, 'O', 'Wear Valley District');
INSERT INTO areas_code (area_id, type, code) VALUES (2301, 'ons', '20UJ');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2302, 'E', 'DIS', 1, 10, 'Durham City Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2302, 'O', 'Durham District');
INSERT INTO areas_code (area_id, type, code) VALUES (2302, 'ons', '20UE');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2303, 'E', 'DIS', 1, 10, 'Chester le Street District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2303, 'O', 'Chester-le-Street District');
INSERT INTO areas_code (area_id, type, code) VALUES (2303, 'ons', '20UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2399, 'E', 'DIS', 1, 10, 'Castle Morpeth Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2399, 'O', 'Castle Morpeth District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2399, 'ons', '35UE');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2400, 'E', 'DIS', 1, 10, 'Tynedale District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2400, 'O', 'Tynedale District');
INSERT INTO areas_code (area_id, type, code) VALUES (2400, 'ons', '35UF');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2401, 'E', 'DIS', 1, 10, 'Blyth Valley Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2401, 'O', 'Blyth Valley District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2401, 'ons', '35UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2402, 'E', 'DIS', 1, 10, 'Wansbeck District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2402, 'O', 'Wansbeck District');
INSERT INTO areas_code (area_id, type, code) VALUES (2402, 'ons', '35UG');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2422, 'E', 'DIS', 1, 10, 'North Shropshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2422, 'O', 'North Shropshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2422, 'ons', '39UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2423, 'E', 'DIS', 1, 10, 'Bridgnorth District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2423, 'O', 'Bridgnorth District');
INSERT INTO areas_code (area_id, type, code) VALUES (2423, 'ons', '39UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2424, 'E', 'DIS', 1, 10, 'Oswestry Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2424, 'O', 'Oswestry District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2424, 'ons', '39UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2425, 'E', 'DIS', 1, 10, 'South Shropshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2425, 'O', 'South Shropshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2425, 'ons', '39UF');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2426, 'E', 'DIS', 1, 10, 'Shrewsbury and Atcham Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2426, 'O', 'Shrewsbury and Atcham District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2426, 'ons', '39UE');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2470, 'E', 'DIS', 1, 10, 'North Wiltshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2470, 'O', 'North Wiltshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2470, 'ons', '46UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2471, 'E', 'DIS', 1, 10, 'Salisbury District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2471, 'O', 'Salisbury District');
INSERT INTO areas_code (area_id, type, code) VALUES (2471, 'ons', '46UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2472, 'E', 'DIS', 1, 10, 'West Wiltshire District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2472, 'O', 'West Wiltshire District');
INSERT INTO areas_code (area_id, type, code) VALUES (2472, 'ons', '46UF');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2473, 'E', 'DIS', 1, 10, 'Kennet District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2473, 'O', 'Kennet District');
INSERT INTO areas_code (area_id, type, code) VALUES (2473, 'ons', '46UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2627, 'E', 'DIS', 1, 10, 'Berwick upon Tweed Borough Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2627, 'O', 'Berwick-upon-Tweed District (B)');
INSERT INTO areas_code (area_id, type, code) VALUES (2627, 'ons', '35UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2628, 'E', 'DIS', 1, 10, 'Alnwick District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2628, 'O', 'Alnwick District');
INSERT INTO areas_code (area_id, type, code) VALUES (2628, 'ons', '35UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2631, 'E', 'DIS', 1, 10, 'Carrick District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2631, 'O', 'Carrick District');
INSERT INTO areas_code (area_id, type, code) VALUES (2631, 'ons', '15UC');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2632, 'E', 'DIS', 1, 10, 'Caradon District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2632, 'O', 'Caradon District');
INSERT INTO areas_code (area_id, type, code) VALUES (2632, 'ons', '15UB');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2633, 'E', 'DIS', 1, 10, 'Penwith District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2633, 'O', 'Penwith District');
INSERT INTO areas_code (area_id, type, code) VALUES (2633, 'ons', '15UF');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2634, 'E', 'DIS', 1, 10, 'Kerrier District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2634, 'O', 'Kerrier District');
INSERT INTO areas_code (area_id, type, code) VALUES (2634, 'ons', '15UD');
INSERT INTO areas_area (id, country, type, generation_low_id, generation_high_id, name) VALUES (2635, 'E', 'DIS', 1, 10, 'North Cornwall District Council');
INSERT INTO areas_name (area_id, type, name) VALUES (2635, 'O', 'North Cornwall District');
INSERT INTO areas_code (area_id, type, code) VALUES (2635, 'ons', '15UE');

-- Fix up the generation numbers. Doesn't really have to be accurate, but for completeness.
update areas_area set generation_low_id=3 where generation_low_id=12 and type='CED' and parent_area_id!=2244;
update areas_area set generation_low_id=2 where type='WMC' and country='S' and generation_low_id=12;
update areas_area set generation_low_id=1 where type='WMC' and country in ('E','W') and generation_low_id=12;
update areas_area set generation_low_id =1 where type in ('DIS','EUR','COI','COP','CTY','GLA','LAC','LBO','LBW','LGD','LGE','LGW','MTD','MTW','NIE','SPC','SPE');
update areas_area set generation_low_id =7 where type in ('WAC','WAE');
update areas_area set generation_low_id=11 where type='UTA' and id in (21068,21069,21070);
update areas_area set generation_low_id=1 where type='UTA' and id not in (21068,21069,21070);
update areas_area set generation_low_id =7 where parent_area_id in (2341,2345,2381,2383,2385,2392,2393,2396,2398,2414,2428,2429) and type='DIW' and generation_low_id=12;
update areas_area set generation_low_id =10 where parent_area_id in (2273,2276,2327,2344) and type='DIW' and generation_low_id=12;
update areas_area set generation_low_id =1 where type='DIW' and generation_low_id=12;
update areas_area set generation_low_id =1 where parent_area_id not in (2238,2245,2250,2636) and type='UTE' and generation_low_id=12;
update areas_area set generation_low_id =3 where parent_area_id in (2223, 2248, 21068, 21069, 21070) and type='UTW' and generation_low_id=12;
update areas_area set generation_low_id =3 where parent_area_id in (2223, 2248, 21068, 21069, 21070) and type='UTE' and generation_low_id=1;
update areas_area set generation_low_id =3 where parent_area_id in (2611) and type='UTW' and generation_low_id=12;
update areas_area set generation_low_id =7 where parent_area_id in (2608) and type='UTW' and generation_low_id=12;
update areas_area set generation_low_id =9 where country='S' and type='UTW' and generation_low_id=12;
update areas_area set generation_low_id =1 where type='UTW' and generation_low_id=12;
update areas_area set generation_low_id=11 where id in (2238,2245,2248,2250,2223,2253); -- Actually these UTA started in 2009

