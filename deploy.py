import os,sys,arcpy;
import xml.dom.minidom as DOM;

###############################################################################
#                                                                             #
# ArcGIS Server Service Deployer Script                                       #
# Version: 20141114                                                           #
#                                                                             #
#  The script takes one optional parameter being the name of the              #
#  ArcCatalog administration connection for the AGS Server                    #
#                                                                             #
#  You may provide a default connection name below.  Note all security        #
#  is handled by the AGS connection.  Obviously there is room here for        #
#  errors if you are continually swapping around this name (e.g. deploying    #
#  to the wrong server).  I would advise against hard coding this to your     #
#  production server connection.                                              #
#                                                                             #
#  In order to change data source paths its necessary to alter the MXD        #
#  before deployment.  Thus this script creates a temporary copy of the MXD   #
#  in order to change the paths.  The original MXD is never modified.         #
#                                                                             #
###############################################################################
if len(sys.argv) > 1:
   catalog = sys.argv[1];
else:
   # Default connection to be used when no parameter is provided
   catalog = "my_ags_server";
   
###############################################################################
#                                                                             #
#  Configuration Section for WATERS_KMZ_NP21 Service                          #
#                                                                             #
###############################################################################

# The location of your MXD file to be deployed to AGS
mxd = "my_map_document.mxd";

# The name of the AGS Service to deploy the MXD as
# Note existing services will be overwritten
service    = "MYSERVICE";

# The AGS folder into which to deploy the service.
# Leave None to deploy to the root.
ags_folder = "MYFOLDER";

# Hash of general properties to be applied
ags_properties = {
    'schemaLockingEnabled': False
   ,'MinInstances': 3
   ,'MaxInstances': 5
}

# Hash of services to enable or disable
ags_services = {
    'WMSServer': True
   ,'WFSServer': False
   ,'KmlServer': True
}

# Array of Hash of properties to be applied to individual services
ags_service_props = {
    'KmlServer': {'WebCapabilities': 'Vectors'}
}

# Values to use in overriding the text provided by the MXD.
ags_summary = None;
ags_tags    = None;

###############################################################################
#                                                                             #
# AGS Data Stores Configuration Section (optional)                            #
#                                                                             #
#   ds_expected is the name of the expected DS and will throw warning if not  #
#      found                                                                  #
#                                                                             #
#   ds_equivalents is a hash of equivalent values for a given ds name.  Thus  #
#      for a ds named X, we inspect X on the server for a given mapping Y.    #
#      If any of the equivalent values are found in the MXD paths, they are   #
#      swapped out for value Y.                                               #
#                                                                             #
###############################################################################
ds_expected = "WatersData";

ds_equivalents = {
    "WatersData": [
        r"\\industux\WatersGeoAGS\WatersData"
       ,r"D:\Public\Data\WatersGeoAGS\WatersData"
    ]
}

###############################################################################
#                                                                             #
# The remaining sections of the script should not require modifications.      #
#                                                                             #
###############################################################################
def srv_property(doc,property,value):
   keys = doc.getElementsByTagName('Key')
   for key in keys:
      if key.hasChildNodes():
         if key.firstChild.data == property:
            if value is True:
               key.nextSibling.firstChild.data = 'true';
            elif value is False:
               key.nextSibling.firstChild.data = 'false';
            else:
               key.nextSibling.firstChild.data = value
   return doc;
  
def soe_enable(doc,soe,value):
   typeNames = doc.getElementsByTagName('TypeName');
   
   for typeName in typeNames:
      if typeName.firstChild.data == soe:
         extension = typeName.parentNode
         for extElement in extension.childNodes:
            if extElement.tagName == 'Enabled':
               if value is True:
                  extElement.firstChild.data = 'true';
               else:
                  extElement.firstChild.data = 'false';

   return doc;

def soe_property(doc,soe,soeProperty,soePropertyValue):
   typeNames = doc.getElementsByTagName('TypeName');
   
   for typeName in typeNames:
      if typeName.firstChild.data == soe:
         extension = typeName.parentNode
         for extElement in extension.childNodes:
            if extElement.tagName == 'Props':
               for propArray in extElement.childNodes:
                  for propSet in propArray.childNodes:
                     for prop in propSet.childNodes:
                        if prop.tagName == "Key":
                           if prop.firstChild.data == soeProperty:
                              if prop.nextSibling.hasChildNodes():
                                 prop.nextSibling.firstChild.data = soePropertyValue
                              else:
                                 txt = doc.createTextNode(soePropertyValue)
                                 prop.nextSibling.appendChild(txt)
   return doc;

###############################################################################
#                                                                             #
# Define the workspace                                                        #
#                                                                             #
###############################################################################
wrkspc = os.getcwd() + os.sep;
print
print "  Workspace = " + wrkspc;
os.chdir(wrkspc);

###############################################################################
#                                                                             #
# Verify the MXD                                                              #
#                                                                             #
###############################################################################
print
if not os.path.exists(wrkspc + mxd):
   print "MXD file not found: " + wrkspc + mxd
   exit(-1);
   
mapDoc = arcpy.mapping.MapDocument(wrkspc + mxd)
print "  Orig MXD = " + wrkspc + mxd;

