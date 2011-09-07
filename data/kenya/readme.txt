These are the steps needed to import the Kenyan data to MaPit.

=== Getting the data ===

Go to http://www.gadm.org/country and select 'Kenya' and 'kmz'.

Download the Country and the five subdivision level files:

    http://www.gadm.org/data/kmz/KEN_adm0.kmz
    http://www.gadm.org/data/kmz/KEN_adm1.kmz
    http://www.gadm.org/data/kmz/KEN_adm2.kmz
    http://www.gadm.org/data/kmz/KEN_adm3.kmz
    http://www.gadm.org/data/kmz/KEN_adm4.kmz
    http://www.gadm.org/data/kmz/KEN_adm5.kmz

On a bash shell you can use this to fetch them all:

    wget http://www.gadm.org/data/kmz/KEN_adm{0,1,2,3,4,5}.kmz

These levels correspond to these hierarchies:

    0: country border
    1: provinces
    2: districts
    3: divisions
    4: locations
    5: sublocations

Note that the new constituencies do not appear to be represented in these
datasets.

There are also some XML errors that prevent the datasets being opened in Google
Earth. Try to open them, note the line number that the error is on and then use
the following to fix them:

    for I in 0 1 2 3 4 5; do
        cat KEN_adm$I.kmz | gunzip - > KEN_adm$I.kml;
        rm KEN_adm$I.kmz;
    done
        
    # edit files as needed to correct issues - most likely a bare '&'.
    
