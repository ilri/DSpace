DROP VIEW IF EXISTS eperson_metadata;

CREATE VIEW eperson_metadata AS SELECT
 eperson_id, email, netid,
 mdv_language.text_value AS language, mdv_firstname.text_value AS firstname, mdv_lastname.text_value AS lastname

 FROM eperson,
 metadatavalue mdv_language,  metadatafieldregistry mdf_language,  metadataschemaregistry mds_language,
 metadatavalue mdv_firstname, metadatafieldregistry mdf_firstname, metadataschemaregistry mds_firstname,
 metadatavalue mdv_lastname,  metadatafieldregistry mdf_lastname,  metadataschemaregistry mds_lastname

  WHERE mdv_language .resource_id = eperson.eperson_id
  AND   mdv_firstname.resource_id = eperson.eperson_id
  AND   mdv_lastname .resource_id = eperson.eperson_id

  AND   mdf_language .metadata_field_id = mdv_language .metadata_field_id
  AND   mdf_firstname.metadata_field_id = mdv_firstname.metadata_field_id
  AND   mdf_lastname .metadata_field_id = mdv_lastname .metadata_field_id

  AND   mds_language .metadata_schema_id = mds_language .metadata_schema_id
  AND   mds_firstname.metadata_schema_id = mds_firstname.metadata_schema_id
  AND   mds_lastname .metadata_schema_id = mds_lastname .metadata_schema_id

  AND   mds_language .short_id = 'eperson'
  AND   mds_firstname.short_id = 'eperson'
  AND   mds_lastname .short_id = 'eperson'

  AND   mdf_language .element = 'language'
  AND   mdf_firstname.element = 'firstname'
  AND   mdf_lastname .element = 'lastname'

  AND   mdf_language .qualifier is null
  AND   mdf_firstname.qualifier is null
  AND   mdf_lastname .qualifier is null;