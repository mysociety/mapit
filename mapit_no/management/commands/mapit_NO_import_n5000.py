# import_norway_n5000.py:
# This script was used to import information from the N5000 dataset available at
# http://www.statkart.no/?module=Articles;action=Article.publicShow;ID=15305
#
# This script can now be done using the generic import script, as follows:
# python manage.py loaddata norway # Optional, will load in types
# python manage.py mapit_import --generation_id <new-gen-id> \
#   --area_type_code NKO --name_type_code M --country_code O \
#   --name_field NAVN --encoding iso-8859-1 \
#   --code_field KOMM --code_type n5000 --use_code_as_id --commit \
#   N5000_AdministrativFlate.shp
