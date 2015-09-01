#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Examples of using beanbag to access PDC REST API.
It's better to set PYTHONPATH to PDC root directory.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pdc_client import make_client, set_option


if __name__ == "__main__":
    # shortcut is OK
    # set_option("url", "qa")
    url = "https://pdc.example.com/rest_api/v1/"
    set_option("url", url)
    set_option("insecure", True)
    pdc, session = make_client()

    # list 20 components at page 1.
    # ._ means the url tailing slash - /rest_api/v1/global-components/
    page_one = pdc['global-components']._()
    # total number of global components.
    print page_one['count']
    # global components list
    print page_one['results']
    # elements in the list are dict object
    first_component = page_one['results'][0]
    print first_component['name']
    print first_component['dist_git_path']

    # access nested resource of global component.
    # /rest_api/v1/global-components/1/contacts/
    contacts = pdc['global-components'][3].contacts._()
    print contacts
    # return a list object
    print contacts[0]

    # create a new global component
    new_global_data = {"name": "New_from_beanbag", "dist_git_path": "beanbag"}
    # pass one dict argument as post data, send POST request, and return the
    # new global component(dict)
    new_global = pdc['global-components']._(new_global_data)
    print new_global

    # update(PUT)
    pdc['global-components'][3]._ = {"name": "Update_from_beanbag"}
    # retrieve the update result
    updated_component = pdc['global-components'][3]._()
    print updated_component['name']

    # partial update(PATCH)
    pdc['global-components'][3]._ += {"dist_git_path": "beanbag"}
    updated_component = pdc['global-components'][3]._()
    print updated_component['dist_git_path']

    # delete the global component with pk = 1
    del pdc['global-components'][3]
