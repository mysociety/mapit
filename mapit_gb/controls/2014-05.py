# A control file for importing May 2014 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    # There are lots of new things in this edition of boundary line, but none
    # of them are things which we have to manually override, which is nice.

    # New areas, by type:

    # Wards, which we don't care about:
    # New area: DIW E05009360 17464 Odiham Ward
    # New area: DIW E05009358 17465 Hartley Wintney Ward
    # New area: DIW E05009359 17483 Hook Ward
    # New area: DIW E05009354 41822 Crookham West and Ewshot Ward
    # New area: DIW E05009353 17452 Crookham East Ward
    # New area: DIW E05009352 17443 Blackwater and Hawley Ward
    # New area: DIW E05009361 17471 Yateley East Ward
    # New area: DIW E05009355 41823 Fleet Central Ward
    # New area: DIW E05009357 17453 Fleet West Ward
    # New area: DIW E05009356 41821 Fleet East Ward
    # New area: DIW E05009362 17474 Yateley West Ward
    # New area: DIW E05009428 3842 Chorleywood South & Maple Cross Ward
    # New area: DIW E05009427 3848 Chorleywood North & Sarratt Ward
    # New area: DIW E05009431 3854 Gade Valley Ward
    # New area: DIW E05009436 3838 Rickmansworth Town Ward
    # New area: DIW E05009433 3922 Moor Park & Eastbury Ward
    # New area: DIW E05009429 3820 Dickinsons Ward
    # New area: DIW E05009432 3825 Leavesden Ward
    # New area: DIW E05009425 3853 Abbots Langley & Bedmond Ward
    # New area: DIW E05009435 3839 Penn & Mill End Ward
    # New area: DIW E05009430 3837 Durrants Ward
    # New area: DIW E05009437 3809 South Oxhey Ward
    # New area: DIW E05009426 3816 Carpenders Park Ward
    # New area: DIW E05009434 3805 Oxhey Hall & Hayling Ward
    # New area: DIW E05009364 8658 Brize Norton and Shilton Ward
    # New area: DIW E05009366 8639 Hailey, Minster Lovell and Leafield Ward
    # New area: DIW E05009363 8614 Burford Ward
    # New area: DIW E05009365 41864 Carterton North West Ward

    # London Borough Wards, which we also don't care about:
    # New area: LBW E05009391 10985 Chelsea Riverside Ward
    # New area: LBW E05009397 11273 Holland Ward
    # New area: LBW E05009398 11348 Norland Ward
    # New area: LBW E05009402 10989 Redcliffe Ward
    # New area: LBW E05009405 10984 Stanley Ward
    # New area: LBW E05009403 11149 Royal Hospital Ward
    # New area: LBW E05009399 44519 Notting Dale Ward
    # New area: LBW E05009404 11446 St. Helen's Ward
    # New area: LBW E05009392 11351 Colville Ward
    # New area: LBW E05009394 11445 Dalgarno Ward
    # New area: LBW E05009396 11347 Golborne Ward
    # New area: LBW E05009395 11274 Earl's Court Ward
    # New area: LBW E05009393 11266 Courtfield Ward
    # New area: LBW E05009388 11272 Abingdon Ward
    # New area: LBW E05009401 11269 Queen's Gate Ward
    # New area: LBW E05009389 11267 Brompton & Hans Town Ward
    # New area: LBW E05009390 11349 Campden Ward
    # New area: LBW E05009400 11350 Pembridge Ward
    # New area: LBW E05009330 10977 St. Katharine's & Wapping Ward
    # New area: LBW E05009332 10976 Shadwell Ward
    # New area: LBW E05009324 44506 Island Gardens Ward
    # New area: LBW E05009323 11048 Canary Wharf Ward
    # New area: LBW E05009318 11174 Blackwall & Cubitt Town Ward
    # New area: LBW E05009328 44507 Poplar Ward
    # New area: LBW E05009333 11193 Spitalfields & Banglatown Ward
    # New area: LBW E05009331 41879 St. Peter's Ward
    # New area: LBW E05009317 11189 Bethnal Green Ward
    # New area: LBW E05009329 11187 St. Dunstan's Ward
    # New area: LBW E05009327 11184 Mile End Ward
    # New area: LBW E05009325 11175 Lansbury Ward
    # New area: LBW E05009322 10974 Bromley South Ward
    # New area: LBW E05009320 11183 Bow West Ward
    # New area: LBW E05009319 11181 Bow East Ward
    # New area: LBW E05009321 44509 Bromley North Ward
    # New area: LBW E05009336 11192 Whitechapel Ward
    # New area: LBW E05009334 44508 Stepney Green Ward
    # New area: LBW E05009326 10975 Limehouse Ward
    # New area: LBW E05009335 10855 Weavers Ward
    # New area: LBW E05009377 44511 Hoxton East & Shoreditch Ward
    # New area: LBW E05009375 11110 Haggerston Ward
    # New area: LBW E05009371 11111 De Beauvoir Ward
    # New area: LBW E05009381 10854 London Fields Ward
    # New area: LBW E05009374 11180 Hackney Wick Ward
    # New area: LBW E05009369 11222 Clissold Ward
    # New area: LBW E05009373 11200 Hackney Downs Ward
    # New area: LBW E05009380 11201 Lea Bridge Ward
    # New area: LBW E05009368 11220 Cazenove Ward
    # New area: LBW E05009383 11202 Springfield Ward
    # New area: LBW E05009379 11210 King's Park Ward
    # New area: LBW E05009367 11283 Brownswood Ward
    # New area: LBW E05009378 11112 Hoxton West Ward
    # New area: LBW E05009370 11208 Dalston Ward
    # New area: LBW E05009386 11190 Victoria Ward
    # New area: LBW E05009372 41886 Hackney Central Ward
    # New area: LBW E05009376 11198 Homerton Ward
    # New area: LBW E05009382 44512 Shacklewell Ward
    # New area: LBW E05009385 11207 Stoke Newington Ward
    # New area: LBW E05009387 11206 Woodberry Down Ward
    # New area: LBW E05009384 11288 Stamford Hill West Ward

    # Unitary Authority wards, we also don't care about these:
    # New area: UTW E05009421 12059 Stony Stratford Ward
    # New area: UTW E05009423 12006 Wolverton Ward
    # New area: UTW E05009407 11918 Bletchley Park Ward
    # New area: UTW E05009406 11943 Bletchley East Ward
    # New area: UTW E05009411 38416 Campbell Park & Old Woughton Ward
    # New area: UTW E05009413 11922 Danesborough & Walton Ward
    # New area: UTW E05009418 12002 Olney Ward
    # New area: UTW E05009416 38419 Newport Pagnell North & Hanslope Ward
    # New area: UTW E05009422 38415 Tattenhoe Ward
    # New area: UTW E05009419 38414 Shenley Brook End Ward
    # New area: UTW E05009414 11953 Loughton & Shenley Ward
    # New area: UTW E05009412 44518 Central Milton Keynes Ward
    # New area: UTW E05009409 12009 Bradwell Ward
    # New area: UTW E05009420 12005 Stantonbury Ward
    # New area: UTW E05009408 11984 Bletchley West Ward
    # New area: UTW E05009424 11990 Woughton & Fishermead Ward
    # New area: UTW E05009415 41911 Monkston Ward
    # New area: UTW E05009410 41910 Broughton Ward
    # New area: UTW E05009417 38418 Newport Pagnell South Ward
    # New area: UTW E05009343 25444 Colnbrook with Poyle Ward
    # New area: UTW E05009342 42337 Cippenham Meadows Ward
    # New area: UTW E05009340 371 Chalvey Ward
    # New area: UTW E05009341 373 Cippenham Green Ward
    # New area: UTW E05009345 364 Farnham Ward
    # New area: UTW E05009337 42338 Baylis and Stoke Ward
    # New area: UTW E05009350 237 Upton Ward
    # New area: UTW E05009339 231 Central Ward
    # New area: UTW E05009349 233 Langley St. Mary's Ward
    # New area: UTW E05009351 367 Wexham Lea Ward
    # New area: UTW E05009346 42339 Foxborough Ward
    # New area: UTW E05009344 44510 Elliman Ward
    # New area: UTW E05009347 362 Haymill and Lynch Hill Ward
    # New area: UTW E05009338 429 Britwell and Northborough Ward
    # New area: UTW E05009348 235 Langley Kedermister Ward

    # Parish Councils, we don't care about these either:
    # New area: CPC E04012323 14263 Corfe Castle CP
    # New area: CPC E04012322 14413 Bere Regis CP
    # New area: CPC E04012326 14359 Wareham St. Martin CP
    # New area: CPC E04012328 14368 Worth Matravers CP
    # New area: CPC E04012325 14365 Steeple with Tyneham CP
    # New area: CPC E04012320 14380 Affpuddle and Turnerspuddle CP
    # New area: CPC E04012327 14354 Wareham Town CP
    # New area: CPC E04012321 14357 Arne CP
    # New area: CPC E04012324 14350 Morden CP
    # New area: CPC E04012293 3821 Croxley Green CP
    # New area: CPC E04012329 23520 Bitteswell with Bittesby CP
    # New area: CPC E04012331 23517 Dunton Bassett CP
    # New area: CPC E04012330 23483 Broughton Astley CP
    # New area: CPC E04012332 23335 Kibworth Beauchamp CP
    # New area: CPC E04012333 23411 Kibworth Harcourt CP
    # New area: CPC E04012295 6798 Spixworth CP
    # New area: CPC E04012294 6793 Crostwick CP
    # New area: CPC E04012306 21868 Long Preston CP
    # New area: CPC E04012303 21870 Hellifield CP
    # New area: CPC E04012305 21883 Lawkland CP
    # New area: CPC E04012297 21884 Austwick CP
    # New area: CPC E04012299 21643 Cowling CP
    # New area: CPC E04012307 21656 Lothersdale CP
    # New area: CPC E04012298 21653 Cononley CP
    # New area: CPC E04012301 21850 Gargrave CP
    # New area: CPC E04012309 21688 Stirton with Thorlby CP
    # New area: CPC E04012308 21881 Settle CP
    # New area: CPC E04012302 21657 Glusburn and Cross Hills CP
    # New area: CPC E04012300 21644 Farnhill CP
    # New area: CPC E04012304 21645 Kildwick CP
    # New area: CPC E04012312 15887 Haverhill CP
    # New area: CPC E04012315 15820 Wickhambrook CP
    # New area: CPC E04012314 15876 Ousden CP
    # New area: CPC E04012310 42110 Bury St. Edmunds CP
    # New area: CPC E04012313 15888 Little Wratting CP
    # New area: CPC E04012311 15832 Fornham All Saints CP
    # New area: CPC E04012318 16523 Chidham and Hambrook CP
    # New area: CPC E04012319 16529 Southbourne CP
    # New area: CPC E04012317 44516 Chadwick End CP
    # New area: CPC E04012316 44514 Balsall CP
    # New area: CPC E04012334 427 Britwell CP
    # New area: CPC W04000982 1811 Cwmbran Central Community
    # New area: CPC W04000985 1851 Pen Tranch Community
    # New area: CPC W04000984 1725 New Inn Community
    # New area: CPC W04000980 1717 Abersychan Community
    # New area: CPC W04000983 1835 Fairwater Community
    # New area: CPC W04000987 1838 Upper Cwmbran Community
    # New area: CPC W04000981 1821 Croesyceiliog Community
    # New area: CPC W04000986 1822 Pontnewydd Community
    # New area: CPC E04012296 44513 Queen's Park CP

    # Unitary Authority Electoral Divisions:

    # This one is weird - the Ordnance survey seem to have resurrected an
    # old GSS code for South Tynedale, which we had previously in generation
    # 20, but which they they changed in generation 21. They changed it back
    # in this update, and that caused issues with the
    # mapit_UK_import_boundary_line management command. We manually fixed that
    # by removing the GSS code from the old area in generation 20, so that
    # the area in this edition looks like a new one to the importer and gets
    # created as such.
    # New area: UTE E05009154 43677 South Tynedale ED

    # New area: UTE W05000995 44515 Llanyrafon East and Ponthir ED
    # New area: UTE W05000997 1726 New Inn ED
    # New area: UTE W05000992 1716 Abersychan ED
    # New area: UTE W05000994 25972 Greenmeadow ED
    # New area: UTE W05001001 1837 Upper Cwmbran ED
    # New area: UTE W05000996 1813 Llanyrafon West ED
    # New area: UTE W05000993 25977 Croesyceiliog North ED
    # New area: UTE W05000999 25990 Snatchwood ED
    # New area: UTE W05001000 25971 St. Dials ED
    # New area: UTE W05000998 1823 Pontnewydd ED

    # This is the default
    return False
