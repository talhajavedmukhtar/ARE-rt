This folder contains the banner datasets provided as input for generating the rules. 

Two dataset files are provided:
    
    - Censys banners
    - Ferret banners

--------------
Banner Files
--------------

The banner files contains banners uniquely identified by their banner-IDs. The files are in json, formatted in the following way:

    "<banner-ID>": {
                "type"      : Banner type (e.g, HTTP, FTP, etc.)
                "banner"    : Banner text
                "ips"       : List of IP addresses of the devices
                "<Labels>"  : List of labels (e.g, Censys labels, Ferret Labels) corresponding to each device
                    {
                        "ip"    : IP address of the device,
                        "label" : {
                            "deviceTypes"   : List of device types associated with the device
                            "vendor"        : Vendor information of the device
                            "product"       : Product/model name of the device
                        }


--------------
Anonymization
--------------

In the Ferret dataset, we replaced all the "UUID" and "FRIENDLY-NAME" in the banner texts with their anonymized versions.
