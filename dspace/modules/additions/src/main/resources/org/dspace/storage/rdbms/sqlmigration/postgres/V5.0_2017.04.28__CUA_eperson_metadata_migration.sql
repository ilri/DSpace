CREATE OR REPLACE VIEW eperson_metadata AS

  SELECT eperson.eperson_id, email, netid,
    mdv_language.text_value AS language, mdv_firstname.text_value AS firstname, mdv_lastname.text_value AS lastname

  FROM EPerson eperson

    LEFT OUTER JOIN (
                      SELECT text_value, resource_id
                      FROM metadatavalue, metadatafieldregistry, metadataschemaregistry
                      WHERE metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id
                            AND metadatafieldregistry.metadata_schema_id = metadataschemaregistry.metadata_schema_id

                            AND metadataschemaregistry.short_id = 'eperson'
                            AND metadatafieldregistry.element = 'language'
                            AND metadatafieldregistry.qualifier is null
                    ) AS mdv_language
      ON mdv_language.resource_id = eperson.eperson_id

    LEFT OUTER JOIN (
                      SELECT text_value, resource_id
                      FROM metadatavalue, metadatafieldregistry, metadataschemaregistry
                      WHERE metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id
                            AND metadatafieldregistry.metadata_schema_id = metadataschemaregistry.metadata_schema_id

                            AND metadataschemaregistry.short_id = 'eperson'
                            AND metadatafieldregistry.element = 'firstname'
                            AND metadatafieldregistry.qualifier is null
                    ) AS mdv_firstname
      ON mdv_firstname.resource_id = eperson.eperson_id

    LEFT OUTER JOIN (
                      SELECT text_value, resource_id
                      FROM metadatavalue, metadatafieldregistry, metadataschemaregistry
                      WHERE metadatavalue.metadata_field_id = metadatafieldregistry.metadata_field_id
                            AND metadatafieldregistry.metadata_schema_id = metadataschemaregistry.metadata_schema_id

                            AND metadataschemaregistry.short_id = 'eperson'
                            AND metadatafieldregistry.element = 'lastname'
                            AND metadatafieldregistry.qualifier is null
                    ) AS mdv_lastname
      ON mdv_lastname.resource_id = eperson.eperson_id
;