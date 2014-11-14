ArcGIS Deployment Script

This script was created to address several concerns when deploying AGS services.
In one case a service author/maintainer may lack publishing privileges on the ArcGIS 
Server target.  Publishing is executed in this case by a second party who administers
the target server.  The target AGS server also may or may not have data source mappings
that are easily modified by the author/maintainer.  The need to dynamically change data 
paths and/or server settings may limit the reusability of compiled sd service files.
Furthermore, there is the larger 
issue of how to persist and document the myriad of AGS deployment settings performed 
either by the secondary admin or even by yourself.   
Encapsulating settings into a
independent version-controlled script is preferable to manual deployment for a host
of reasons that should be pretty evident.

As with all ArcPy scripts, server access is managed through your ArcCatalog connections.
Thus the script itself does not contain any information about the server or your access
credentials.  The user must have an existing ArcCatalog AGS admin connection to deploy 
services.

Currently the script provides the ability to script specific AGS deployment parameters
through the midstream modification of the sddraft as outlined in the examples at
http://resources.arcgis.com/en/help/main/10.2/index.html#//00s30000006q000000

Furthermore the script allows the dynamic alteration of data source paths.  In this 
scenario your local MXD may utilize file resources located at path A.  Your staging
server under your control may have a data store that remaps path A to path B.  However
your production servers may place the data at any number of locations and your ability
to create data stores is limited.  This script will allow your secondary admin to redefine 
your data paths  on the fly to match your production servers.
 