###############################################################################
#                                                                             #
# Validate the AGS Server connection                                          #
#   Certain ArcGIS installations (e.g. government work stations) seem unable  #
#   to find the connection pool when calling "GIS Servers" alone.  In this    #
#   case we root about looking for it as best we can.                         #
#                                                                             #
###############################################################################
con = "GIS Servers\\" + catalog + ".ags";
if not arcpy.Exists(con):
   print
   print "  Connection named GIS Servers\\" + catalog + ".ags not found."
   con2 = os.environ['USERPROFILE'] + "\\AppData\\Roaming\\ESRI\\Desktop10.2\\ArcCatalog\\" + catalog + ".ags"
   
   if arcpy.Exists(con2):
      con = con2;
      
   else:
      print
      print "  No luck checking " + con2
      con3 = os.environ['USERPROFILE'] + "\\AppData\\Roaming\\ESRI\\Desktop10.1\\ArcCatalog\\" + catalog + ".ags"
      
      if arcpy.Exists(con3):
         con = con3;
      
      else:  
         print
         print "  No luck checking " + con3
         print "  Unable to find a valid connection for " + catalog
         exit(-1);

###############################################################################
#                                                                             #
# Create a temporary copy of the MXD                                          #
#                                                                             #
###############################################################################
tempMap = wrkspc + mxd;
tempMap = tempMap.replace(".mxd","_temp.mxd");
print "  Temp MXD = " + tempMap;
os.remove(tempMap) if os.path.exists(tempMap) else None;
mapDoc.saveACopy(tempMap);
mapDoc = arcpy.mapping.MapDocument(tempMap)
print
print "  Connection = " + con;
    
###############################################################################
#                                                                             #
# Do data store path swap on temporary MXD                                    #
#                                                                             #
###############################################################################
database_stores = arcpy.ListDataStoreItems(con,'DATABASE')
folder_stores = arcpy.ListDataStoreItems(con,'FOLDER')

boo = False;
for item in folder_stores:
   key = None;
   
   if item[0] == ds_expected:
      boo = True;
      
   if item[0] in ds_equivalents:
      print
      print "  Found AGS Data Store " + item[0] + " mapped to "
      print "    " + item[2];
      
      for equiv in ds_equivalents[item[0]]:
         if item[2] == equiv:
            key = equiv
            
      if key is not None:
         for equiv in ds_equivalents[item[0]]:
            if equiv != key:
               print
               print "    Swapping " 
               print "      " + equiv
               print "      for "
               print "      " + key
               print "      if exists..."
               
               mapDoc.findAndReplaceWorkspacePaths(
                   equiv
                  ,key
                  ,False
               );
               mapDoc.save()
         
if boo is False:
   print "  Warning: Expected data store " + ds_expected + " not found on this AGS Server ";

###############################################################################
#                                                                             #
# Remove any old sddrafts or sd files lying around                            #
#                                                                             #
#  Note that after deployment ArcPy automatically removes the sddraft but     #
#  retains the sd file                                                        # 
#                                                                             #
###############################################################################
sddraft = wrkspc + service + '.sddraft'
sd = wrkspc + service + '.sd'
print
print "  SD draft = " + sddraft;

print

if os.path.exists(sddraft):
   os.remove(sddraft);
   
if os.path.exists(sd):
   os.remove(sd);
   
###############################################################################
#                                                                             #
# Create service definition draft                                             #
#                                                                             #
###############################################################################
results = arcpy.mapping.CreateMapSDDraft(
    map_document = mapDoc
   ,out_sddraft = sddraft
   ,service_name = service
   ,server_type = 'ARCGIS_SERVER'
   ,connection_file_path = con
   ,copy_data_to_server = False
   ,folder_name = ags_folder
   ,summary = ags_summary
   ,tags = ags_tags
);

if results['errors'] != {}:
   print results['errors']
   sys.exit();
   
###############################################################################
#                                                                             #
# Alter Service Definitions                                                   #
#                                                                             #
###############################################################################
doc = DOM.parse(sddraft)
for k, v in ags_properties.iteritems():
   doc = srv_property(doc,k,v);
for k, v in ags_services.iteritems():
   doc = soe_enable(doc,k,v);
for k, v in ags_service_props.iteritems():
   doc = soe_property(doc,k,v.keys()[0],v.values()[0]);
f = open(sddraft, 'w')
doc.writexml( f )
f.close()

###############################################################################
#                                                                             #
# Validate the draft                                                          #
#                                                                             #
###############################################################################   
analysis = arcpy.mapping.AnalyzeForSD(sddraft)

if analysis['errors'] != {}:
   print '---- ERRORS ----'
   vars = analysis['errors']
   for ((message, code), layerlist) in vars.iteritems():
      print '    ', message, ' (CODE %i)' % code
      if len(layerlist) > 0:
         print '       applies to:',
         for layer in layerlist:
            print layer.name,
         print

if analysis['warnings'] != {}:
   print '---- WARNINGS ----'
   vars = analysis['warnings']
   for ((message, code), layerlist) in vars.iteritems():
      print '    ', message, ' (CODE %i)' % code
      if len(layerlist) > 0:
         print '       applies to:',
         for layer in layerlist:
            print layer.name,
         print
         
if analysis['messages'] != {}:
   print '---- MESSAGES ----'
   vars = analysis['messages']
   for ((message, code), layerlist) in vars.iteritems():
      print '    ', message, ' (CODE %i)' % code
      if len(layerlist) > 0:
         print '       applies to:',
         for layer in layerlist:
            print layer.name,
         print

###############################################################################
#                                                                             #
# Publish the draft to server                                                 #
#                                                                             #
###############################################################################
print '------------------'
if analysis['errors'] == {}:
   arcpy.StageService_server(sddraft, sd)

   arcpy.UploadServiceDefinition_server(sd, con)
   print "Service successfully published"
    
else: 
   print "Service could not be published because errors were found during analysis."

print arcpy.GetMessages()

###############################################################################
#                                                                             #
# Do Cleanup                                                                  #
#                                                                             #
###############################################################################
del mapDoc, sd, con, results, doc;
arcpy.Delete_management(tempMap);
